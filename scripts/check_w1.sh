#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

required_files=(
  .gitignore
  roles.md
  docs/PRD.md
  docs/SPEC.md
  process/task_cards/2410311404-code-coach-w1-cards.md
  process/gate/2410311404-code-coach-gate-1-prd-spec.md
  evidence/2410311404-code-coach-w1-detector-spike.md
  evidence/2410311404-code-coach-w1-ai-spike.md
  spike/src/language_detector.cpp
  spike/tests/run_spike.sh
  spike/tests/run_ai_spike.py
  spike/tests/ai_request.json
  spike/tests/gate1_review_request.json
  spike/tests/sample.cpp
  spike/tests/sample.py
  spike/tests/ambiguous.txt
  scripts/check_w1.sh
)

for file in "${required_files[@]}"; do
  test -s "${file}" || {
    echo "W1_REQUIRED_FILE_CHECK=FAIL file=${file}"
    exit 1
  }
done

if find . -type f -iname 'README*' \
  -not -path './.git/*' \
  -not -path './.venv/*' \
  -not -path './.pytest_cache/*' \
  -print -quit | grep -q .; then
  echo "W1_README_CHECK=FAIL"
  exit 1
fi

python3 - <<'PY'
import re
from pathlib import Path

prd = Path("docs/PRD.md").read_text(encoding="utf-8")
for marker in ("目标用户", "核心场景", "成功指标", "Non-goals"):
    assert marker in prd, marker

spec = Path("docs/SPEC.md").read_text(encoding="utf-8")
for story in range(1, 5):
    marker = f"### US-{story} "
    assert marker in spec, marker
    section = spec.split(marker, 1)[1].split("### US-", 1)[0]
    count = section.count(f"- AC-{story}.")
    assert count >= 2, (story, count)
print("W1_PRD_SPEC_CHECK=PASS stories=4")

cards_text = Path(
    "process/task_cards/2410311404-code-coach-w1-cards.md"
).read_text(encoding="utf-8")
cards = re.findall(r"^## CC-.*?(?=^## CC-|\Z)", cards_text, flags=re.M | re.S)
assert len(cards) == 3, len(cards)
required = [
    "- Role:", "- Status:", "- Depends on:", "- Traceability:",
    "- Context:", "- User Value:", "- Scope:", "- Acceptance:",
    "- Evidence:", "- Test Command:", "- Out of scope:",
    "- Risk:", "- Estimated Effort:",
]
for index, card in enumerate(cards, start=1):
    for marker in required:
        assert marker in card, (index, marker)
    assert "- Status: completed" in card, index
    assert "->" in card, index
print("W1_TASK_CARD_CHECK=PASS cards=3")
PY

python3 -m json.tool spike/tests/ai_request.json >/dev/null
python3 -m json.tool spike/tests/gate1_review_request.json >/dev/null
bash spike/tests/run_spike.sh

rg -F "AI_EXPLANATION_CAPABILITY=PASS" \
  evidence/2410311404-code-coach-w1-ai-spike.md >/dev/null
rg -F "AI_STRUCTURED_CONTRACT=PARTIAL_VALIDATION_REQUIRED" \
  evidence/2410311404-code-coach-w1-ai-spike.md >/dev/null
rg -F '`MODIFIED_PASS`' \
  process/gate/2410311404-code-coach-gate-1-prd-spec.md >/dev/null

residue="$(rg -n \
  '<YYYY-MM-DD>|<项目名称>|<风险>|TODO|TBD|待填写|待补|Lorem ipsum|changeme' \
  -g '!.git/**' -g '!scripts/check_*.sh' . || true)"
if test -n "${residue}"; then
  printf '%s\n' "${residue}"
  echo "W1_TEMPLATE_RESIDUE_CHECK=FAIL"
  exit 1
fi

if rg -n -i '\b\x73\x6f\x6c\x6f\b' -g '!.git/**' .; then
  echo "W1_NAMING_CHECK=FAIL"
  exit 1
fi

if rg -n '[[:blank:]]+$' -g '!.git/**' -g '!spike/tmp/**' .; then
  echo "W1_TRAILING_WHITESPACE_CHECK=FAIL"
  exit 1
fi

if rg -n \
  'sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|BEGIN [A-Z ]*PRIVATE KEY' \
  -g '!.git/**' -g '!scripts/check_*.sh' .; then
  echo "W1_SECRET_SCAN=FAIL"
  exit 1
fi

git diff --check

echo "W1_TEMPLATE_RESIDUE_CHECK=PASS"
echo "W1_NAMING_CHECK=PASS"
echo "W1_SECRET_SCAN=PASS"
echo "W1_GATE_CHECK=PASS"

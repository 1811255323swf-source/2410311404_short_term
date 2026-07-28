#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

bash scripts/check_w1.sh

required_files=(
  docs/DESIGN.md
  docs/adr/ADR-001-deterministic-core-ai-adapter.md
  docs/adr/ADR-002-hybrid-safe-language-detection.md
  process/task_cards/2410311404-code-coach-w2-cards.md
  process/gate/2410311404-code-coach-gate-2-design.md
  evidence/2410311404-code-coach-w2-contract-red-green.md
  evidence/2410311404-code-coach-w2-design-review.md
  spike/src/ai_contract.py
  spike/tests/test_ai_contract.py
  spike/tests/w2_design_review_request.json
  scripts/check_w2.sh
)

for file in "${required_files[@]}"; do
  test -s "${file}" || {
    echo "W2_REQUIRED_FILE_CHECK=FAIL file=${file}"
    exit 1
  }
done

python3 - <<'PY'
import re
from pathlib import Path

spec = Path("docs/SPEC.md").read_text(encoding="utf-8")
acceptance = sorted(set(re.findall(r"AC-[1-4]\.[1-3]", spec)))
expected = {
    "AC-1.1", "AC-1.2",
    "AC-2.1", "AC-2.2", "AC-2.3",
    "AC-3.1", "AC-3.2", "AC-3.3",
    "AC-4.1", "AC-4.2",
}
assert set(acceptance) == expected, acceptance

design = Path("docs/DESIGN.md").read_text(encoding="utf-8")
for marker in sorted(expected):
    assert marker in design, marker
for heading in (
    "## 3. 模块地图",
    "## 4. 依赖方向",
    "## 6. 核心数据结构",
    "## 7. 状态变化",
    "## 8. AI 调用边界",
    "## 10. 测试策略",
    "## 11. 测试先行证据",
):
    assert heading in design, heading
print("W2_SPEC_TRACEABILITY_CHECK=PASS ac=10")
print("W2_DESIGN_STRUCTURE_CHECK=PASS")

adr_paths = sorted(Path("docs/adr").glob("ADR-*.md"))
assert len(adr_paths) == 2, adr_paths
for path in adr_paths:
    text = path.read_text(encoding="utf-8")
    for heading in (
        "## Status",
        "## Context",
        "## Alternatives",
        "## Rejected Options",
        "## Decision",
        "## Consequences",
        "## Rollback",
    ):
        assert heading in text, (path, heading)
print("W2_ADR_STRUCTURE_CHECK=PASS count=2")
PY

python3 -m json.tool spike/tests/w2_design_review_request.json >/dev/null
python3 -m unittest discover -s spike/tests -p 'test_ai_contract.py' -v

rg -F "W2_AI_CONTRACT_RED_GREEN=PASS" \
  evidence/2410311404-code-coach-w2-contract-red-green.md >/dev/null
rg -F "W2_DESIGN_REVIEW=PASS" \
  evidence/2410311404-code-coach-w2-design-review.md >/dev/null
rg -F "W2_GATE_DECISION=MODIFIED_PASS" \
  process/gate/2410311404-code-coach-gate-2-design.md >/dev/null

residue="$(rg -n \
  '<YYYY-MM-DD>|<项目名称>|<风险>|TODO|TBD|待填写|待补|Lorem ipsum|changeme' \
  -g '!.git/**' -g '!scripts/check_*.sh' . || true)"
if test -n "${residue}"; then
  printf '%s\n' "${residue}"
  echo "W2_TEMPLATE_RESIDUE_CHECK=FAIL"
  exit 1
fi

if rg -n -i '\b\x73\x6f\x6c\x6f\b' -g '!.git/**' .; then
  echo "W2_NAMING_CHECK=FAIL"
  exit 1
fi

if rg -n '[[:blank:]]+$' -g '!.git/**' -g '!spike/tmp/**' .; then
  echo "W2_TRAILING_WHITESPACE_CHECK=FAIL"
  exit 1
fi

if rg -n \
  'sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|BEGIN [A-Z ]*PRIVATE KEY' \
  -g '!.git/**' -g '!scripts/check_*.sh' .; then
  echo "W2_SECRET_SCAN=FAIL"
  exit 1
fi

git diff --check

echo "W2_AI_CONTRACT_TEST=PASS tests=3"
echo "W2_TEMPLATE_RESIDUE_CHECK=PASS"
echo "W2_NAMING_CHECK=PASS"
echo "W2_SECRET_SCAN=PASS"
echo "W2_GATE_CHECK=PASS"

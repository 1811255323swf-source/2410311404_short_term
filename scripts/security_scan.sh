#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

patterns=(
  'sk-[A-Za-z0-9_-]{20,}'
  'AKIA[0-9A-Z]{16}'
  'ghp_[A-Za-z0-9_]{20,}'
  'git''hub_pat_[A-Za-z0-9_]+'
  'glpat-[A-Za-z0-9_-]{20,}'
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'
  'Bearer[[:space:]]+[A-Za-z0-9._~+/-]{20,}'
  '(API_KEY|ACCESS_TOKEN|PASSWORD|SECRET)[[:space:]]*[:=][[:space:]]*["'\''][A-Za-z0-9._~+/-]{12,}'
)

found=""
for pattern in "${patterns[@]}"; do
  matches="$(rg -n -i \
    -g '!.git/**' \
    -g '!.venv/**' \
    -g '!__pycache__/**' \
    -g '!*.db*' \
    -g '!scripts/security_scan.sh' \
    -g '!scripts/check_w1.sh' \
    -g '!scripts/check_w2.sh' \
    -- "${pattern}" . || true)"
  if test -n "${matches}"; then
    found+="${matches}"$'\n'
  fi
done

if test -n "${found}"; then
  printf '%s' "${found}"
  echo "SECURITY_SCAN=FAIL"
  exit 1
fi

echo "SECURITY_SCAN=PASS"

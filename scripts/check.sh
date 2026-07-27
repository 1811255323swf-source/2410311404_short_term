#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if ! test -x .venv/bin/python; then
  echo "ENV_CHECK=FAIL missing=.venv"
  exit 1
fi

.venv/bin/python -m pip check
bash scripts/check_w2.sh
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q app tests
bash scripts/security_scan.sh

if rg -n '[[:blank:]]+$' \
  -g '!.git/**' \
  -g '!.venv/**' \
  -g '!__pycache__/**' \
  -g '!*.db*' \
  .; then
  echo "TRAILING_WHITESPACE_CHECK=FAIL"
  exit 1
fi

git diff --check

echo "DEPENDENCY_CHECK=PASS"
echo "PYTHON_TESTS=PASS"
echo "PYTHON_COMPILE_CHECK=PASS"
echo "TRAILING_WHITESPACE_CHECK=PASS"
echo "DELIVERY_CHECK=PASS"

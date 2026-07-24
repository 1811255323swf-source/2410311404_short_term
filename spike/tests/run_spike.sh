#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BIN_DIR="${ROOT}/spike/tmp"
BIN="${BIN_DIR}/language_detector"

mkdir -p "${BIN_DIR}"

g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror \
  "${ROOT}/spike/src/language_detector.cpp" \
  -o "${BIN}"

CPP_JSON="$("${BIN}" "${ROOT}/spike/tests/sample.cpp")"
PY_JSON="$("${BIN}" "${ROOT}/spike/tests/sample.py")"
UNKNOWN_JSON="$("${BIN}" "${ROOT}/spike/tests/ambiguous.txt")"

python3 - "${CPP_JSON}" "${PY_JSON}" "${UNKNOWN_JSON}" <<'PY'
import json
import sys

cpp, python, unknown = (json.loads(value) for value in sys.argv[1:])

assert cpp["detected_language"] == "cpp", cpp
assert cpp["confidence"] >= 0.80, cpp
assert len(cpp["detection_evidence"]) >= 2, cpp
assert cpp["python_score"] == 0, cpp

assert python["detected_language"] == "python", python
assert python["confidence"] >= 0.80, python
assert len(python["detection_evidence"]) >= 2, python
assert python["cpp_score"] == 0, python

assert unknown["detected_language"] == "unknown", unknown
assert unknown["confidence"] < 0.80, unknown

print("CPP_RESULT=" + json.dumps(cpp, ensure_ascii=False, sort_keys=True))
print("PYTHON_RESULT=" + json.dumps(python, ensure_ascii=False, sort_keys=True))
print("UNKNOWN_RESULT=" + json.dumps(unknown, ensure_ascii=False, sort_keys=True))
print("W1_LANGUAGE_DETECTION_SPIKE=PASS")
PY

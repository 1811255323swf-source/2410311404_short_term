#!/usr/bin/env python3
"""Run a local, redacted Ollama capability probe and print contract status."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib import request


ROOT = Path(__file__).resolve().parents[2]
REQUEST_PATH = ROOT / "spike" / "tests" / "ai_request.json"
REQUIRED_FIELDS = {"summary", "repair_order", "concept_link", "exercise"}


def main() -> int:
    host = os.environ.get("OLLAMA_HOST", "127.0.0.1:11435")
    url = f"http://{host}/api/chat"
    payload = REQUEST_PATH.read_bytes()
    http_request = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with request.urlopen(http_request, timeout=60) as response:
        outer = json.loads(response.read().decode("utf-8"))

    content = outer.get("message", {}).get("content", "")
    try:
        coaching = json.loads(content)
    except json.JSONDecodeError:
        coaching = {}

    summary_ok = isinstance(coaching.get("summary"), str) and bool(
        coaching["summary"].strip()
    )
    fields_present = REQUIRED_FIELDS.issubset(coaching)
    field_types_valid = fields_present and all(
        isinstance(coaching[field], str) for field in REQUIRED_FIELDS
    )

    print(f"MODEL={outer.get('model', 'unknown')}")
    print(f"DONE_REASON={outer.get('done_reason', 'unknown')}")
    print(f"CONTENT_JSON={'PASS' if coaching else 'FAIL'}")
    print(f"REQUIRED_FIELDS={'PASS' if fields_present else 'PARTIAL'}")
    print(f"FIELD_TYPES={'PASS' if field_types_valid else 'PARTIAL'}")
    print(f"AI_EXPLANATION_CAPABILITY={'PASS' if summary_ok else 'FAIL'}")
    print(
        "AI_STRUCTURED_CONTRACT="
        + ("PASS" if field_types_valid else "PARTIAL_VALIDATION_REQUIRED")
    )
    return 0 if summary_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

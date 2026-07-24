#!/usr/bin/env python3
"""Contract tests for the W2 AI coaching boundary."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from ai_contract import validate_ai_coaching  # noqa: E402


class AiCoachingContractTest(unittest.TestCase):
    def test_valid_coaching_payload_is_accepted(self) -> None:
        payload = {
            "summary": "NULL should be replaced with nullptr here.",
            "repair_order": ["replace NULL", "compile again"],
            "concept_links": ["C++ nullptr is not Python None"],
            "exercises": ["compare null handling in both languages"],
        }

        valid, errors = validate_ai_coaching(payload)

        self.assertTrue(valid)
        self.assertEqual([], errors)

    def test_missing_fields_are_rejected(self) -> None:
        payload = {
            "summary": "partial response",
            "repair_order": ["retry"],
        }

        valid, errors = validate_ai_coaching(payload)

        self.assertFalse(valid)
        self.assertIn("missing:concept_links", errors)
        self.assertIn("missing:exercises", errors)

    def test_wrong_field_types_are_rejected(self) -> None:
        payload = {
            "summary": ["not a string"],
            "repair_order": "not a list",
            "concept_links": ["valid item"],
            "exercises": ["valid item"],
        }

        valid, errors = validate_ai_coaching(payload)

        self.assertFalse(valid)
        self.assertIn("type:summary", errors)
        self.assertIn("type:repair_order", errors)


if __name__ == "__main__":
    unittest.main()

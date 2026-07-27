from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any


AI_REQUIRED_FIELDS = (
    "summary",
    "repair_order",
    "concept_links",
    "exercises",
)


@dataclass(frozen=True)
class StaticIssue:
    issue_id: str
    rule_id: str
    severity: str
    line: int
    message: str
    local_context_hash: str

    @classmethod
    def create(
        cls,
        *,
        rule_id: str,
        severity: str,
        line: int,
        message: str,
        source_line: str,
    ) -> "StaticIssue":
        normalized_message = " ".join(message.split())
        context_hash = sha256(source_line.strip().encode("utf-8")).hexdigest()[:16]
        identity = f"{rule_id}|{normalized_message}|{context_hash}"
        issue_id = sha256(identity.encode("utf-8")).hexdigest()[:16]
        return cls(
            issue_id=issue_id,
            rule_id=rule_id,
            severity=severity,
            line=max(1, line),
            message=normalized_message,
            local_context_hash=context_hash,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DetectionResult:
    language: str
    confidence: float
    evidence: list[str]
    cpp_score: int
    python_score: int
    cpp_probe: str
    python_probe: str
    decision_reason: str


@dataclass(frozen=True)
class AiResult:
    status: str
    coaching: dict[str, Any] | None
    error_type: str | None = None
    attempts: int = 0


@dataclass(frozen=True)
class ReviewResult:
    review_id: str
    created_at: str
    detected_language: str
    confidence: float
    detection_evidence: list[str]
    static_issues: list[StaticIssue]
    score: int
    ai_status: str
    ai_coaching: dict[str, Any] | None
    rule_version: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["static_issues"] = [issue.to_dict() for issue in self.static_issues]
        return payload


@dataclass(frozen=True)
class StoredReview:
    result: ReviewResult
    code_hash: str


@dataclass(frozen=True)
class ComparisonResult:
    review_id: str
    revision_id: str
    resolved_issue_ids: list[str]
    remaining_issue_ids: list[str]
    new_issue_ids: list[str]
    score_delta: int
    score: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_ai_coaching(payload: Any) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return False, ["payload must be an object"]

    missing = [field for field in AI_REQUIRED_FIELDS if field not in payload]
    errors.extend(f"missing required field: {field}" for field in missing)

    summary = payload.get("summary")
    if "summary" in payload and (not isinstance(summary, str) or not summary.strip()):
        errors.append("summary must be a non-empty string")

    for field in AI_REQUIRED_FIELDS[1:]:
        value = payload.get(field)
        if field not in payload:
            continue
        if not isinstance(value, list):
            errors.append(f"{field} must be a list of strings")
            continue
        if not value:
            errors.append(f"{field} must contain at least one item")
            continue
        if any(not isinstance(item, str) or not item.strip() for item in value):
            errors.append(f"{field} must contain only non-empty strings")

    return not errors, errors

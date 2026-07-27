from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.adapters.ai_coach import AiCoach
from app.analyzers.cpp_analyzer import CppAnalyzer
from app.analyzers.python_analyzer import PythonAnalyzer
from app.detectors.language_detector import LanguageDetector
from app.domain.comparison import compare_issues
from app.domain.contracts import (
    AiResult,
    ComparisonResult,
    ReviewResult,
    StoredReview,
)
from app.domain.errors import DomainError
from app.domain.scoring import calculate_score
from app.reporting.markdown_reporter import MarkdownReporter
from app.security.input_guard import InputGuard
from app.storage.repository import ReviewRepository


RULE_VERSION = "2026.07.23"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class ReviewService:
    def __init__(
        self,
        *,
        repository: ReviewRepository,
        ai_coach: AiCoach,
        detector: LanguageDetector | None = None,
        input_guard: InputGuard | None = None,
        reporter: MarkdownReporter | None = None,
    ):
        self.repository = repository
        self.ai_coach = ai_coach
        self.detector = detector or LanguageDetector()
        self.input_guard = input_guard or InputGuard()
        self.reporter = reporter or MarkdownReporter()
        self.analyzers = {
            "cpp": CppAnalyzer(),
            "python": PythonAnalyzer(),
        }

    def review(
        self,
        code: str,
        goal: str = "",
        request_ai: bool = True,
    ) -> ReviewResult:
        inspection = self.input_guard.validate(code)
        goal_sensitive = bool(goal) and self.input_guard.inspect(goal).sensitive
        detection = self.detector.detect(code)
        if detection.language == "unknown":
            raise DomainError(
                422,
                "language_unknown",
                "Language evidence is insufficient or conflicting",
            )

        issues = self.analyzers[detection.language].analyze(code)
        score = calculate_score(issues)
        ai_result = self._coach(
            code=code,
            language=detection.language,
            issues=issues,
            goal=goal,
            request_ai=request_ai,
            sensitive=inspection.sensitive or goal_sensitive,
        )
        review = ReviewResult(
            review_id=uuid4().hex[:16],
            created_at=_utc_now(),
            detected_language=detection.language,
            confidence=detection.confidence,
            detection_evidence=detection.evidence,
            static_issues=issues,
            score=score,
            ai_status=ai_result.status,
            ai_coaching=ai_result.coaching,
            rule_version=RULE_VERSION,
        )
        self.repository.save_review(
            StoredReview(result=review, code_hash=inspection.code_hash)
        )
        return review

    def _coach(
        self,
        *,
        code: str,
        language: str,
        issues,
        goal: str,
        request_ai: bool,
        sensitive: bool,
    ) -> AiResult:
        if not request_ai:
            return AiResult(status="not_requested", coaching=None)
        if sensitive:
            return AiResult(
                status="blocked_sensitive_input",
                coaching=None,
                error_type="blocked_sensitive_input",
            )
        return self.ai_coach.coach(language, issues, goal)

    def compare(self, review_id: str, code: str) -> ComparisonResult:
        stored = self.repository.get_review(review_id)
        if stored is None:
            raise DomainError(404, "review_not_found", "Review does not exist")

        inspection = self.input_guard.validate(code)
        detection = self.detector.detect(code)
        if detection.language == "unknown":
            raise DomainError(
                422,
                "language_unknown",
                "Language evidence is insufficient or conflicting",
            )
        if detection.language != stored.result.detected_language:
            raise DomainError(
                422,
                "language_mismatch",
                "Revision language differs from the original review",
            )

        issues = self.analyzers[detection.language].analyze(code)
        score = calculate_score(issues)
        revision_id = uuid4().hex[:16]
        comparison = compare_issues(
            stored.result.static_issues,
            issues,
            before_score=stored.result.score,
            after_score=score,
            review_id=review_id,
            revision_id=revision_id,
        )
        self.repository.save_revision(
            comparison,
            created_at=_utc_now(),
            code_hash=inspection.code_hash,
        )
        return comparison

    def report(self, review_id: str) -> str:
        stored = self.repository.get_review(review_id)
        if stored is None:
            raise DomainError(404, "review_not_found", "Review does not exist")
        revisions = self.repository.get_revisions(review_id)
        return self.reporter.render(stored, revisions)

from app.adapters.ai_coach import AiCoach, MockAiProvider
from app.application.review_service import ReviewService
from app.storage.repository import ReviewRepository


INITIAL_CPP = """\
#include <cstddef>
int main() {
    int* value = NULL;
    return value == NULL;
}
"""

REVISED_CPP = """\
#include <cstddef>
int main() {
    int* value = nullptr;
    return value == nullptr;
}
"""


def build_service(tmp_path):
    repository = ReviewRepository(tmp_path / "reviews.db")
    service = ReviewService(
        repository=repository,
        ai_coach=AiCoach(provider=MockAiProvider()),
    )
    return service, repository


def test_review_is_persisted_without_raw_source(tmp_path):
    service, repository = build_service(tmp_path)

    review = service.review(INITIAL_CPP, goal="learn Python", request_ai=True)

    assert review.detected_language == "cpp"
    assert review.ai_status == "available"
    assert any(issue.rule_id == "CPP-NULLPTR" for issue in review.static_issues)
    stored = repository.get_review(review.review_id)
    assert stored is not None
    assert INITIAL_CPP.encode("utf-8") not in (tmp_path / "reviews.db").read_bytes()


def test_compare_and_markdown_report_close_the_user_loop(tmp_path):
    service, _ = build_service(tmp_path)
    review = service.review(INITIAL_CPP, request_ai=False)

    comparison = service.compare(review.review_id, REVISED_CPP)
    report = service.report(review.review_id)

    assert comparison.resolved_issue_ids
    assert comparison.score_delta > 0
    assert "# code_coach 学习报告" in report
    assert review.review_id in report
    assert "原始代码" not in report

from app.domain.contracts import ComparisonResult, StaticIssue


def compare_issues(
    before: list[StaticIssue],
    after: list[StaticIssue],
    *,
    before_score: int,
    after_score: int,
    review_id: str = "",
    revision_id: str = "",
) -> ComparisonResult:
    before_ids = {issue.issue_id for issue in before}
    after_ids = {issue.issue_id for issue in after}
    return ComparisonResult(
        review_id=review_id,
        revision_id=revision_id,
        resolved_issue_ids=sorted(before_ids - after_ids),
        remaining_issue_ids=sorted(before_ids & after_ids),
        new_issue_ids=sorted(after_ids - before_ids),
        score_delta=after_score - before_score,
        score=after_score,
    )

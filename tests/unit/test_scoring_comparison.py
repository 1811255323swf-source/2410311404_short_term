from app.domain.comparison import compare_issues
from app.domain.contracts import StaticIssue
from app.domain.scoring import calculate_score


def issue(rule_id: str, severity: str, line: int = 1) -> StaticIssue:
    return StaticIssue.create(
        rule_id=rule_id,
        severity=severity,
        line=line,
        message=f"{rule_id} message",
        source_line=f"line-{line}",
    )


def test_score_is_deterministic_and_clamped():
    issues = [
        issue("E1", "error"),
        issue("W1", "warning"),
        issue("I1", "info"),
    ]

    assert calculate_score(issues) == 79
    assert calculate_score([issue(f"E{index}", "error") for index in range(10)]) == 0


def test_comparison_reports_resolved_remaining_and_new_issues():
    before = [issue("A", "warning"), issue("B", "info")]
    after = [before[1], issue("C", "error")]

    result = compare_issues(before, after, before_score=94, after_score=84)

    assert result.resolved_issue_ids == [before[0].issue_id]
    assert result.remaining_issue_ids == [before[1].issue_id]
    assert result.new_issue_ids == [after[1].issue_id]
    assert result.score_delta == -10

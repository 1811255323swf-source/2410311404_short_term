from collections.abc import Iterable

from app.domain.contracts import StaticIssue


DEDUCTIONS = {
    "error": 15,
    "warning": 5,
    "info": 1,
}


def calculate_score(issues: Iterable[StaticIssue]) -> int:
    deduction = sum(DEDUCTIONS.get(issue.severity, 0) for issue in issues)
    return max(0, 100 - deduction)

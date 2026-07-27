from __future__ import annotations

from app.domain.contracts import StoredReview


class MarkdownReporter:
    def render(
        self,
        stored: StoredReview,
        revisions: list[dict[str, object]],
    ) -> str:
        review = stored.result
        lines = [
            "# code_coach 学习报告",
            "",
            f"- Review ID: `{review.review_id}`",
            f"- Created at: `{review.created_at}`",
            f"- Language: `{review.detected_language}`",
            f"- Confidence: `{review.confidence:.2f}`",
            f"- Deterministic score: `{review.score}`",
            f"- Rule version: `{review.rule_version}`",
            f"- AI status: `{review.ai_status}`",
            "",
            "## Detection evidence",
            "",
        ]
        lines.extend(f"- {item}" for item in review.detection_evidence)

        lines.extend(["", "## Static issues", ""])
        if review.static_issues:
            for issue in review.static_issues:
                lines.append(
                    f"- `{issue.severity}` `{issue.rule_id}` line {issue.line}: "
                    f"{issue.message}"
                )
        else:
            lines.append("- No known deterministic issue was found.")

        lines.extend(["", "## AI coaching", ""])
        if review.ai_coaching is None:
            lines.append(f"- Coaching is not present; status is `{review.ai_status}`.")
        else:
            lines.append(review.ai_coaching["summary"])
            for title, field in (
                ("Repair order", "repair_order"),
                ("Concept links", "concept_links"),
                ("Exercises", "exercises"),
            ):
                lines.extend(["", f"### {title}", ""])
                lines.extend(f"- {item}" for item in review.ai_coaching[field])

        lines.extend(["", "## Revisions", ""])
        if not revisions:
            lines.append("- No revision has been compared.")
        for revision in revisions:
            lines.extend(
                [
                    f"### Revision `{revision['revision_id']}`",
                    "",
                    f"- Score: `{revision['score']}`",
                    f"- Resolved: `{len(revision['resolved_issue_ids'])}`",
                    f"- Remaining: `{len(revision['remaining_issue_ids'])}`",
                    f"- New: `{len(revision['new_issue_ids'])}`",
                    "",
                ]
            )

        lines.extend(
            [
                "## Privacy and limits",
                "",
                "- The database stores a SHA-256 digest and issue snapshots, not source text.",
                "- AI coaching can be unavailable without changing static issues or score.",
                "- Only C++ and Python are within the accepted scope.",
                "",
            ]
        )
        return "\n".join(lines)

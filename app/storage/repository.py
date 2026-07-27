from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.domain.contracts import (
    ComparisonResult,
    ReviewResult,
    StaticIssue,
    StoredReview,
)


class ReviewRepository:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    code_hash TEXT NOT NULL,
                    rule_version TEXT NOT NULL,
                    detected_language TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    detection_evidence_json TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    ai_status TEXT NOT NULL,
                    ai_coaching_json TEXT
                );

                CREATE TABLE IF NOT EXISTS issue_snapshots (
                    review_id TEXT NOT NULL,
                    issue_id TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    line INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    local_context_hash TEXT NOT NULL,
                    PRIMARY KEY (review_id, issue_id),
                    FOREIGN KEY (review_id) REFERENCES reviews(review_id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS revisions (
                    revision_id TEXT PRIMARY KEY,
                    review_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    code_hash TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    resolved_issue_ids_json TEXT NOT NULL,
                    remaining_issue_ids_json TEXT NOT NULL,
                    new_issue_ids_json TEXT NOT NULL,
                    FOREIGN KEY (review_id) REFERENCES reviews(review_id)
                        ON DELETE CASCADE
                );
                """
            )

    def save_review(self, stored: StoredReview) -> None:
        review = stored.result
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO reviews (
                    review_id, created_at, code_hash, rule_version,
                    detected_language, confidence, detection_evidence_json,
                    score, ai_status, ai_coaching_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review.review_id,
                    review.created_at,
                    stored.code_hash,
                    review.rule_version,
                    review.detected_language,
                    review.confidence,
                    json.dumps(review.detection_evidence, ensure_ascii=False),
                    review.score,
                    review.ai_status,
                    (
                        json.dumps(review.ai_coaching, ensure_ascii=False)
                        if review.ai_coaching is not None
                        else None
                    ),
                ),
            )
            connection.executemany(
                """
                INSERT INTO issue_snapshots (
                    review_id, issue_id, rule_id, severity,
                    line, message, local_context_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        review.review_id,
                        issue.issue_id,
                        issue.rule_id,
                        issue.severity,
                        issue.line,
                        issue.message,
                        issue.local_context_hash,
                    )
                    for issue in review.static_issues
                ],
            )

    def get_review(self, review_id: str) -> StoredReview | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM reviews WHERE review_id = ?",
                (review_id,),
            ).fetchone()
            if row is None:
                return None
            issue_rows = connection.execute(
                """
                SELECT * FROM issue_snapshots
                WHERE review_id = ?
                ORDER BY line, rule_id, issue_id
                """,
                (review_id,),
            ).fetchall()

        issues = [
            StaticIssue(
                issue_id=issue["issue_id"],
                rule_id=issue["rule_id"],
                severity=issue["severity"],
                line=issue["line"],
                message=issue["message"],
                local_context_hash=issue["local_context_hash"],
            )
            for issue in issue_rows
        ]
        review = ReviewResult(
            review_id=row["review_id"],
            created_at=row["created_at"],
            detected_language=row["detected_language"],
            confidence=row["confidence"],
            detection_evidence=json.loads(row["detection_evidence_json"]),
            static_issues=issues,
            score=row["score"],
            ai_status=row["ai_status"],
            ai_coaching=(
                json.loads(row["ai_coaching_json"])
                if row["ai_coaching_json"] is not None
                else None
            ),
            rule_version=row["rule_version"],
        )
        return StoredReview(result=review, code_hash=row["code_hash"])

    def save_revision(
        self,
        comparison: ComparisonResult,
        *,
        created_at: str,
        code_hash: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO revisions (
                    revision_id, review_id, created_at, code_hash, score,
                    resolved_issue_ids_json, remaining_issue_ids_json,
                    new_issue_ids_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    comparison.revision_id,
                    comparison.review_id,
                    created_at,
                    code_hash,
                    comparison.score,
                    json.dumps(comparison.resolved_issue_ids),
                    json.dumps(comparison.remaining_issue_ids),
                    json.dumps(comparison.new_issue_ids),
                ),
            )

    def get_revisions(self, review_id: str) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT revision_id, created_at, score,
                       resolved_issue_ids_json, remaining_issue_ids_json,
                       new_issue_ids_json
                FROM revisions
                WHERE review_id = ?
                ORDER BY created_at, revision_id
                """,
                (review_id,),
            ).fetchall()
        return [
            {
                "revision_id": row["revision_id"],
                "created_at": row["created_at"],
                "score": row["score"],
                "resolved_issue_ids": json.loads(row["resolved_issue_ids_json"]),
                "remaining_issue_ids": json.loads(row["remaining_issue_ids_json"]),
                "new_issue_ids": json.loads(row["new_issue_ids_json"]),
            }
            for row in rows
        ]

from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256

from app.domain.errors import DomainError


MAX_CODE_CHARS = 20_000

_SENSITIVE_PATTERNS = (
    (
        "credential_assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|access[_-]?token|token|password|secret)\b"
            r"\s*[:=]\s*[\"'][^\"'\r\n]{6,}[\"']"
        ),
    ),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("authorization_header", re.compile(r"(?i)\bAuthorization\s*:\s*Bearer\s+\S+")),
)


@dataclass(frozen=True)
class GuardInspection:
    code_hash: str
    sensitive: bool
    reason: str


class InputGuard:
    def inspect(self, code: str) -> GuardInspection:
        digest = sha256(code.encode("utf-8")).hexdigest()
        for reason, pattern in _SENSITIVE_PATTERNS:
            if pattern.search(code):
                return GuardInspection(
                    code_hash=digest,
                    sensitive=True,
                    reason=reason,
                )
        return GuardInspection(
            code_hash=digest,
            sensitive=False,
            reason="clear",
        )

    def validate(self, code: str) -> GuardInspection:
        if not isinstance(code, str) or not code.strip():
            raise DomainError(400, "empty_code", "Code must not be empty")
        if len(code) > MAX_CODE_CHARS:
            raise DomainError(
                413,
                "code_too_large",
                f"Code must not exceed {MAX_CODE_CHARS} characters",
            )
        return self.inspect(code)

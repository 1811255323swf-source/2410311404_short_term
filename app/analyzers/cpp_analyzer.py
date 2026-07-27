from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.domain.contracts import StaticIssue
from app.security.process_limits import limited_syntax_command


_DIAGNOSTIC = re.compile(
    r"^.*?:(?P<line>\d+):(?:(?P<column>\d+):)?\s*"
    r"(?P<severity>fatal error|error|warning|note):\s*(?P<message>.+)$"
)


class CppAnalyzer:
    def __init__(self, timeout_seconds: float = 3.0):
        self.timeout_seconds = timeout_seconds

    def analyze(self, code: str) -> list[StaticIssue]:
        lines = code.splitlines()
        issues = self._compiler_issues(code, lines)
        issues.extend(self._learning_rules(lines))
        unique = {issue.issue_id: issue for issue in issues}
        return sorted(
            unique.values(),
            key=lambda item: (item.line, item.rule_id, item.issue_id),
        )

    def _compiler_issues(
        self,
        code: str,
        lines: list[str],
    ) -> list[StaticIssue]:
        compiler = shutil.which("g++")
        if compiler is None:
            return [
                StaticIssue.create(
                    rule_id="CPP-TOOL-UNAVAILABLE",
                    severity="warning",
                    line=1,
                    message="g++ syntax checker is unavailable",
                    source_line="",
                )
            ]

        try:
            with tempfile.TemporaryDirectory(prefix="code_coach_analyze_") as directory:
                source_path = Path(directory) / "input.cpp"
                source_path.write_text(code, encoding="utf-8")
                command = limited_syntax_command(
                    [
                        compiler,
                        "-std=c++17",
                        "-Wall",
                        "-Wextra",
                        "-Wpedantic",
                        "-x",
                        "c++",
                        "-fsyntax-only",
                        str(source_path),
                    ]
                )
                result = subprocess.run(
                    command,
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
        except subprocess.TimeoutExpired:
            return [
                StaticIssue.create(
                    rule_id="CPP-TOOL-TIMEOUT",
                    severity="warning",
                    line=1,
                    message="g++ syntax checker exceeded the 3 second budget",
                    source_line="",
                )
            ]
        except OSError:
            return [
                StaticIssue.create(
                    rule_id="CPP-TOOL-UNAVAILABLE",
                    severity="warning",
                    line=1,
                    message="g++ syntax checker could not be started",
                    source_line="",
                )
            ]

        issues: list[StaticIssue] = []
        for diagnostic in result.stderr.splitlines():
            match = _DIAGNOSTIC.match(diagnostic)
            if not match or match.group("severity") == "note":
                continue
            line = int(match.group("line"))
            compiler_severity = match.group("severity")
            severity = "error" if "error" in compiler_severity else "warning"
            rule_id = "CPP-SYNTAX" if severity == "error" else "CPP-COMPILER-WARNING"
            message = match.group("message")
            source_line = lines[line - 1] if 0 < line <= len(lines) else ""
            issues.append(
                StaticIssue.create(
                    rule_id=rule_id,
                    severity=severity,
                    line=line,
                    message=message,
                    source_line=source_line,
                )
            )
        return issues

    def _learning_rules(self, lines: list[str]) -> list[StaticIssue]:
        issues: list[StaticIssue] = []
        for line_number, source_line in enumerate(lines, start=1):
            if re.search(r"\bNULL\b", source_line):
                issues.append(
                    StaticIssue.create(
                        rule_id="CPP-NULLPTR",
                        severity="warning",
                        line=line_number,
                        message="Prefer nullptr for a typed C++ null pointer",
                        source_line=source_line,
                    )
                )
            if re.search(r"\bnew\s+[A-Za-z_]", source_line):
                issues.append(
                    StaticIssue.create(
                        rule_id="CPP-RAW-NEW",
                        severity="warning",
                        line=line_number,
                        message="Prefer RAII containers or smart pointers over raw new",
                        source_line=source_line,
                    )
                )
            if "using namespace std;" in source_line:
                issues.append(
                    StaticIssue.create(
                        rule_id="CPP-USING-NAMESPACE",
                        severity="info",
                        line=line_number,
                        message="Avoid a global using namespace directive in reusable code",
                        source_line=source_line,
                    )
                )
        return issues

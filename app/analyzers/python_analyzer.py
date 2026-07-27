from __future__ import annotations

import ast

from app.domain.contracts import StaticIssue


class _LearningRuleVisitor(ast.NodeVisitor):
    def __init__(self, lines: list[str]):
        self.lines = lines
        self.issues: list[StaticIssue] = []

    def source_line(self, line: int) -> str:
        return self.lines[line - 1] if 0 < line <= len(self.lines) else ""

    def add(self, node: ast.AST, rule_id: str, severity: str, message: str) -> None:
        line = getattr(node, "lineno", 1)
        self.issues.append(
            StaticIssue.create(
                rule_id=rule_id,
                severity=severity,
                line=line,
                message=message,
                source_line=self.source_line(line),
            )
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        defaults = [*node.args.defaults, *node.args.kw_defaults]
        if any(isinstance(value, (ast.List, ast.Dict, ast.Set)) for value in defaults):
            self.add(
                node,
                "PY-MUTABLE-DEFAULT",
                "warning",
                "Use None and create the mutable value inside the function",
            )
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self.add(
                node,
                "PY-BARE-EXCEPT",
                "warning",
                "Catch a specific exception instead of using bare except",
            )
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        values = [node.left, *node.comparators]
        contains_none = any(
            isinstance(value, ast.Constant) and value.value is None for value in values
        )
        uses_equality = any(isinstance(operator, (ast.Eq, ast.NotEq)) for operator in node.ops)
        if contains_none and uses_equality:
            self.add(
                node,
                "PY-NONE-IDENTITY",
                "warning",
                "Compare None with is or is not",
            )
        self.generic_visit(node)


class PythonAnalyzer:
    def analyze(self, code: str) -> list[StaticIssue]:
        lines = code.splitlines()
        try:
            tree = ast.parse(code)
        except SyntaxError as error:
            line = error.lineno or 1
            source_line = lines[line - 1] if 0 < line <= len(lines) else ""
            return [
                StaticIssue.create(
                    rule_id="PY-SYNTAX",
                    severity="error",
                    line=line,
                    message=error.msg,
                    source_line=source_line,
                )
            ]

        visitor = _LearningRuleVisitor(lines)
        visitor.visit(tree)
        unique = {issue.issue_id: issue for issue in visitor.issues}
        return sorted(
            unique.values(),
            key=lambda item: (item.line, item.rule_id, item.issue_id),
        )

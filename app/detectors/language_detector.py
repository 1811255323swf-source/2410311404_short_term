from __future__ import annotations

import ast
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.domain.contracts import DetectionResult
from app.security.process_limits import limited_syntax_command


@dataclass
class _Score:
    value: int
    evidence: list[str]


def _score_cpp(code: str) -> _Score:
    value = 0
    evidence: list[str] = []

    def add(weight: int, label: str) -> None:
        nonlocal value
        value += weight
        evidence.append(label)

    if "#include" in code:
        add(5, "cpp:#include")
    if re.search(r"\bint\s+main\s*\(", code):
        add(5, "cpp:int-main")
    if "std::" in code:
        add(4, "cpp:std-namespace")
    if re.search(r"\b(vector|string|map|unordered_map|set)\s*<", code):
        add(3, "cpp:template-type")
    if code.count(";") >= 2 and "{" in code and "}" in code:
        add(2, "cpp:brace-semicolon-structure")
    if "nullptr" in code or (value >= 5 and "->" in code):
        add(2, "cpp:pointer-syntax")
    return _Score(value, evidence)


def _score_python(code: str) -> _Score:
    value = 0
    evidence: list[str] = []

    def add(weight: int, label: str) -> None:
        nonlocal value
        value += weight
        evidence.append(label)

    if re.search(r"(^|\n)\s*(async\s+)?def\s+[A-Za-z_]\w*\s*\([^\n]*\)\s*:", code):
        add(5, "python:def-block")
    if re.search(r"(^|\n)\s*(from\s+\S+\s+import|import\s+\S+)", code):
        add(4, "python:import-statement")
    if "if __name__" in code:
        add(5, "python:main-guard")
    if re.search(r"\b(None|True|False)\b", code):
        add(2, "python:built-in-literal")
    if re.search(
        r"(^|\n)\s*(for|while|if|elif|else|try|except|with|class)\b[^\n]*:",
        code,
    ):
        add(3, "python:colon-block")
    if value >= 3 and "\n    " in code and ":" in code:
        add(2, "python:indented-block")
    return _Score(value, evidence)


def _probe_python(code: str) -> str:
    try:
        ast.parse(code)
    except (SyntaxError, ValueError, TypeError):
        return "failed"
    return "passed"


def _probe_cpp(code: str, timeout_seconds: float) -> str:
    compiler = shutil.which("g++")
    if compiler is None:
        return "unavailable"

    try:
        with tempfile.TemporaryDirectory(prefix="code_coach_probe_") as directory:
            source_path = Path(directory) / "input.cpp"
            source_path.write_text(code, encoding="utf-8")
            command = limited_syntax_command(
                [
                    compiler,
                    "-std=c++17",
                    "-x",
                    "c++",
                    "-fsyntax-only",
                    str(source_path),
                ]
            )
            completed = subprocess.run(
                command,
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
    except subprocess.TimeoutExpired:
        return "timeout"
    except OSError:
        return "unavailable"
    return "passed" if completed.returncode == 0 else "failed"


class LanguageDetector:
    def __init__(self, probe_timeout_seconds: float = 3.0):
        self.probe_timeout_seconds = probe_timeout_seconds

    def detect(self, code: str) -> DetectionResult:
        cpp = _score_cpp(code)
        python = _score_python(code)
        cpp_probe = _probe_cpp(code, self.probe_timeout_seconds)
        python_probe = _probe_python(code)

        maximum = max(cpp.value, python.value)
        difference = abs(cpp.value - python.value)
        strong_candidate = maximum >= 5 and difference >= 3

        if strong_candidate:
            language = "cpp" if cpp.value > python.value else "python"
            score = cpp if language == "cpp" else python
            probe = cpp_probe if language == "cpp" else python_probe
            confidence = 0.95 if probe == "passed" else 0.82
            evidence = [*score.evidence, f"{language}_probe:{probe}"]
            return DetectionResult(
                language=language,
                confidence=confidence,
                evidence=evidence,
                cpp_score=cpp.value,
                python_score=python.value,
                cpp_probe=cpp_probe,
                python_probe=python_probe,
                decision_reason="strong_feature_candidate",
            )

        weak_cpp = cpp.value > python.value and cpp.value > 0
        weak_python = python.value > cpp.value and python.value > 0
        if weak_cpp and cpp_probe == "passed" and python_probe == "failed":
            return DetectionResult(
                language="cpp",
                confidence=0.80,
                evidence=[*cpp.evidence, "cpp_probe:passed"],
                cpp_score=cpp.value,
                python_score=python.value,
                cpp_probe=cpp_probe,
                python_probe=python_probe,
                decision_reason="weak_features_with_single_probe",
            )
        if weak_python and python_probe == "passed" and cpp_probe == "failed":
            return DetectionResult(
                language="python",
                confidence=0.80,
                evidence=[*python.evidence, "python_probe:passed"],
                cpp_score=cpp.value,
                python_score=python.value,
                cpp_probe=cpp_probe,
                python_probe=python_probe,
                decision_reason="weak_features_with_single_probe",
            )

        confidence = min(0.79, maximum / 10.0)
        return DetectionResult(
            language="unknown",
            confidence=confidence,
            evidence=[
                f"cpp_score:{cpp.value}",
                f"python_score:{python.value}",
                f"cpp_probe:{cpp_probe}",
                f"python_probe:{python_probe}",
            ],
            cpp_score=cpp.value,
            python_score=python.value,
            cpp_probe=cpp_probe,
            python_probe=python_probe,
            decision_reason="insufficient_or_conflicting_evidence",
        )

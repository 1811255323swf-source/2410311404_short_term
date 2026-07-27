from pathlib import Path
import shutil
import subprocess

import app.detectors.language_detector as detector_module
from app.detectors.language_detector import LanguageDetector
from app.security.process_limits import limited_syntax_command


CPP_SAMPLE = """\
#include <iostream>
int main() {
    std::cout << "hello";
    return 0;
}
"""

PYTHON_SAMPLE = """\
from pathlib import Path

def greet(name):
    return f"hello {name}"

if __name__ == "__main__":
    print(greet("student"))
"""


def test_complete_cpp_and_python_samples_are_detected():
    detector = LanguageDetector()

    cpp = detector.detect(CPP_SAMPLE)
    python = detector.detect(PYTHON_SAMPLE)

    assert cpp.language == "cpp"
    assert cpp.confidence >= 0.80
    assert len(cpp.evidence) >= 2
    assert python.language == "python"
    assert python.confidence >= 0.80
    assert len(python.evidence) >= 2


def test_ambiguous_assignment_stays_unknown():
    result = LanguageDetector().detect("value = 1")

    assert result.language == "unknown"
    assert result.confidence < 0.80


def test_strong_cpp_with_syntax_error_still_routes_to_cpp():
    source = '#include <iostream>\nint main( { std::cout << "x"; }\n'

    result = LanguageDetector().detect(source)

    assert result.language == "cpp"
    assert result.confidence >= 0.80
    assert "cpp_probe:failed" in result.evidence


def test_syntax_probe_never_executes_user_program(tmp_path: Path):
    created_by_program = tmp_path / "must-not-exist.txt"
    source = f"""\
#include <fstream>
int main() {{
    std::ofstream("{created_by_program}") << "unsafe";
    return 0;
}}
"""

    result = LanguageDetector().detect(source)

    assert result.language == "cpp"
    assert not created_by_program.exists()


def test_cpp_probe_command_has_syntax_only_and_resource_limits():
    command = limited_syntax_command(["g++", "-fsyntax-only", "input.cpp"])

    assert "-fsyntax-only" in command
    if shutil.which("prlimit"):
        assert "--as=536870912" in command
        assert "--cpu=4" in command
        assert "--fsize=1048576" in command
        assert "--nofile=64" in command
        assert "--" in command


def test_cpp_probe_unavailable_is_observable_for_strong_cpp(monkeypatch):
    monkeypatch.setattr(detector_module.shutil, "which", lambda name: None)

    result = LanguageDetector().detect(CPP_SAMPLE)

    assert result.language == "cpp"
    assert result.cpp_probe == "unavailable"
    assert "cpp_probe:unavailable" in result.evidence


def test_cpp_probe_timeout_is_observable_for_strong_cpp(monkeypatch):
    monkeypatch.setattr(
        detector_module.shutil,
        "which",
        lambda name: "/usr/bin/g++",
    )

    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=3.0)

    monkeypatch.setattr(detector_module.subprocess, "run", raise_timeout)

    result = LanguageDetector().detect(CPP_SAMPLE)

    assert result.language == "cpp"
    assert result.cpp_probe == "timeout"
    assert "cpp_probe:timeout" in result.evidence


def test_conflicting_language_features_stay_unknown():
    source = (
        "#include <iostream>\n"
        "std::cout;\n"
        "def greet(name):\n"
        "    return name\n"
    )

    result = LanguageDetector().detect(source)

    assert result.cpp_score > 0
    assert result.python_score > 0
    assert result.cpp_probe == "failed"
    assert result.python_probe == "failed"
    assert result.language == "unknown"
    assert result.decision_reason == "insufficient_or_conflicting_evidence"

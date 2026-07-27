from app.analyzers.cpp_analyzer import CppAnalyzer
from app.analyzers.python_analyzer import PythonAnalyzer


def test_cpp_analyzer_reports_nullptr_learning_issue():
    source = """\
#include <cstddef>
int main() {
    int* value = NULL;
    return value == NULL;
}
"""

    issues = CppAnalyzer().analyze(source)

    assert any(issue.rule_id == "CPP-NULLPTR" for issue in issues)


def test_cpp_analyzer_normalizes_compiler_syntax_error():
    issues = CppAnalyzer().analyze("#include <iostream>\nint main( {\n")

    assert any(issue.rule_id == "CPP-SYNTAX" for issue in issues)
    assert all("/tmp/" not in issue.message for issue in issues)


def test_python_analyzer_reports_mutable_default_and_bare_except():
    source = """\
def collect(item, bucket=[]):
    try:
        bucket.append(item)
    except:
        return []
    return bucket
"""

    issues = PythonAnalyzer().analyze(source)
    rule_ids = {issue.rule_id for issue in issues}

    assert "PY-MUTABLE-DEFAULT" in rule_ids
    assert "PY-BARE-EXCEPT" in rule_ids


def test_python_analyzer_normalizes_syntax_error():
    issues = PythonAnalyzer().analyze("def broken(:\n    pass\n")

    assert len(issues) == 1
    assert issues[0].rule_id == "PY-SYNTAX"
    assert issues[0].severity == "error"

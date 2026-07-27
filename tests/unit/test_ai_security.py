from app.adapters.ai_coach import AiCoach, MockAiProvider
from app.domain.contracts import StaticIssue, validate_ai_coaching
from app.security.input_guard import InputGuard


VALID_COACHING = {
    "summary": "先修复空指针写法，再比较两种语言的空值语义。",
    "repair_order": ["把 NULL 替换为 nullptr"],
    "concept_links": ["C++ nullptr 对应 Python None 的空值概念"],
    "exercises": ["分别写一个空值判断并说明类型差异"],
}


class SequenceProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0
        self.requests = []

    def generate(self, request, timeout_seconds):
        self.requests.append(request)
        response = self.responses[self.calls]
        self.calls += 1
        return response


class FailingProvider:
    def __init__(self, error):
        self.error = error
        self.calls = 0

    def generate(self, request, timeout_seconds):
        self.calls += 1
        raise self.error


def test_ai_contract_accepts_only_complete_typed_payload():
    valid, errors = validate_ai_coaching(VALID_COACHING)
    assert valid is True
    assert errors == []

    valid, errors = validate_ai_coaching({"summary": "missing lists"})
    assert valid is False
    assert any("repair_order" in error for error in errors)


def test_ai_coach_repairs_contract_once_then_succeeds():
    provider = SequenceProvider([
        {"summary": "missing lists"},
        VALID_COACHING,
    ])
    coach = AiCoach(provider=provider)

    result = coach.coach(language="cpp", issues=[], goal="")

    assert result.status == "available"
    assert result.coaching == VALID_COACHING
    assert provider.calls == 2
    assert all("code" not in request for request in provider.requests)


def test_ai_coach_degrades_after_second_invalid_response():
    provider = SequenceProvider([
        {"summary": "still invalid"},
        {"summary": "still invalid"},
    ])

    result = AiCoach(provider=provider).coach(language="cpp", issues=[], goal="")

    assert result.status == "unavailable"
    assert result.coaching is None
    assert result.error_type == "contract_violation"
    assert provider.calls == 2


def test_ai_coach_degrades_when_provider_is_offline():
    provider = FailingProvider(OSError("offline"))

    result = AiCoach(provider=provider).coach("cpp", [], "")

    assert result.status == "unavailable"
    assert result.error_type == "offline"
    assert provider.calls == 2


def test_ai_coach_degrades_when_provider_times_out():
    provider = FailingProvider(TimeoutError("timeout"))

    result = AiCoach(provider=provider).coach("cpp", [], "")

    assert result.status == "unavailable"
    assert result.error_type == "timeout"
    assert provider.calls == 2


def test_mock_provider_is_deterministic():
    issue = StaticIssue.create(
        rule_id="CPP-NULLPTR",
        severity="warning",
        line=3,
        message="Prefer nullptr",
        source_line="int* value = NULL;",
    )
    coach = AiCoach(provider=MockAiProvider())

    first = coach.coach("cpp", [issue], "learn Python")
    second = coach.coach("cpp", [issue], "learn Python")

    assert first.coaching == second.coaching
    assert first.status == "available"


def test_sensitive_marker_is_detected_without_echoing_value():
    marker = "pass" + "word"
    source = f'// {marker} = "classroom-example-value"'

    result = InputGuard().inspect(source)

    assert result.sensitive is True
    assert result.code_hash
    assert "classroom-example-value" not in result.reason

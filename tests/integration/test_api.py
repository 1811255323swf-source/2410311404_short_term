from fastapi.testclient import TestClient

from app.adapters.ai_coach import MockAiProvider
from app.main import create_app


CPP_SOURCE = """\
#include <cstddef>
int main() {
    int* value = NULL;
    return value == NULL;
}
"""

REVISED_CPP = """\
#include <cstddef>
int main() {
    int* value = nullptr;
    return value == nullptr;
}
"""


def build_client(tmp_path):
    app = create_app(
        database_path=tmp_path / "api.db",
        ai_provider=MockAiProvider(),
    )
    return TestClient(app)


def test_review_compare_and_report_api(tmp_path):
    client = build_client(tmp_path)

    created = client.post(
        "/api/reviews",
        json={"code": CPP_SOURCE, "goal": "learn Python", "request_ai": True},
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["detected_language"] == "cpp"
    assert payload["confidence"] >= 0.80
    assert payload["ai_status"] == "available"
    review_id = payload["review_id"]

    compared = client.post(
        f"/api/reviews/{review_id}/compare",
        json={"code": REVISED_CPP},
    )
    assert compared.status_code == 200
    assert compared.json()["resolved_issue_ids"]

    report = client.get(f"/api/reviews/{review_id}/report")
    assert report.status_code == 200
    assert report.headers["content-type"].startswith("text/markdown")
    assert "# code_coach 学习报告" in report.text


def test_api_returns_observable_input_errors(tmp_path):
    client = build_client(tmp_path)

    empty = client.post("/api/reviews", json={"code": ""})
    too_large = client.post("/api/reviews", json={"code": "x" * 20001})
    unknown = client.post("/api/reviews", json={"code": "value = 1"})
    missing = client.get("/api/reviews/not-found/report")

    assert empty.status_code == 400
    assert empty.json()["error"] == "empty_code"
    assert too_large.status_code == 413
    assert too_large.json()["error"] == "code_too_large"
    assert unknown.status_code == 422
    assert unknown.json()["error"] == "language_unknown"
    assert missing.status_code == 404
    assert missing.json()["error"] == "review_not_found"


def test_sensitive_input_keeps_static_result_and_blocks_ai(tmp_path):
    client = build_client(tmp_path)
    marker = "pass" + "word"
    source = f"""\
#include <cstddef>
// {marker} = "classroom-example-value"
int main() {{
    int* value = NULL;
    return value == NULL;
}}
"""

    response = client.post(
        "/api/reviews",
        json={"code": source, "request_ai": True},
    )

    assert response.status_code == 201
    assert response.json()["ai_status"] == "blocked_sensitive_input"
    assert response.json()["static_issues"]

    safe_source_sensitive_goal = client.post(
        "/api/reviews",
        json={
            "code": CPP_SOURCE,
            "goal": f'{marker} = "classroom-example-value"',
            "request_ai": True,
        },
    )
    assert safe_source_sensitive_goal.status_code == 201
    assert (
        safe_source_sensitive_goal.json()["ai_status"]
        == "blocked_sensitive_input"
    )


def test_web_entrypoint_is_available_without_language_selector(tmp_path):
    client = build_client(tmp_path)

    response = client.get("/")
    favicon = client.get("/favicon.ico")

    assert response.status_code == 200
    assert favicon.status_code == 204
    assert "code_coach" in response.text
    assert 'id="source-code"' in response.text
    assert 'name="language"' not in response.text

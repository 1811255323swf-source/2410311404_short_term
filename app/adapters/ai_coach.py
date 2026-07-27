from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Sequence
from typing import Any, Protocol

from app.domain.contracts import AiResult, StaticIssue, validate_ai_coaching


class AiProvider(Protocol):
    def generate(self, request: dict[str, Any], timeout_seconds: float) -> Any:
        ...


class MockAiProvider:
    """Deterministic teaching output used by automated tests and offline demos."""

    def generate(self, request: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
        language = request["language"]
        issues = request["issues"]
        rule_ids = [issue["rule_id"] for issue in issues]
        if language == "cpp":
            concept = "C++ nullptr 对应 Python None，但两者都有各自的类型语义。"
            exercise = "把一个 C++ 空指针判断改写成 Python 的 is None 判断。"
        else:
            concept = "Python 的动态对象模型可与 C++ 的显式类型和生命周期对照学习。"
            exercise = "为同一小函数分别写 Python 与 C++ 版本并标出类型差异。"

        if rule_ids:
            repair_order = [f"先处理 {rule_id}" for rule_id in rule_ids[:3]]
            summary = f"检测到 {len(rule_ids)} 个确定性问题，按严重程度逐项修复。"
        else:
            repair_order = ["保持当前正确结构，再补一个边界测试"]
            summary = "未发现已知静态问题，可以继续通过练习巩固概念。"

        return {
            "summary": summary,
            "repair_order": repair_order,
            "concept_links": [concept],
            "exercises": [exercise],
        }


class OllamaProvider:
    """Optional local provider. It never participates in deterministic tests."""

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:11435/api/chat",
        model: str = "qwen3.5:4b",
    ):
        self.endpoint = endpoint
        self.model = model

    def generate(self, request: dict[str, Any], timeout_seconds: float) -> Any:
        prompt = {
            "language": request["language"],
            "goal": request.get("goal", ""),
            "static_issues": request["issues"],
            "contract_errors": request.get("contract_errors", []),
            "required_output": {
                "summary": "non-empty string",
                "repair_order": ["non-empty string"],
                "concept_links": ["non-empty string"],
                "exercises": ["non-empty string"],
            },
        }
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "format": "json",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a code learning coach. Static issues are authoritative. "
                        "Return only the required JSON object and never change the score."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt, ensure_ascii=False),
                },
            ],
            "options": {"temperature": 0, "num_predict": 512},
        }
        raw_request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(raw_request, timeout=timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as error:
            if isinstance(error.reason, TimeoutError):
                raise TimeoutError("local model timed out") from error
            raise OSError("local model is unavailable") from error
        content = body.get("message", {}).get("content", "")
        if not content:
            return None
        if isinstance(content, dict):
            return content
        text = content.strip()
        if text.startswith("```") and text.endswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].lstrip()
        return json.loads(text)


class AiCoach:
    def __init__(
        self,
        provider: AiProvider,
        *,
        total_budget_seconds: float = 35.0,
        attempt_timeout_seconds: float = 20.0,
    ):
        self.provider = provider
        self.total_budget_seconds = total_budget_seconds
        self.attempt_timeout_seconds = attempt_timeout_seconds

    def coach(
        self,
        language: str,
        issues: Sequence[StaticIssue],
        goal: str,
    ) -> AiResult:
        started = time.monotonic()
        contract_errors: list[str] = []
        issue_payload = [issue.to_dict() for issue in issues]
        last_error = "provider_error"

        for attempt in range(1, 3):
            remaining = self.total_budget_seconds - (time.monotonic() - started)
            if remaining <= 0:
                return AiResult(
                    status="unavailable",
                    coaching=None,
                    error_type="timeout",
                    attempts=attempt - 1,
                )
            request = {
                "language": language,
                "issues": issue_payload,
                "goal": goal,
                "contract_errors": contract_errors,
            }
            try:
                payload = self.provider.generate(
                    request,
                    timeout_seconds=min(self.attempt_timeout_seconds, remaining),
                )
                if payload is None:
                    last_error = "empty_response"
                    contract_errors = ["provider returned an empty response"]
                    continue
                if isinstance(payload, str):
                    payload = json.loads(payload)
            except TimeoutError:
                last_error = "timeout"
                continue
            except OSError:
                last_error = "offline"
                continue
            except (json.JSONDecodeError, TypeError, ValueError):
                last_error = "invalid_json"
                contract_errors = ["provider response was not valid JSON"]
                continue

            valid, contract_errors = validate_ai_coaching(payload)
            if valid:
                return AiResult(
                    status="available",
                    coaching=payload,
                    attempts=attempt,
                )
            last_error = "contract_violation"

        return AiResult(
            status="unavailable",
            coaching=None,
            error_type=last_error,
            attempts=2,
        )

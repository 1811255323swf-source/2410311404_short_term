const examples = {
  cpp: `#include <cstddef>
#include <iostream>

int main() {
    int* value = NULL;
    std::cout << (value == NULL);
    return 0;
}`,
  python: `from pathlib import Path

def collect(item, bucket=[]):
    try:
        bucket.append(item)
    except:
        return []
    return bucket

if __name__ == "__main__":
    print(collect(Path(".")))`,
};

const sourceCode = document.querySelector("#source-code");
const revisionCode = document.querySelector("#revision-code");
const goal = document.querySelector("#learning-goal");
const requestAi = document.querySelector("#request-ai");
const analyzeButton = document.querySelector("#analyze-button");
const compareButton = document.querySelector("#compare-button");
const statusMessage = document.querySelector("#status-message");
const reportLink = document.querySelector("#report-link");
const revisionPanel = document.querySelector("#revision-panel");
const comparisonOutput = document.querySelector("#comparison-output");

let currentReviewId = null;

document.querySelectorAll("[data-example]").forEach((button) => {
  button.addEventListener("click", () => {
    sourceCode.value = examples[button.dataset.example];
    statusMessage.textContent = "已载入示例，可以直接评审。";
  });
});

function setBusy(button, busy, busyText, normalText) {
  button.disabled = busy;
  button.textContent = busy ? busyText : normalText;
}

function renderIssues(issues) {
  const list = document.querySelector("#issue-list");
  list.replaceChildren();
  if (!issues.length) {
    const item = document.createElement("li");
    item.className = "empty-state";
    item.textContent = "未发现已知静态问题。";
    list.append(item);
    return;
  }
  issues.forEach((issue) => {
    const item = document.createElement("li");
    item.className = `issue issue-${issue.severity}`;

    const header = document.createElement("div");
    const badge = document.createElement("span");
    badge.className = "issue-badge";
    badge.textContent = issue.severity;
    const rule = document.createElement("strong");
    rule.textContent = issue.rule_id;
    const line = document.createElement("span");
    line.textContent = `line ${issue.line}`;
    header.append(badge, rule, line);

    const message = document.createElement("p");
    message.textContent = issue.message;
    item.append(header, message);
    list.append(item);
  });
}

function addListSection(container, title, values) {
  const heading = document.createElement("h4");
  heading.textContent = title;
  const list = document.createElement("ul");
  values.forEach((value) => {
    const item = document.createElement("li");
    item.textContent = value;
    list.append(item);
  });
  container.append(heading, list);
}

function renderCoaching(payload, status) {
  const output = document.querySelector("#coaching-output");
  output.replaceChildren();
  output.className = "coaching-output";
  if (!payload) {
    output.classList.add("empty-state");
    const messages = {
      not_requested: "本次未请求 AI，静态结果仍完整可用。",
      blocked_sensitive_input: "输入疑似包含敏感信息，已阻止模型调用。",
      unavailable: "模型离线、超时或合同错误，已降级为静态结果。",
    };
    output.textContent = messages[status] || "AI 教学解释当前不可用。";
    return;
  }

  const summary = document.createElement("p");
  summary.className = "coaching-summary";
  summary.textContent = payload.summary;
  output.append(summary);
  addListSection(output, "修复顺序", payload.repair_order);
  addListSection(output, "概念连接", payload.concept_links);
  addListSection(output, "练习", payload.exercises);
}

function renderReview(payload) {
  document.querySelector("#metric-language").textContent = payload.detected_language;
  document.querySelector("#metric-confidence").textContent =
    `${Math.round(payload.confidence * 100)}%`;
  document.querySelector("#metric-score").textContent = payload.score;
  document.querySelector("#metric-ai").textContent = payload.ai_status;
  renderIssues(payload.static_issues);
  renderCoaching(payload.ai_coaching, payload.ai_status);

  currentReviewId = payload.review_id;
  revisionPanel.classList.remove("hidden");
  revisionCode.value = sourceCode.value;
  reportLink.href = `/api/reviews/${currentReviewId}/report`;
  reportLink.classList.remove("disabled");
  reportLink.removeAttribute("aria-disabled");
}

async function readPayload(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return {error: "unexpected_response", message: await response.text()};
}

analyzeButton.addEventListener("click", async () => {
  statusMessage.textContent = "";
  comparisonOutput.textContent = "";
  setBusy(analyzeButton, true, "分析中…", "开始评审");
  try {
    const response = await fetch("/api/reviews", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        code: sourceCode.value,
        goal: goal.value,
        request_ai: requestAi.checked,
      }),
    });
    const payload = await readPayload(response);
    if (!response.ok) {
      throw new Error(`${payload.error}: ${payload.message}`);
    }
    renderReview(payload);
    statusMessage.textContent = `评审完成 · ${payload.review_id}`;
  } catch (error) {
    statusMessage.textContent = error.message;
  } finally {
    setBusy(analyzeButton, false, "分析中…", "开始评审");
  }
});

compareButton.addEventListener("click", async () => {
  if (!currentReviewId) {
    comparisonOutput.textContent = "请先完成一次评审。";
    return;
  }
  setBusy(compareButton, true, "比较中…", "比较修改");
  try {
    const response = await fetch(`/api/reviews/${currentReviewId}/compare`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({code: revisionCode.value}),
    });
    const payload = await readPayload(response);
    if (!response.ok) {
      throw new Error(`${payload.error}: ${payload.message}`);
    }
    comparisonOutput.textContent =
      `分数变化 ${payload.score_delta >= 0 ? "+" : ""}${payload.score_delta} · ` +
      `已解决 ${payload.resolved_issue_ids.length} · ` +
      `仍存在 ${payload.remaining_issue_ids.length} · ` +
      `新增 ${payload.new_issue_ids.length}`;
  } catch (error) {
    comparisonOutput.textContent = error.message;
  } finally {
    setBusy(compareButton, false, "比较中…", "比较修改");
  }
});

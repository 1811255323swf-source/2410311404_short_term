# W3 Independent Implementation Review

- Delivery ID: `2410311404-code-coach`
- Date: 2026-07-24
- Reviewer input: 本地 `qwen3.5:4b` 脱敏摘要复审 + pytest、文件差异和合同一致性审计
- Request: `spike/tests/w3_implementation_review_request.json`
- Model decision: `MODIFIED_PASS`

## Model Findings

复审提出五类问题：g++ 编译错误提示、敏感规则误报处理、语法探针进程隔离、Ollama 离线/超时，以及模型请求不得包含完整源码。

## Accepted Changes

1. g++ syntax-only 在临时目录、参数数组和 3 秒墙钟超时基础上，增加 `prlimit`：512 MiB 地址空间、4 秒 CPU、1 MiB 文件输出和 64 个文件描述符。
2. 增加离线 provider 和超时 provider 的确定性测试，均验证最多两次尝试后 `ai_status=unavailable`。
3. AI provider 请求仅保留语言、学习目标、结构化问题摘要和合同错误，不传递完整源码；代码和学习目标命中敏感模式时均阻断模型调用。
4. DESIGN 与 ADR-002 同步记录模型数据边界和语法探针资源限制，避免实现与设计漂移。

## Already Satisfied or Rejected

- 编译错误已经标准化为 `CPP-SYNTAX` 并在网页静态问题区显示，因此不新增另一套“降级提示”状态。
- 敏感规则坚持安全优先，不提供一键绕过；误报时用户可在本地移除疑似凭据后重试，静态结果仍保留。
- 持续会话历史不属于 PRD/SPEC；compare 只表示一次修订状态。
- 真实 Ollama 不进入自动压力测试，以免随机输出破坏 Gate；W1 已保留真实模型能力证据，W3 自动 Gate 使用 mock、离线和超时 provider。

## Deterministic Evidence

- `.venv/bin/python -m pytest tests -q` -> W3 测试目录 `48 passed`。
- `.venv/bin/python -m pytest -q` -> 连同 W1-W2 回归共 `51 passed`。
- `bash scripts/check.sh` -> `DELIVERY_CHECK=PASS`。
- `git diff --check` -> 无输出。
- Red/green record: `evidence/2410311404-code-coach-w3-red-green.md`。

## Decision

`MODIFIED_PASS`：模型数据边界、资源隔离、工具异常和模型失败测试已补齐，W3 实现、等价审查与测试记录相互一致，允许进入下一阶段。

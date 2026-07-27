# code_coach W3 Sprint Cards

- Delivery ID: `2410311404-code-coach`
- Stage: W3
- Source: Gate 2 `MODIFIED_PASS`
- Rule: 每张卡先运行目标测试得到红灯，再做最小实现；真实模型不进入自动 Gate。

## TC-2410311404-01 - 领域合同、评分与比较

- Status: completed
- User-visible increment: 用户能得到稳定分数，并能区分已解决、仍存在和新增问题。
- Scope: `app/domain/contracts.py`、`scoring.py`、`comparison.py`。
- Acceptance:
  - 输入 error、warning、info 各一条 -> 分数为 79。
  - 比较前后问题 -> 返回 resolved、remaining、new 和 score_delta。
- Red test: `tests/unit/test_scoring_comparison.py` 在生产包缺失时失败。
- Test command: `.venv/bin/python -m pytest tests/unit/test_scoring_comparison.py -q`
- Effort: 45 分钟。
- Depends on: Gate 2。
- Risk: 问题身份随行号漂移；使用规则号、归一化消息和上下文哈希，不把行号作为唯一身份。

## TC-2410311404-02 - 安全双语检测

- Status: completed
- User-visible increment: 完整 C++/Python 自动识别，模糊片段返回 unknown。
- Scope: `app/detectors/language_detector.py`、`app/security/process_limits.py`。
- Acceptance:
  - 完整 C++/Python -> 语言正确、可信度至少 0.80、至少两条证据。
  - `value = 1` -> unknown。
  - 强 C++ 特征但语法错误 -> 仍路由 cpp；探针永不执行程序。
  - g++ 缺失、超时或两类特征冲突 -> 返回可观察探针状态并遵守强候选或 unknown 决策。
- Red test: `tests/unit/test_language_detector.py` 在 Detector 缺失时失败。
- Test command: `.venv/bin/python -m pytest tests/unit/test_language_detector.py -q`
- Effort: 90 分钟。
- Depends on: TC-01。
- Risk: syntax-only 被误当执行；固定参数数组、临时目录、3 秒超时且不生成可执行文件。

## TC-2410311404-03 - C++ 与 Python 最小分析器

- Status: completed
- User-visible increment: 用户能看到归一化语法错误和两种语言的教学规则。
- Scope: `app/analyzers/cpp_analyzer.py`、`python_analyzer.py`。
- Acceptance:
  - C++ NULL -> `CPP-NULLPTR`；错误语法 -> `CPP-SYNTAX` 且不泄露临时路径。
  - Python 可变默认参数和裸 except -> 对应规则；错误语法 -> `PY-SYNTAX`。
- Red test: `tests/unit/test_analyzers.py` 在 Analyzer 缺失时失败。
- Test command: `.venv/bin/python -m pytest tests/unit/test_analyzers.py -q`
- Effort: 90 分钟。
- Depends on: TC-01、TC-02。
- Risk: 编译器文本随版本变化；只解析稳定的行、严重级别和消息部分。

## TC-2410311404-04 - AI 合同、安全阻断与降级

- Status: completed
- User-visible increment: AI 输出稳定为四字段，失败时仍保留静态结果。
- Scope: `app/adapters/ai_coach.py`、`app/security/input_guard.py`。
- Acceptance:
  - 首次合同错误 -> 最多修复一次后成功。
  - 两次错误 -> unavailable；敏感标记 -> 不向模型发送并不回显值。
  - 模型请求 -> 只含语言、学习目标和结构化问题摘要，不含完整源码。
  - mock 相同输入 -> 相同输出。
- Red test: `tests/unit/test_ai_security.py` 在 Adapter 与 Guard 缺失时失败。
- Test command: `.venv/bin/python -m pytest tests/unit/test_ai_security.py -q`
- Effort: 90 分钟。
- Depends on: TC-01。
- Risk: 真实模型不稳定；自动测试只使用 mock，Ollama 仅作脱敏人工证据。

## TC-2410311404-05 - SQLite 与评审服务

- Status: completed
- User-visible increment: 一次评审可以保存摘要、提交修订并导出学习报告。
- Scope: `app/storage/repository.py`、`app/application/review_service.py`、`app/reporting/markdown_reporter.py`。
- Acceptance:
  - 创建评审 -> 可按 ID 读取，但数据库字节中没有完整源代码。
  - 提交 nullptr 修订 -> NULL 问题被标记为 resolved，分数上升。
  - 导出 -> UTF-8 Markdown 且不包含原始代码。
- Red test: `tests/integration/test_storage_service.py` 在服务缺失时失败。
- Test command: `.venv/bin/python -m pytest tests/integration/test_storage_service.py -q`
- Effort: 90 分钟。
- Depends on: TC-02、TC-03、TC-04。
- Risk: 源码被意外持久化；表结构只保存代码 SHA-256、评审元数据、问题快照、分数、AI 状态、教学结果和修订差异，不设置源码列。

## TC-2410311404-06 - FastAPI 合同

- Status: completed
- User-visible increment: 用户可以通过 review、compare、report 三个 API 完成闭环。
- Scope: `app/main.py`、API 请求模型与错误映射。
- Acceptance:
  - review -> 201；compare/report -> 200。
  - 空输入/超长/unknown/不存在 -> 400/413/422/404。
  - 敏感输入 -> 201 且 `ai_status=blocked_sensitive_input`。
- Red test: `tests/integration/test_api.py` 在 FastAPI 应用缺失时失败。
- Test command: `.venv/bin/python -m pytest tests/integration/test_api.py -q`
- Effort: 90 分钟。
- Depends on: TC-05。
- Risk: 框架默认 422 覆盖业务错误；由 DomainError 统一映射设计状态码。

## TC-2410311404-07 - 本地网页闭环

- Status: completed
- User-visible increment: 用户能粘贴代码、查看检测/问题/AI 教学、比较修改并下载报告。
- Scope: `app/web/index.html`、`app/web/static/app.js`、`styles.css`。
- Acceptance:
  - GET `/` -> 200 且存在源码输入框。
  - 页面没有手动语言选择器；空值、unknown 和 AI 降级均有可见提示。
  - 检查前端请求与显示逻辑 -> 使用 review、compare、report 合同，并读取结构化 error 与 ai_status。
- Red test: API 集成测试中的网页入口断言先失败。
- Test command: `.venv/bin/python -m pytest tests/integration/test_api.py -q`；`rg -n 'payload.error|ai_status' app/web/static/app.js`。
- Effort: 90 分钟。
- Depends on: TC-06。
- Risk: 前端错误状态与后端不一致；统一读取结构化 error 和 ai_status。

## TC-2410311404-08 - 本地 CI 与等价审查

- Status: completed
- User-visible increment: 评审者可以用一条命令复测全部功能和安全边界。
- Scope: `scripts/check.sh`、`scripts/security_scan.sh`、分类语料、W3 证据与冲刺记录。
- Acceptance:
  - `scripts/check.sh` -> 所有测试、语法、W1-W2 回归、空白和敏感模式扫描通过。
  - 受控语料达到 PRD 成功指标。
  - 独立复审问题有采纳/拒绝结论。
- Red test: W3 初始全量 pytest 出现 6 个生产包缺失错误。
- Test command: `bash scripts/check.sh`
- Effort: 60 分钟。
- Depends on: TC-01 至 TC-07。
- Risk: 红绿过程可能缺少连续证据；使用真实失败输出、通过输出和文件差异交叉验证。

## Implementation Order

`TC-01 -> TC-02 -> TC-03 -> TC-04 -> TC-05 -> TC-06 -> TC-07 -> TC-08`

## W3 Risk Summary

| Risk | Impact | Mitigation |
|---|---|---|
| g++ 不可用或超时 | C++ 探针降级 | 工具状态进入证据，强特征可限可信度路由 |
| 语法错误被误判 unknown | 用户拿不到诊断 | 强候选与语法正确性分离 |
| 模型离线或合同错误 | AI 教学缺失 | 两次上限、35 秒预算、静态结果降级 |
| 原始代码落库 | 隐私边界破坏 | schema 无源码列，集成测试搜索数据库字节 |
| UI 与 API 状态漂移 | 用户无法理解错误 | 统一结构化 error 与 ai_status，并用 API 集成测试和前端合同检查复核 |
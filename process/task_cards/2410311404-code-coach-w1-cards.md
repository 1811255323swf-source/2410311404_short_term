# code_coach W1 Task Cards

- Delivery ID: `2410311404-code-coach`
- Stage: W1 Gate 1
- Date: 2026-07-22

## CC-001 定义 W1 范围与规格

- Role: `pm-2410311404`
- Status: completed
- Depends on: 无
- Traceability: `docs/PRD.md`、`docs/SPEC.md`
- Context: Gate 1 需要明确目标用户、核心场景、成功指标、非目标和可测试验收标准。
- User Value: 学生和评审者能够准确理解 W1 原型做什么。
- Scope: 4 个用户故事、验收标准、错误路径、AI 边界和文件追踪。
- Acceptance:
  - 运行 W1 检查 -> 识别 4 个用户故事且每个至少包含 2 条验收标准。
  - 核对文件追踪 -> 每个实现或证据路径都能在仓库中找到。
- Evidence: `docs/PRD.md`、`docs/SPEC.md`
- Test Command: `bash scripts/check_w1.sh`
- Out of scope: 网页、网络 API、数据库和完整静态分析。
- Risk: 规格超出已有纵切面会造成材料与实现不一致。
- Estimated Effort: 90 分钟。

## CC-002 实现语言检测最小纵切面

- Role: `dev-2410311404`
- Status: completed
- Depends on: CC-001
- Traceability: SPEC US-1、US-2
- Context: 代码文件需要在不执行内容的前提下分类。
- User Value: 学生能看到语言、可信度、得分和判断依据。
- Scope: C++17 特征评分、三类样例、JSON 输出和自动断言。
- Acceptance:
  - 运行语言探针 -> C++ 和 Python 样例正确分类，可信度不低于 0.80。
  - 检查模糊样例 -> 返回 `unknown`。
- Evidence: `evidence/2410311404-code-coach-w1-detector-spike.md`
- Test Command: `bash spike/tests/run_spike.sh`
- Out of scope: 执行输入代码、完整编译诊断和 Python AST 诊断。
- Risk: 三个样例只能证明路径可行，不能代表所有代码。
- Estimated Effort: 90 分钟。

## CC-003 完成 AI 探针与 Gate 1

- Role: `qa-2410311404`
- Status: completed
- Depends on: CC-001、CC-002
- Traceability: SPEC US-3、US-4
- Context: AI 原生方向需要证明教学解释能力，同时保留结构校验失败。
- User Value: 学生能获得与确定性诊断相关的跨语言解释，评审者能复现结论。
- Scope: 脱敏 AI 请求、响应校验、两轮 Loop Engineering、统一检查和 Gate 1。
- Acceptance:
  - 运行 AI 探针 -> 输出解释能力与结构合同状态。
  - 运行 W1 统一检查 -> 输出 `W1_GATE_CHECK=PASS`。
- Evidence: `evidence/2410311404-code-coach-w1-ai-spike.md`、`process/gate/2410311404-code-coach-gate-1-prd-spec.md`
- Test Command: `bash scripts/check_w1.sh`
- Out of scope: 将单次模型输出作为自动 Gate 结论。
- Risk: 本地模型可能离线或返回不完整字段。
- Estimated Effort: 90 分钟。

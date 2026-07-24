# Gate 2 Design Audit - code_coach

- Reviewer: `reviewer-2410311404`
- Date: 2026-07-23
- Delivery ID: `2410311404-code-coach`
- Key modules: InputGuard、LanguageDetector、StaticAnalyzer、AiCoach、ReviewService、ReviewRepository、Reporter
- ADR checked: `docs/adr/ADR-001-deterministic-core-ai-adapter.md`、`docs/adr/ADR-002-hybrid-safe-language-detection.md`
- Highest-risk dependency: 本地 g++ 版本影响安全语法探针；真实模型可能离线、超时或返回不符合合同的内容
- Test strategy summary: 纯函数与合同使用确定性输入，命令行纵切面使用三类样例，集成测试使用 mock AI，真实模型只保留脱敏能力证据
- Decision after audit: 修改后通过（`MODIFIED_PASS`）

## SPEC Traceability

`docs/DESIGN.md` 追踪 SPEC 的 10 条验收标准。语言识别、unknown 决策、AI 教学输出校验和 Gate 复现均有对应责任与当前证据。

## Module and Dependency Audit

- `ReviewService` 是唯一编排入口。
- InputGuard、LanguageDetector、StaticAnalyzer 和 AI 合同校验保持确定性。
- AiCoach 不能修改语言结果、确定性问题或分数。
- Reporter 只读取已完成结果，不重新运行分析或模型。

## ADR Audit

- ADR-001 比较 AI-first、完全确定性和分层混合，选择确定性核心加可降级 AI。
- ADR-002 比较纯特征、执行代码、在线服务和本地安全语法探针，选择特征评分与本地探针组合。
- 两条 ADR 均包含真实候选方案、拒绝理由、影响和回滚。

## AI Boundary and Budget

- 模型只接收脱敏诊断摘要。
- 自动测试使用固定对象，不依赖真实模型。
- 合同错误最多修复重试一次。
- 单次上限 20 秒，两次尝试总预算 35 秒。
- 空响应、非法 JSON、缺字段、字段类型错误、离线或超时均降级，并保留确定性结果。

## Test-First Evidence

- Red commit: `2c85613`，合同测试因缺少实现模块失败。
- Green commit: `cf9c90a`，加入最小合同校验后 3 个测试通过。
- Evidence: `evidence/2410311404-code-coach-w2-contract-red-green.md`

## Loop Engineering Audit

### Loop-1 Baseline Design

- Hypothesis: Gate 1 的语言检测和 AI 能力边界可以映射为单向依赖模块与稳定合同。
- Action: 编写 DESIGN、数据结构、状态变化、测试策略和两条 ADR。
- Evidence: `docs/DESIGN.md`、`docs/adr/`、`scripts/check_w2.sh`
- Result: 模块职责、依赖方向和失败状态可以由文档定位。
- Decision: 基线结构可行，需进一步检查接口宽度和 AI 合同失败路径。
- Next loop: 使用脱敏设计摘要进行独立复审，并用确定性脚本复核。

### Loop-2 Independent Review

- Hypothesis: 独立评审能发现模块绕行、阈值和预算保护缺口。
- Action: 运行脱敏设计评审，采纳可由 SPEC 和测试验证的修改。
- Evidence: `evidence/2410311404-code-coach-w2-design-review.md`、DESIGN 与 ADR 文件差异、`bash scripts/check_w2.sh`
- Result: 明确唯一编排入口、候选阈值、语法失败语义、一次修复重试和 35 秒总预算。
- Decision: 修改后通过。
- Next loop: 后续实现从失败测试开始，严格遵守当前模块和合同边界。

## Final Check

`bash scripts/check_w2.sh` 验证 W1 基线、DESIGN 结构、10 条验收追踪、2 条 ADR、3 个 AI 合同测试、Gate 2 证据、模板残留和凭据模式。

W2_GATE_DECISION=MODIFIED_PASS

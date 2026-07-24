# Gate 1 PRD/SPEC Review - code_coach

- Reviewer: `reviewer-2410311404`
- Date: 2026-07-22
- Project topic: `code_coach`
- Delivery ID: `2410311404-code-coach`
- Main users: 已学习 C++、正在过渡到 Python 的高校学生
- Accepted scope: C++/Python/unknown 语言检测、稳定 JSON、三类样例、脱敏 AI 能力探针和 W1 自动检查
- Removed scope: 执行输入代码、其他语言、网页、网络 API、数据库、完整静态分析和自动修复
- Most important risk: 短代码和混合语法的分类边界，以及本地模型结构化输出不稳定
- AI capability spike: 本地模型能根据 `CPP-NULLPTR` 脱敏摘要生成相关教学解释
- Minimum vertical slice: 代码文件输入 -> C++17 检测器 -> JSON 输出 -> 自动断言
- Spike evidence: `evidence/2410311404-code-coach-w1-detector-spike.md`、`evidence/2410311404-code-coach-w1-ai-spike.md`

## Reviewer Restatement

`code_coach` W1 原型面向从 C++ 过渡到 Python 的学生。当前仓库能够读取代码文件，识别 C++、Python 或证据不足的输入，并输出可信度、两类得分和判断依据；本地 AI 探针用于验证脱敏教学解释，统一脚本用于复现 Gate 1 证据。原型不执行输入代码，也不提供网页或网络服务。

## Loop Engineering Audit

### Loop-1 PRD/SPEC Review

- Hypothesis: 如果 W1 范围自洽，PRD 和 SPEC 中的用户故事、验收标准与文件追踪都应由当前仓库验证。
- Action: 以语言检测纵切面和 AI 探针为边界编写 PRD、SPEC 与 3 张任务卡；逐项核对文件追踪。
- Evidence command or artifact: `docs/PRD.md`、`docs/SPEC.md`、`process/task_cards/2410311404-code-coach-w1-cards.md`、`bash scripts/check_w1.sh`
- Evidence result: 形成 4 个用户故事和 10 条可测试验收标准；所有实现、样例、脚本和证据路径均存在。
- Decision: 范围可在 W1 内完成，语言检测作为最小纵切面。
- Next loop: 用受控样例和真实模型输出挑战检测与 AI 结构边界。

### Loop-2 Capability Review

- Hypothesis: 简单特征会出现跨语言碰撞；模型可以生成相关解释，但不一定完整遵守四字段合同。
- Action: 先运行三类样例，再为交叉得分增加失败断言并修正规则；随后使用脱敏诊断运行本地 AI 探针。
- Evidence command or artifact: `bash spike/tests/run_spike.sh`、`python3 spike/tests/run_ai_spike.py`、两份 W1 spike evidence
- Evidence result: C++ 和 Python 样例均正确分类且交叉得分为 0，模糊样例返回 `unknown`；AI 教学摘要通过，四字段结构校验部分通过。
- Decision: 修改后通过。最小纵切面与 AI 解释能力已有证据，样例数量和模型结构稳定性仍是明确限制。
- Next loop: 增加边界样例，并为 AI 响应增加更严格的本地校验与降级处理。

## Gate Decision

`MODIFIED_PASS`

PRD 能说明目标用户、核心场景、成功指标和非目标；SPEC 包含 4 个用户故事及可测试验收标准；最小纵切面、AI 能力探针和两轮 Loop Engineering 均有仓库内证据。现有材料满足 W1 Gate 1 范围。

## Stage Boundary

W1 交付仅由当前仓库中的 PRD、SPEC、3 张任务卡、语言检测实现、3 个样例、AI 请求与校验脚本、2 份探针证据、角色说明、统一检查脚本和本 Gate 文件组成。

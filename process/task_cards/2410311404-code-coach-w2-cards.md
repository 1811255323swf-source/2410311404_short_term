# code_coach W2 Task Cards

- Delivery ID: `2410311404-code-coach`
- Stage: W2 Gate 2
- Date: 2026-07-23

## CC-W2-001 DESIGN 与 ADR

- Role: `architect-2410311404`
- Status: completed
- Depends on: Gate 1 `MODIFIED_PASS`
- Traceability: SPEC 的 10 条验收标准
- Context: Gate 2 需要固定模块职责、依赖方向、状态、失败路径和架构取舍。
- User Value: 评审者能理解系统如何拆分及为何采用当前方案。
- Scope: DESIGN、两条 ADR、数据结构、状态变化、AI 边界和测试策略。
- Acceptance:
  - 检查 DESIGN -> 10 条验收标准均有设计责任和证据入口。
  - 检查两条 ADR -> 每条均含候选、拒绝理由、决定、影响和回滚。
- Evidence: `docs/DESIGN.md`、`docs/adr/`
- Test Command: `bash scripts/check_w2.sh`
- Out of scope: W2 不新增完整应用实现。
- Risk: 设计名称可能被误读为已存在文件。
- Estimated Effort: 90 分钟。

## CC-W2-002 AI 合同红绿骨架

- Role: `dev-2410311404`
- Status: completed
- Depends on: CC-W2-001
- Traceability: SPEC AC-3.1 至 AC-3.3
- Context: 真实模型可能缺字段或返回错误类型，自动 Gate 需要离线确定性合同。
- User Value: 模型结构错误不会被当成完整教学结果。
- Scope: 四字段校验器、合法对象、缺字段和错误类型测试。
- Acceptance:
  - 运行合同测试 -> 3 个测试全部通过。
  - 提交非法对象 -> 返回稳定错误列表。
- Evidence: `evidence/2410311404-code-coach-w2-contract-red-green.md`
- Test Command: `python3 -m unittest discover -s spike/tests -p 'test_ai_contract.py' -v`
- Out of scope: 真实模型网络客户端。
- Risk: 合同通过不代表内容质量正确。
- Estimated Effort: 60 分钟。

## CC-W2-003 设计复审与 Gate 2

- Role: `qa-2410311404`
- Status: completed
- Depends on: CC-W2-001、CC-W2-002
- Traceability: Gate 2 通过标准
- Context: DESIGN、ADR、AI 边界和测试先行证据需要统一审计。
- User Value: 评审者能够复现 W2 范围和风险结论。
- Scope: 脱敏复审、确定性检查、两轮 Loop Engineering 和 Gate 2。
- Acceptance:
  - 运行 W2 检查 -> 输出 `W2_GATE_CHECK=PASS`。
  - 检查 Gate 2 -> 模块、ADR、最高风险、测试策略和决定均可定位。
- Evidence: `evidence/2410311404-code-coach-w2-design-review.md`、`process/gate/2410311404-code-coach-gate-2-design.md`
- Test Command: `bash scripts/check_w2.sh`
- Out of scope: 将模型意见直接作为 Gate 结论。
- Risk: 评审输出可能不符合结构合同。
- Estimated Effort: 60 分钟。

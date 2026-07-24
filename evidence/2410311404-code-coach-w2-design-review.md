# W2 Independent Design Review Evidence

- Delivery ID: `2410311404-code-coach`
- Date: 2026-07-23
- Reviewer input: 本地 `qwen3.5:4b` 脱敏评审与确定性文件检查
- Request artifact: `spike/tests/w2_design_review_request.json`
- Reviewed scope: SPEC 追踪、模块依赖、状态变化、AI 失败路径、预算保护和测试策略

## Model Review Runs

运行命令：

```bash
curl --max-time 120 -sS \
  -H 'Content-Type: application/json' \
  --data-binary @spike/tests/w2_design_review_request.json \
  http://127.0.0.1:11435/api/chat
```

第一次运行在预测长度上限处结束，未形成完整结论。缩短请求后第二次运行完成并给出 `MODIFIED_PASS`。模型没有严格遵循请求中的 JSON Schema，因此意见只作为设计问题输入，不作为自动检查结果。

## Accepted Changes

1. 明确 `ReviewService` 是唯一编排入口，其他模块不得相互绕行调用。
2. 固定语言候选阈值：最高分至少为 5，分差至少为 3。
3. 语法探针失败不能单独否定强候选，因为待诊断代码可能含语法错误。
4. 增加 AI 合同失败、一次修复重试、35 秒总预算和降级状态。
5. 区分纯函数测试、命令行纵切面、集成测试和真实模型证据。

## Deterministic Review

`bash scripts/check_w2.sh` 检查以下内容：

- SPEC 的 10 条验收标准均被 DESIGN 追踪；
- DESIGN 包含模块地图、依赖、数据结构、状态、AI 边界和测试策略；
- 两条 ADR 均包含候选、拒绝理由、决定、影响和回滚；
- AI 合同的 3 个离线测试通过；
- Gate 2、红绿证据和评审记录均可定位。

## Decision

`MODIFIED_PASS`

W2_DESIGN_REVIEW=PASS

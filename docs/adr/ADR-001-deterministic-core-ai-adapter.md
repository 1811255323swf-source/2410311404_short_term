# ADR-001 - Deterministic Core with a Degradable AI Adapter

## Status

Accepted

## Context

`code_coach` 必须同时提供可复现的静态事实与 AI 教学解释。W1 证明本地模型可以生成相关解释，但严格结构输出可能缺字段、类型错误或被长度上限截断。若让模型直接决定问题和评分，自动测试与用户结果会随模型波动。

## Alternatives

1. AI-first：把语言识别、问题发现、评分和解释一次性交给模型。
2. 确定性纯核心：完全移除 AI，只保留编译器、AST 和规则。
3. Layered hybrid：确定性核心产生事实与评分，AI 适配器只解释这些事实，并允许降级。

## Rejected Options

- 拒绝 AI-first：结果不可复现，模型离线时主链路整体失效，也无法证明评分来自固定规则。
- 拒绝确定性纯核心：它无法满足项目的 AI 原生教学价值，也不能提供跨语言概念映射和练习。

## Decision

采用 Layered hybrid。`domain`、语言检测和分析器产生不可被 AI 修改的 `StaticIssue` 与 `score`；`AiCoach` 只接收脱敏诊断摘要，通过可替换适配器生成 `AiCoaching`。应用层使用 `validate_ai_coaching` 校验，最多进行一次合同修复重试，之后降级为 `unavailable`。

## Consequences

- 好处：静态结果可重复测试；模型离线或结构错误时仍有用户价值；mock 可以覆盖全部自动测试。
- 代价：需要维护确定性规则、AI 合同和两类证据，响应结构也更明确。
- 测试要求：证明 AI 不能改变静态问题与分数；覆盖成功、超时、空响应、非法 JSON、字段错误、重试成功和重试失败。
- 预算要求：最多两次尝试、总预算 35 秒，自动测试不进行在线调用。

## Rollback

如果后续证据显示本地模型仍无法稳定通过合同，保留适配器接口与 mock，运行结果降级为静态结果加模板化跨语言提示；不得回滚为 AI-first。恢复真实模型前必须新增可复现的合同通过证据。

# code_coach DESIGN

- Delivery ID: `2410311404-code-coach`
- Stage: W2 Gate 2
- Date: 2026-07-23

## 1. 设计范围

W2 在 Gate 1 已验证的语言检测纵切面上补充模块边界、依赖方向、核心数据结构、状态变化、AI 调用保护和测试策略。W2 的可运行新增内容是 AI 输出合同校验器及其离线单元测试；其余模块属于明确的设计边界，不作为已完成实现。

## 2. 当前资产

| 状态 | 内容 | 文件 |
|---|---|---|
| 已实现 | C++17 语言特征检测 | `spike/src/language_detector.cpp` |
| 已验证 | C++、Python、unknown 三类样例 | `spike/tests/run_spike.sh` |
| 已实现 | AI 教学输出合同校验 | `spike/src/ai_contract.py` |
| 已验证 | 合法、缺字段、字段类型错误 | `spike/tests/test_ai_contract.py` |
| 已记录 | 语言检测与 AI 能力探针证据 | `evidence/2410311404-code-coach-w1-detector-spike.md`、`evidence/2410311404-code-coach-w1-ai-spike.md` |

## 3. 模块地图

以下名称表示设计职责，不表示 W2 已存在同名实现文件。

| 模块 | 负责 | 不负责 |
|---|---|---|
| InputGuard | 输入大小、空白和敏感模式预检 | 语言判断、模型调用 |
| LanguageDetector | C++、Python、unknown 决策与证据 | 执行输入代码 |
| StaticAnalyzer | 产生确定性问题列表 | AI 教学文本 |
| AiCoach | 根据脱敏问题摘要生成教学解释 | 修改确定性问题和分数 |
| ReviewService | 编排预检、检测、分析、AI 降级 | 直接实现语言规则 |
| ReviewRepository | 保存评审摘要与状态 | 保存凭据或默认保存原始代码 |
| Reporter | 根据已完成评审生成学习报告 | 重新运行分析器或模型 |

## 4. 依赖方向

```text
Input
  -> InputGuard
  -> LanguageDetector
  -> StaticAnalyzer
  -> ReviewService
       -> AiCoach
       -> ReviewRepository
       -> Reporter
```

约束：

- `ReviewService` 是唯一编排入口。
- `LanguageDetector`、`StaticAnalyzer` 和 AI 合同校验保持确定性。
- `AiCoach` 只能读取脱敏问题摘要，不能覆盖检测结果、问题列表或分数。
- `Reporter` 只读取已完成结果，不触发新的分析或模型调用。

## 5. SPEC 追踪

| SPEC 验收标准 | 设计责任 | W2 证据 |
|---|---|---|
| AC-1.1、AC-1.2 | LanguageDetector 的 C++ 判定与证据 | `bash spike/tests/run_spike.sh` |
| AC-2.1、AC-2.2、AC-2.3 | LanguageDetector 的 Python 与 unknown 判定 | `bash spike/tests/run_spike.sh` |
| AC-3.1、AC-3.2、AC-3.3 | AiCoach 边界与 AI 合同校验 | `python3 -m unittest discover -s spike/tests -p 'test_ai_contract.py' -v` |
| AC-4.1、AC-4.2 | ReviewService 的检查编排与 Gate 证据定位 | `bash scripts/check_w2.sh` |

## 6. 核心数据结构

### DetectionResult

- `detected_language`: `cpp | python | unknown`
- `confidence`: 0 至 0.99
- `cpp_score`: 非负整数
- `python_score`: 非负整数
- `detection_evidence`: 特征标签数组

### StaticIssue

- `issue_id`: 稳定规则编号
- `severity`: `error | warning | info`
- `location`: 行号或范围
- `message`: 确定性说明

### AiCoaching

- `summary`: 非空字符串
- `repair_order`: 非空字符串数组
- `concept_links`: 非空字符串数组
- `exercises`: 非空字符串数组

### ReviewResult

- `detection`: DetectionResult
- `static_issues`: StaticIssue 数组
- `ai_status`: `not_requested | available | unavailable | blocked`
- `ai_coaching`: AiCoaching 或空值

W2 的 `validate_ai_coaching` 已实现 AiCoaching 四字段校验；其他结构是后续实现必须遵守的设计合同。

## 7. 状态变化

```text
RECEIVED
  -> VALIDATED
  -> DETECTED
  -> ANALYZED
  -> COACHED
  -> COMPLETED
```

失败与降级：

- 输入无效：`RECEIVED -> REJECTED`
- 语言证据不足：`VALIDATED -> UNKNOWN`
- 敏感输入：`ANALYZED -> BLOCKED -> COMPLETED`
- 模型离线、超时或合同错误：`ANALYZED -> DEGRADED -> COMPLETED`

`DEGRADED` 保留确定性结果；任何状态都不得执行输入代码。

## 8. AI 调用边界

- 调用前只传递脱敏诊断摘要。
- 自动测试使用固定对象，不依赖真实模型。
- 首次响应合同错误时最多修复重试一次。
- 单次调用上限 20 秒，两次尝试总预算 35 秒。
- 空响应、非法 JSON、缺字段或字段类型错误均视为合同失败。
- 合同失败后设置 `ai_status=unavailable`，保留确定性结果。
- AI 输出不参与语言判定和确定性评分。

## 9. 失败路径

| 失败 | 可观察结果 | 保留内容 |
|---|---|---|
| 输入为空或超长 | 明确错误码或错误 JSON | 不进入检测 |
| 文件不可读 | 进程返回 2 | 不创建结果 |
| 语言证据不足 | `detected_language=unknown` | 得分与判断依据 |
| 模型不可连接 | `ai_status=unavailable` | 检测和确定性问题 |
| AI 内容不是 JSON | 合同校验失败 | 原确定性结果 |
| AI 缺字段或类型错误 | 稳定错误列表 | 原确定性结果 |
| 重试耗尽 | 降级完成 | 不伪造教学输出 |

## 10. 测试策略

| 层级 | 当前 W2 状态 | 策略 |
|---|---|---|
| 纯函数与合同 | 已有 | 语言结果断言、AI 合同离线单元测试 |
| 命令行纵切面 | 已有 | 编译检测器并运行三类固定样例 |
| API 或 UI 集成 | W2 未纳入 | 如后续增加，必须使用 mock AI 并覆盖错误路径 |
| 真实模型证据 | 已有脱敏记录 | 只作能力证据，不进入确定性 Gate |

## 11. 测试先行证据

- Red：提交 `2c85613` 先加入 `spike/tests/test_ai_contract.py`，因缺少实现模块产生 `ModuleNotFoundError`。
- Green：提交 `cf9c90a` 后加入 `spike/src/ai_contract.py`，相同命令的 3 个测试通过。
- 详细记录：`evidence/2410311404-code-coach-w2-contract-red-green.md`。

## 12. 安全与隐私

- 不执行输入代码。
- 不把代码拼接到 shell 命令。
- 真实模型调用前执行敏感模式预检。
- 日志和证据不记录凭据、完整请求头或私有服务信息。
- 自动测试不访问外部模型服务。

## 13. W2 完成定义

- DESIGN 追踪 SPEC 的 10 条验收标准。
- 两条 ADR 均包含候选方案、拒绝理由、决定、影响和回滚。
- AI 调用边界、失败路径、重试和预算保护可定位。
- 测试策略区分纯函数、命令行纵切面、集成测试和真实模型证据。
- AI 合同保留先红后绿的提交与过程记录。
- `bash scripts/check_w2.sh` 返回 `W2_GATE_CHECK=PASS`。

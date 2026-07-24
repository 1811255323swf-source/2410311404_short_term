# code_coach PRD

- Delivery ID: `2410311404-code-coach`
- Stage: W1 Gate 1
- Date: 2026-07-22

## 产品说明

`code_coach` W1 原型面向已学习 C++、准备学习 Python 的学生，通过可运行的命令行探针识别代码语言，并验证本地 AI 能否根据确定性诊断生成教学解释。

## 目标用户

主要用户是具备 C++ 基础、正在过渡到 Python 的高校学生。评审者负责复现语言检测和 AI 能力探针的结果。

## 核心场景

1. 学生提供一个 UTF-8 代码文件。
2. 语言检测器返回 `cpp`、`python` 或 `unknown`，同时给出可信度、两类得分和判断依据。
3. 脱敏诊断摘要通过本地 AI 探针生成教学解释，并由校验器记录字段完整性。
4. 评审者运行统一检查脚本，复现 W1 文档、样例、探针和 Gate 1 结果。

## W1 目标

- 用 C++17 实现可运行的语言检测最小纵切面。
- 为 C++、Python 和信息不足输入各提供一个受控样例。
- 输出稳定 JSON，不执行输入代码。
- 完成一次脱敏 AI capability spike，并如实记录成功与失败边界。
- 用两轮 Loop Engineering 记录假设、行动、证据、结果和结论。

## 成功指标

- `sample.cpp` 返回 `detected_language=cpp`，可信度不低于 0.80，判断依据不少于 2 条。
- `sample.py` 返回 `detected_language=python`，可信度不低于 0.80，判断依据不少于 2 条。
- `ambiguous.txt` 返回 `detected_language=unknown`。
- C++ 样例的 Python 得分为 0，Python 样例的 C++ 得分为 0。
- AI 探针能返回相关教学摘要；结构字段不完整时必须报告 `PARTIAL_VALIDATION_REQUIRED`。
- `bash scripts/check_w1.sh` 完成全部 W1 确定性检查。

## 用户故事

### US-1 识别 C++ 代码

作为具备 C++ 基础的学生，我希望检测器识别典型 C++ 文件，以便确认输入已进入正确的学习路径。

### US-2 识别 Python 与不确定输入

作为准备学习 Python 的学生，我希望检测器识别典型 Python 文件，并在证据不足时返回 `unknown`，避免错误分类。

### US-3 获得 AI 教学解释

作为跨语言学习者，我希望本地 AI 根据脱敏诊断说明 `nullptr` 与 `None` 的边界，并给出修复和练习方向。

### US-4 复现 W1 结果

作为评审者，我希望通过仓库内的脚本和证据文件复现语言检测结果，核对 AI 探针结论和 Gate 1 决策。

## In scope

- C++17 特征评分语言检测器；
- C++、Python、unknown 三类样例；
- JSON 输出与断言；
- 本地 Ollama 脱敏能力探针；
- PRD、SPEC、任务卡、两轮 Loop Engineering 和 Gate 1；
- W1 统一检查脚本。

## Non-goals

- 不执行输入代码；
- 不支持 C++ 和 Python 以外的语言；
- 不提供网页、网络 API、数据库或用户系统；
- 不实现完整编译诊断、Python AST 诊断或自动修复；
- 不把单次模型输出当作最终质量指标。

## 错误路径

| 操作 | 预期输出 |
|---|---|
| 未提供唯一文件参数 | 标准错误输出用法，进程返回 2 |
| 文件无法读取 | 标准错误输出 `cannot read input file`，进程返回 2 |
| 输入为空或全空白 | 输出 `empty_code` JSON，进程返回 2 |
| 输入超过 20000 字符 | 输出 `code_too_large` JSON，进程返回 2 |
| 两种语言证据不足或接近 | 返回 `detected_language=unknown` |
| 本地模型不可连接 | AI 探针返回非零状态，不影响语言检测证据 |
| 模型输出字段不完整 | 校验器报告 `PARTIAL_VALIDATION_REQUIRED` |

## AI 使用边界

AI 只接收脱敏的规则摘要，不接收账号、凭据或私有服务信息。AI 输出只用于解释能力验证，不能覆盖检测器结果，也不能声称未执行的命令已经通过。

## W1 完成定义

- PRD 与 SPEC 内容均可由仓库内文件验证；
- 4 个用户故事均有至少 2 条“操作 -> 预期输出”验收标准；
- 三类语言样例通过自动断言；
- AI 能力探针保留真实结果和结构缺口；
- 两轮 Loop Engineering 与 Gate 1 结论可定位；
- 统一检查脚本返回 `W1_GATE_CHECK=PASS`。

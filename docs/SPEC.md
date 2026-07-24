# code_coach SPEC

- Delivery ID: `2410311404-code-coach`
- Stage: W1 Gate 1
- Date: 2026-07-22

## 1. 已实现接口

### 1.1 语言检测器

编译：

```bash
g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror \
  spike/src/language_detector.cpp \
  -o spike/tmp/language_detector
```

调用：

```bash
spike/tmp/language_detector <code-file>
```

程序只读取一个代码文件，不执行文件内容。正常检测返回 0；参数、读取或输入校验失败返回 2。

### 1.2 JSON 输出

正常检测包含以下字段：

| 字段 | 类型 | 含义 |
|---|---|---|
| `detected_language` | string | `cpp`、`python` 或 `unknown` |
| `confidence` | number | 0 至 0.99 |
| `cpp_score` | integer | C++ 特征总分 |
| `python_score` | integer | Python 特征总分 |
| `detection_evidence` | string array | 命中的语言特征标签 |

空输入和超长输入返回 `error` 与 `detected_language`。

### 1.3 AI 能力探针

```bash
python3 spike/tests/run_ai_spike.py
```

脚本读取 `spike/tests/ai_request.json`，调用 `OLLAMA_HOST` 指向的本地 Ollama 服务，并检查模型内容能否解析为 JSON、是否含有 `summary`、`repair_order`、`concept_link`、`exercise` 四个字符串字段。

## 2. 检测规则

### DET-001 输入预检

- 参数数量必须为 1。
- 文件必须可读。
- 文件内容必须非空且不超过 20000 字符。

### DET-002 C++ 特征

`#include`、`int main(`、`std::`、常用模板类型、花括号与分号结构可以增加 C++ 得分。`nullptr` 可以独立增加得分；`->` 只有已有 C++ 证据时才增加得分。

### DET-003 Python 特征

函数定义、导入语句、`if __name__`、内建布尔或空值、冒号块可以增加 Python 得分。缩进只有已有 Python 证据时才增加得分。

### DET-004 决策

最高得分至少为 5，且两类得分差至少为 3 时返回得分较高的语言；否则返回 `unknown`。可信度和判断依据必须随结果输出。

## 3. 用户故事与验收标准

### US-1 识别 C++ 代码

- AC-1.1：运行 `bash spike/tests/run_spike.sh` 检测 `sample.cpp` -> 返回 `cpp` 且可信度不低于 0.80。
- AC-1.2：检查 C++ 检测结果 -> 判断依据不少于 2 条，`python_score=0`。

### US-2 识别 Python 与不确定输入

- AC-2.1：运行检测脚本处理 `sample.py` -> 返回 `python` 且可信度不低于 0.80。
- AC-2.2：检查 Python 检测结果 -> 判断依据不少于 2 条，`cpp_score=0`。
- AC-2.3：处理 `ambiguous.txt` -> 返回 `unknown` 且可信度低于 0.80。

### US-3 验证 AI 教学解释能力

- AC-3.1：本地 Ollama 可连接时运行 `python3 spike/tests/run_ai_spike.py` -> 输出模型名、结束原因和内容 JSON 状态。
- AC-3.2：模型返回相关 `summary` -> 输出 `AI_EXPLANATION_CAPABILITY=PASS`。
- AC-3.3：四个字段缺失或类型错误 -> 输出 `AI_STRUCTURED_CONTRACT=PARTIAL_VALIDATION_REQUIRED`，不报告完整通过。

### US-4 复现 Gate 1

- AC-4.1：运行 `bash scripts/check_w1.sh` -> PRD/SPEC、任务卡、JSON、语言探针和证据标记全部通过。
- AC-4.2：检查 Gate 1 文件 -> 能定位接受范围、移出范围、主要风险、最小纵切面、两轮 Loop 和最终决策。

## 4. 错误路径

| 操作 | 预期输出 |
|---|---|
| 不带参数或参数超过一个 | `usage: language_detector <code-file>`，返回 2 |
| 读取不存在的文件 | `cannot read input file`，返回 2 |
| 读取空文件 | `{"error":"empty_code","detected_language":"unknown"}`，返回 2 |
| 读取超长文件 | `{"error":"code_too_large","detected_language":"unknown"}`，返回 2 |
| 输入语言证据不足 | 正常返回 JSON，语言为 `unknown` |
| AI 服务不可连接 | AI 探针返回非零状态，语言探针仍可独立运行 |
| AI 内容不是 JSON | `CONTENT_JSON=FAIL`，AI 探针返回非零状态 |

## 5. 文件追踪

| 目标 | 实现或证据 |
|---|---|
| 语言检测实现 | `spike/src/language_detector.cpp` |
| 自动断言 | `spike/tests/run_spike.sh` |
| 三类输入 | `spike/tests/sample.cpp`、`spike/tests/sample.py`、`spike/tests/ambiguous.txt` |
| AI 请求与校验 | `spike/tests/ai_request.json`、`spike/tests/run_ai_spike.py` |
| 探针证据 | `evidence/2410311404-code-coach-w1-detector-spike.md`、`evidence/2410311404-code-coach-w1-ai-spike.md` |
| Gate 1 | `process/gate/2410311404-code-coach-gate-1-prd-spec.md` |
| 统一检查 | `scripts/check_w1.sh` |

## 6. 范围边界

W1 只验收仓库内已有的语言检测最小纵切面、AI 能力探针及其过程证据。网页、网络 API、持久化、完整静态分析和自动修复不属于本规格。

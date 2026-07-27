# W3 Core Slice Red/Green Evidence

- Delivery ID: `2410311404-code-coach`
- Date: 2026-07-23
- Evidence mode: 使用真实失败输出、通过输出和文件差异保留测试先行证据。

## Red - Production Package Missing

先创建 6 个测试文件，固定语言检测、双语言分析、评分比较、AI 合同与重试、安全预扫、SQLite 隐私、review/compare/report API 和网页入口的预期；此时没有创建 `app/`。

Command:

```bash
.venv/bin/python -m pytest -q
```

Actual result:

```text
ERROR tests/integration/test_api.py
ERROR tests/integration/test_storage_service.py
ERROR tests/unit/test_ai_security.py
ERROR tests/unit/test_analyzers.py
ERROR tests/unit/test_language_detector.py
ERROR tests/unit/test_scoring_comparison.py
Interrupted: 6 errors during collection
ModuleNotFoundError: No module named 'app'
```

Decision: 红灯有效。失败原因是生产包尚不存在，而不是测试环境偶发问题；下一步只实现满足既定 SPEC 的最小生产模块，不放宽断言。

## Initial Green - Minimal Production Slice

完成 `app/` 的领域合同、语言检测、双语言分析、AI 适配、安全预扫、SQLite、评审服务、报告、FastAPI 和网页后，重新运行既定测试。

Command:

```bash
.venv/bin/python -m pytest tests -q
```

Actual result:

```text
............................................. [100%]
45 passed
```

该命令依据 `pyproject.toml` 同时收集 W3 测试与 W1-W2 合同回归，是最小生产纵切面首次完整通过时的历史基线。实现复审补充编译器资源限制、模型离线与超时测试后，全量测试增加到 48 项；提交前审计再补充 g++ 缺失、超时和语言特征冲突 3 条边界测试，最终增加到 51 项。

覆盖内容：

- 20 个受控语言样例及准确率断言；
- C++/Python/unknown、强特征语法错误和不执行程序；
- C++/Python 教学规则、评分和修订比较；
- AI 四字段合同、一次修复重试、离线、超时和最终降级；
- 敏感输入阻断、源码不落库；
- review/compare/report API、网页入口及错误状态。

## Small-Step Focused Verification

初始红灯固定了 6 个生产模块缺失错误；各任务卡同时保留独立的红灯条件、目标测试和最小实现范围。2026-07-25 按任务边界重新执行聚焦测试，验证每个增量可以单独复现：

| Task card | Focused command | Result | Verified increment |
|---|---|---|---|
| TC-01 | `.venv/bin/python -m pytest tests/unit/test_scoring_comparison.py -q` | 2 passed | 领域合同、评分与比较 |
| TC-02 | `.venv/bin/python -m pytest tests/unit/test_language_detector.py -q` | 8 passed | C++、Python、unknown、工具异常与冲突检测 |
| TC-03 | `.venv/bin/python -m pytest tests/unit/test_analyzers.py -q` | 4 passed | C++ 与 Python 分析规则 |
| TC-04 | `.venv/bin/python -m pytest tests/unit/test_ai_security.py -q` | 7 passed | AI 合同、重试、阻断与降级 |
| TC-05 | `.venv/bin/python -m pytest tests/integration/test_storage_service.py -q` | 2 passed | SQLite、评审服务与报告 |
| TC-06 | `.venv/bin/python -m pytest tests/integration/test_api.py -q` | 4 passed | review、compare、report 与错误合同 |
| TC-07 | `.venv/bin/python -m pytest tests/integration/test_api.py -q` | 4 passed | Web 入口与结构化状态展示 |
| TC-08 | `bash scripts/check.sh` | 51 passed，全部检查通过 | 回归、评估、编译与安全边界 |

聚焦测试矩阵与任务卡中的依赖顺序相互对应，补充了从初始整体红灯到各增量独立绿灯的可复现证据。

## Implementation Feedback Loops

### Loop-1 Minimal Slice

- Hypothesis: Gate 2 模块边界足以支持从代码输入到学习报告的最小闭环。
- Action: 按 TC-01 至 TC-07 实现领域规则、检测器、分析器、AI 适配、存储、API 和本地网页。
- Evidence: `.venv/bin/python -m pytest -q` -> 历史基线 `45 passed`。
- Decision: 最小纵切面通过，进入等价实现复审。

### Loop-2 Equivalent Implementation Review

- Hypothesis: 语法探针资源边界和模型失败路径已经完整。
- Action: 使用脱敏实现摘要复审，补充 `prlimit`、离线 provider 和超时 provider 测试。
- Evidence: `spike/tests/w3_implementation_review_request.json`、`evidence/2410311404-code-coach-w3-implementation-review.md`；全量测试 `48 passed`。
- Decision: 修改后通过，继续提交前一致性审计。

### Loop-3 Pre-submission Consistency Audit

- Hypothesis: W3 文件均与 PRD、DESIGN、ADR 和阶段边界一致。
- Action: 移除模型请求中的完整源码，增加学习目标敏感预检，补充 g++ 缺失、超时和语言特征冲突测试，并删除跨阶段验收引用。
- Evidence: `tests/unit/test_ai_security.py`、`tests/unit/test_language_detector.py`、`git diff --check`、`bash scripts/check.sh`。
- Decision: 全量 `51 passed`，W3 文档只保留实现、等价审查和测试记录。

## Decision

`PASS`：初始验收测试从 6 个收集错误转为 45 项通过；实现复审后为 48 项，提交前一致性审计后为 51 项。源码不进入模型请求，工具异常与冲突决策均有确定性测试，既定验收意图未被放宽。

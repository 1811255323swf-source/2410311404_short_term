# W2 AI Contract Red/Green Evidence

- Delivery ID: `2410311404-code-coach`
- Date: 2026-07-23
- Scope: AI 教学输出四字段合同，不连接真实模型
- Test command: `python3 -m unittest discover -s spike/tests -p 'test_ai_contract.py' -v`

## Red

先加入 `spike/tests/test_ai_contract.py`，覆盖合法对象、缺字段和错误字段类型；此时实现模块尚不存在。

- Commit: `2c85613`
- Result: `FAILED (errors=1)`
- Key failure: `ModuleNotFoundError: No module named 'ai_contract'`
- Decision: 失败来自生产合同缺失，测试能够阻止空实现通过。

## Green

随后加入 `spike/src/ai_contract.py`，使用 Python 标准库校验 `summary`、`repair_order`、`concept_links`、`exercises`。

- Commit: `cf9c90a`
- Result: `Ran 3 tests ... OK`
- Passing cases:
  - 合法四字段对象被接受；
  - 缺少字段时返回稳定错误；
  - 字段类型错误时返回稳定错误。

## Boundary

该骨架证明合同校验路径可执行，不表示真实模型已经稳定遵守合同。模型适配器仍需遵守超时、最多一次修复重试、35 秒总预算、敏感输入阻断和确定性结果降级。

## Decision

`PASS`

W2_AI_CONTRACT_RED_GREEN=PASS

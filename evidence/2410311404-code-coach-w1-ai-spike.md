# W1 Local AI Capability Spike Evidence

- Delivery ID: `2410311404-code-coach`
- Role: `qa-2410311404`
- Model: `msd-2410311404-qwen3-4b-ms:latest`
- Tool: WSL Ollama local API，`OLLAMA_HOST=127.0.0.1:11435`
- Input summary: 虚构的 C++ 第 8 行 `CPP-NULLPTR` 诊断，要求解释 `nullptr` 与 Python `None` 的边界。
- Sensitive data: 无真实代码、账号、Key、Token、支付信息或私有服务地址。

## Attempt 1

请求未显式关闭 thinking，`num_predict=256`。实际结果：`message.content` 为空，`done_reason=length`，输出预算被内部推理耗尽。

Review conclusion: FAIL。不能把内部推理存在当作可用教学输出。

## Attempt 2

请求增加 `think=false` 和 JSON 输出。模型返回可解析内容与相关 `summary`，但遗漏 `concept_link`、`exercise`，并把 `repair_order` 返回为数组而不是约定的字符串。

Review conclusion: 教学解释能力可行，严格结构合同未通过。

## Final validator output

Command:

```bash
python3 spike/tests/run_ai_spike.py
```

Observed output:

```text
MODEL=msd-2410311404-qwen3-4b-ms:latest
DONE_REASON=stop
CONTENT_JSON=PASS
REQUIRED_FIELDS=PARTIAL
FIELD_TYPES=PARTIAL
AI_EXPLANATION_CAPABILITY=PASS
AI_STRUCTURED_CONTRACT=PARTIAL_VALIDATION_REQUIRED
```

Conclusion: W1 的真实 AI capability spike 已证明“根据确定性诊断生成相关教学解释”可行；响应结构不稳定是已知风险。后续改进需要增加本地字段校验、有限重试和无模型降级，自动测试不能依赖本次真实输出。

## Independent reviewer restatement

- Model: `qwen3.5:4b`，本地、脱敏。
- Restatement: 评审模型正确复述了目标用户、自动识别、静态事实、AI 跨语言解释、修改后比较与本地安全边界。
- Risk found: 三个样例不足以证明对混合语法、非标准代码和未知输入的鲁棒性。
- Output limitation: 模型输出因长度达到上限，没有返回完整 Gate 决策；因此只把“能复述与发现风险”记为证据，不把它记作 Gate PASS。

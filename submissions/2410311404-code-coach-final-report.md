# code_coach 最终报告

- Delivery ID：`2410311404-code-coach`
- 项目名称：`code_coach`
- 交付状态：Gate 3 `MODIFIED_PASS`

## 交付导航

- [第 1 次周志](2410311404-code-coach-weekly-1.md)
- [第 2 次周志](2410311404-code-coach-weekly-2.md)
- [答辩 PPT](2410311404-code-coach-defense.pptx)
- [README 复现入口](../README.md)

## 1. 项目说明

`code_coach` 是面向正在从 C++ 过渡到 Python 的学生的 AI 原生代码学习系统。
用户粘贴代码后，系统自动识别 C++ 或 Python，先给出可重复验证的静态诊断、
严重程度与确定性分数，再由可降级的 AI 教练把问题解释成迁移知识、修复顺序和
练习。用户提交修改版后，还能比较已解决、仍存在和新增的问题并导出 Markdown
报告。

核心价值不是“让模型替用户写代码”，而是把编译器或 AST 事实、教学解释和修改
反馈串成可验证的学习闭环。

## 2. 目标用户、场景与范围

主要用户是已会 C++、即将学习 Python 的学生；次要用户是需要快速查看学习证据的
教师或助教。核心场景为：

1. 粘贴 C++ 或 Python 代码并自动识别语言；
2. 查看稳定的静态问题、位置、严重程度和分数；
3. 获取 AI 教练的概念映射、修复顺序和练习；
4. 提交修改版并比较前后差异；
5. 导出不含原始源码和凭证的 Markdown 报告。

明确非目标包括自动修改源码、执行用户代码、任意语言支持、登录与班级管理、
公网部署和多人实时协作。该边界防止四周提交期发生范围蔓延。

## 3. 需求、规格与设计追踪

- PRD：[docs/PRD.md](../docs/PRD.md)，包含 4 个用户故事、成功指标、错误路径和非目标。
- SPEC：[docs/SPEC.md](../docs/SPEC.md)，把故事拆成 DET、AI、SEC 契约和 10 条“操作 ->
  预期输出”验收标准。
- DESIGN：[docs/DESIGN.md](../docs/DESIGN.md)，定义检测器、分析器、应用服务、AI 适配器、存储、
  报告和 Web 边界。
- [ADR-001](../docs/adr/ADR-001-deterministic-core-ai-adapter.md)：确定性核心是事实来源，AI 只能解释，不能改写问题或分数。
- [ADR-002](../docs/adr/ADR-002-hybrid-safe-language-detection.md)：语言检测采用特征评分与安全语法探针；C++ 探针使用临时目录、参数
  数组、仅语法检查、墙钟超时和本地资源限制。

从 PRD 到测试的追踪路径为：

`US/AC -> DESIGN 模块 -> W3 任务卡 -> 单元/集成/评估测试 -> HTTP/浏览器 UAT`。

## 4. 实现结果

### 4.1 自动语言检测

系统依据强特征分数选择候选语言，再用 Python `ast.parse` 或 C++ `g++
-fsyntax-only` 进行安全语法探针。短而模糊的 `value = 1` 返回 `unknown`，
不会误入正式分析器。20 个受控样例用于重复评估 C++、Python 和未知输入。

### 4.2 确定性分析与评分

C++ 分析器标准化 g++ 诊断，并实现 `CPP-NULLPTR`、`CPP-RAW-NEW`、
`CPP-USING-NAMESPACE` 等教学规则。Python 分析器基于 AST 和语法错误，实现
`PY-MUTABLE-DEFAULT`、`PY-BARE-EXCEPT`、`PY-NONE-IDENTITY` 等规则。
统一问题对象驱动纯函数评分与前后比较，因此相同输入可得到稳定结果。

### 4.3 AI 原生边界

AI 教练接收脱敏后的静态事实，返回摘要、修复优先级、C++/Python 概念映射和
练习。默认 mock 适配器保证演示可复现；本地 Ollama 是可替换实现。输出必须通过
结构校验，失败时最多修复重试一次；单次调用预算 20 秒，总预算 35 秒。模型超时、
离线或结构错误时，主响应仍保留静态结果并显示 `ai_status=unavailable`。

### 4.4 API、页面与存储

FastAPI 提供评审、修改比较和 Markdown 报告接口。单页 Web 界面不提供手动语言
选择，直接展示检测依据、分数、静态问题、AI 状态和修改比较。SQLite 只持久化
评审元数据、问题快照和修订结果，不保存用户原始源码。

## 5. Loop Engineering 与阶段 Gate

- Gate 1：PRD/SPEC 范围复审、语言探针与本地 AI 能力探针，结论见
  [Gate 1 评审](../process/gate/2410311404-code-coach-gate-1-prd-spec.md)。
- Gate 2：DESIGN、两条 ADR、AI 输出合同红绿测试和本地独立复核，结论见
  [Gate 2 评审](../process/gate/2410311404-code-coach-gate-2-design.md)。
- W3：先记录测试收集失败，再实现检测、分析、AI、安全、存储、API 和页面；
  证据见 [W3 红绿实现记录](../evidence/2410311404-code-coach-w3-red-green.md)。
- W3 复核：Qwen 给出“修改后通过”；接受 g++ 资源限制建议，暂不扩展超出本期
  范围的持续会话历史，证据见
  [W3 独立实现复审](../evidence/2410311404-code-coach-w3-implementation-review.md)。
- Gate 3：全量检查、HTTP 与浏览器主路径验证、安全扫描和交付审计，复现入口见
  [README](../README.md)，最终结论见本报告第 6 节。

## 6. 测试与 UAT 证据

最终检查结果：

- W1/W2 回归检查通过；
- 51 项自动化测试通过；
- 20 个受控语言样例纳入评估；
- Python 字节码编译与 C++17 探针编译通过；
- 真实 HTTP UAT 覆盖 C++、Python、比较、报告和错误路径；
- 真实浏览器完成“初次评审 -> 修改 -> 对比”主路径；
- 浏览器控制台 0 error、0 warning；
- 安全扫描结果 `SECURITY_SCAN=PASS`。

主要证据：

- [W3 红绿实现记录](../evidence/2410311404-code-coach-w3-red-green.md)
- [W3 独立实现复审](../evidence/2410311404-code-coach-w3-implementation-review.md)
- [API 集成测试](../tests/integration/test_api.py)
- [安全测试](../tests/unit/test_ai_security.py)
- [语言评估测试](../tests/evaluation/test_language_corpus.py)
- [全量检查脚本](../scripts/check.sh)
- [安全扫描脚本](../scripts/security_scan.sh)

## 7. 安全与隐私

系统不执行用户代码。C++ 只运行 `g++ -fsyntax-only`，不生成可执行文件，也不把
源码拼接进 shell 命令；探针使用临时目录、3 秒墙钟超时，并在 WSL 可用时通过
`prlimit` 限制 512 MiB 地址空间、4 秒 CPU、1 MiB 文件输出和 64 个文件描述符。
输入上限为 20,000 字符。疑似凭证在真实 AI 调用前被阻断。日志、数据库和导出
报告不保存原始源码、API Key、Token 或请求头。

## 8. 运行、测试与演示

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
bash scripts/check.sh
bash scripts/security_scan.sh
CODE_COACH_AI_PROVIDER=mock \
CODE_COACH_DB_PATH=data/code_coach.db \
.venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8124
```

建议的 5 分钟演示顺序：

1. 打开 `http://127.0.0.1:8124`，粘贴 `tests/fixtures/review_initial.cpp`；
2. 展示自动识别、确定性问题、分数和 AI 教学说明；
3. 粘贴 `tests/fixtures/review_revised.cpp`，展示分数变化与问题集合；
4. 导出 Markdown 报告；
5. 简述敏感输入阻断、模型离线降级和不保存源码。

完整运行、验证和验收步骤见 [README](../README.md)。

## 9. 角色与贡献说明

项目负责人完成需求、设计、实现、测试、UAT 与交付材料，角色职责见 [roles.md](../roles.md)。
Qwen 用于脱敏能力探针和设计复核，所有结论均由仓库命令、测试结果与文件证据约束。

## 10. 已知限制与发布条件

- 仅支持 C++17 与 Python；
- 规则集用于教学演示，不代替专业静态分析产品；
- 真实模型可用性不作为确定性 Gate；
- 当前没有公网部署或账号体系；
- 项目运行入口为 [README](../README.md)；
- 交付材料和关键证据均通过仓库相对路径互相定位。

## 11. 最终交付索引

- 总入口：[README](../README.md)
- 第 1 次周志：[submissions/2410311404-code-coach-weekly-1.md](2410311404-code-coach-weekly-1.md)
- 第 2 次周志：[submissions/2410311404-code-coach-weekly-2.md](2410311404-code-coach-weekly-2.md)
- 答辩 PPT：[submissions/2410311404-code-coach-defense.pptx](2410311404-code-coach-defense.pptx)
- Gate 1：[process/gate/2410311404-code-coach-gate-1-prd-spec.md](../process/gate/2410311404-code-coach-gate-1-prd-spec.md)
- Gate 2：[process/gate/2410311404-code-coach-gate-2-design.md](../process/gate/2410311404-code-coach-gate-2-design.md)
- W3 红绿记录：[evidence/2410311404-code-coach-w3-red-green.md](../evidence/2410311404-code-coach-w3-red-green.md)
- W3 复审：[evidence/2410311404-code-coach-w3-implementation-review.md](../evidence/2410311404-code-coach-w3-implementation-review.md)

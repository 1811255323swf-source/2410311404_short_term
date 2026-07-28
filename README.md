# code_coach

`code_coach` 是面向已掌握 C++、准备学习 Python 的学生的代码学习系统。系统自动识别 C++ 或 Python 代码，以确定性分析结果为依据输出问题、严重程度和评分，再由 AI 教练提供概念对照、修改顺序和练习建议。

## 核心功能

- 自动识别 C++ 与 Python，证据不足时返回未知语言。
- 对 C++ 编译诊断和 Python AST 结果进行统一分析。
- 输出稳定的静态问题、严重程度、位置和分数。
- 提供 C++ 与 Python 概念对照及分步骤学习建议。
- 比较修改前后的已解决、仍存在和新增问题。
- 导出不含原始源代码的 Markdown 学习报告。
- 在 AI 不可用时保留确定性分析结果。
- 阻断疑似敏感输入，不执行用户提交的源代码。

## 技术组成

- Python 3.12
- FastAPI 与 Uvicorn
- SQLite
- HTML、CSS 与 JavaScript
- pytest
- g++ C++17 语法检查

## 本地运行

运行环境为 Ubuntu 24.04，推荐在 WSL2 中执行。首次使用时安装基础工具：

```bash
sudo apt update
sudo apt install -y git g++ python3 python3-venv python3-pip ripgrep
```

确认工具可用：

```bash
python3 --version
g++ --version
git --version
rg --version
```

克隆仓库并安装依赖：

```bash
git clone git@github.com:1811255323swf-source/2410311404_short_term.git
cd 2410311404_short_term
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

启动本地服务：

```bash
CODE_COACH_AI_PROVIDER=mock \
CODE_COACH_DB_PATH=data/code_coach.db \
.venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8124
```

浏览器访问 `http://127.0.0.1:8124`。默认使用可重复验证的 mock AI 提供器，不需要外部 API Key。按 `Ctrl+C` 停止服务。

## 项目验证

在项目根目录执行：

```bash
bash scripts/check.sh
```

该命令检查 W1/W2 过程资产、Python 测试、代码编译、依赖、空白字符和敏感信息。

## 验收操作

1. 打开页面并选择“C++ 示例”。
2. 点击“开始评审”，确认语言为 `cpp`、分数为 `90`，并显示两个 `CPP-NULLPTR` 问题。
3. 在修改框中把两处 `NULL` 替换为 `nullptr`。
4. 点击“比较修改”，确认分数变化为 `+10`、已解决问题为 `2`。
5. 点击“下载报告”，确认能够获得 UTF-8 Markdown 学习报告。
6. 选择“Python 示例”重新评审，确认识别为 Python 并显示对应规则。

## 目录结构

```text
app/          应用、分析器、AI 适配器、存储和 Web 页面
docs/         PRD、SPEC、DESIGN 与 ADR
evidence/     能力探针、测试和阶段复核证据
process/      Gate、任务卡和过程记录
scripts/      自动检查与安全扫描脚本
spike/        早期能力探针及合同测试
submissions/  两次周志、最终报告与答辩 PPT
tests/        单元、集成、安全和评估测试
```


## 当前边界

- 支持 C++17 与 Python。
- 规则集用于教学反馈，不替代生产级静态分析工具。
- 不提供自动修改源代码、账号系统、公网部署或多人实时协作。
- 真实模型不可用时自动降级，不影响静态分析和评分。

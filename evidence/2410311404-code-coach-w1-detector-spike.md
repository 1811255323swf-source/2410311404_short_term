# W1 Automatic Language Detection Spike Evidence

- Delivery ID: `2410311404-code-coach`
- Role: `dev-2410311404`，复核角色 `qa-2410311404`
- Environment: WSL2 Ubuntu 24.04，g++ 13.3.0，Python 3.12.3
- Scope: 仅验证 C++ / Python / unknown 特征评分与稳定 JSON，不执行输入代码。

## Red 1：测试先于实现

Command:

```bash
bash spike/tests/run_spike.sh
```

Observed result:

```text
cc1plus: fatal error: .../spike/src/language_detector.cpp: No such file or directory
compilation terminated.
```

Decision: 失败符合预期，证明验收脚本在实现缺失时不会假通过；随后创建最小 C++17 实现。

## Green 1：三类样例通过

首次实现后，C++、Python 和模糊样例的最终语言均识别正确，测试输出 `W1_LANGUAGE_DETECTION_SPIKE=PASS`。但详细分数暴露了两个跨语言碰撞：Python 返回类型注解 `-> int` 被计为 C++ 指针特征；C++ 的 `std::` 与缩进组合被计为 Python 特征。

Decision: 虽然顶层分类通过，交叉得分会降低边界样例可靠性，因此不接受该状态作为最终绿色结果。

## Red 2：收紧交叉得分断言

先增加：

```text
python["cpp_score"] == 0
cpp["python_score"] == 0
```

两次实际失败分别为：

```text
AssertionError: detected_language=python, cpp_score=2
AssertionError: detected_language=cpp, python_score=2
```

## Green 2：修正碰撞规则

- C++ `->` 只有在已经存在其他 C++ 证据时才加分，`nullptr` 仍可独立加分。
- Python 缩进证据只有在已经存在其他 Python 证据时才加分。

Final command:

```bash
bash spike/tests/run_spike.sh
```

Final output:

```text
CPP_RESULT={"confidence": 0.99, "cpp_score": 19, "detected_language": "cpp", "detection_evidence": ["cpp:#include", "cpp:int-main", "cpp:std-namespace", "cpp:template-type", "cpp:brace-semicolon-structure"], "python_score": 0}
PYTHON_RESULT={"confidence": 0.99, "cpp_score": 0, "detected_language": "python", "detection_evidence": ["python:import-statement", "python:main-guard", "python:colon-block", "python:indented-block"], "python_score": 14}
UNKNOWN_RESULT={"confidence": 0.0, "cpp_score": 0, "detected_language": "unknown", "detection_evidence": [], "python_score": 0}
W1_LANGUAGE_DETECTION_SPIKE=PASS
```

Conclusion: W1 最小纵切面通过。三样例只证明当前检测路径可行；继续扩展前需要增加更多边界与混合语法样例。

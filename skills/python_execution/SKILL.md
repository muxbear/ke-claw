---
name: python_execution
description: Python脚本执行服务：执行用户代码和预定义Python脚本
---

# Python脚本执行技能

## 功能范围

- 用户代码执行：执行用户提供的Python代码字符串
- 预定义脚本执行：运行skills/python_execution/scripts/目录下的预定义脚本
- 数据处理：使用Python进行数据清洗、分析、转换
- 计算任务：数学计算、数据统计、文本处理

## 使用规范

1. 当用户需要执行Python代码时使用此技能
2. 预定义脚本优先：优先使用scripts/目录下的预定义脚本
3. 用户代码安全：仅执行可信的代码，注意沙箱限制
4. 输出格式化：将执行结果以清晰的格式返回给用户

## 工具说明

### execute_python

执行用户提供的Python代码字符串。

- code (string): 要执行的Python代码
- 返回: 代码执行结果或错误信息

### run_script

执行预定义脚本目录中的Python脚本。

- script_name (string): 脚本文件名（不含.py后缀）
- args (string, optional): 传递给脚本的参数
- 返回: 脚本执行结果

## 预定义脚本

可在scripts/目录下添加常用脚本：

- data_analysis.py: 数据分析脚本
- text_processing.py: 文本处理脚本
- calculator.py: 计算器脚本

添加新脚本后，agent可自动发现并使用。

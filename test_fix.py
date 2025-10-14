#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '.')

from src.formula_converter import FormulaConverter
import yaml

# 加载配置
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

fc = FormulaConverter(config)

print("=" * 80)
print("测试1: y_0 2 (有空格)")
print("=" * 80)

test1 = r"\((y_0 2 + 1)x^2 - 2(2y_0 2 + x_0)x + 2 - 10y_0 2 = 0\)"
result1 = fc.post_process_llm_output(test1)

print(f"输入: {test1}")
print(f"输出: {result1}")
print()

if "y_0^2" in result1 and "y_0 2" not in result1:
    print("✅ y_0 2 → y_0^2 修复成功！")
else:
    print("❌ y_0 2 未修复")

print()
print("=" * 80)
print("测试2: 实际 LLM 输出（完整段落）")
print("=" * 80)

test2 = r"""当 \(y_0 \neq 0\) 时，由

\[
\begin{cases}
(\bar{x}_1)^2 + y^2 = 6, \\
x_0 x + 2 y_0 y = 2,
\end{cases}
\]

得 \((y_0 2 + 1)x^2 - 2(2y_0 2 + x_0)x + 2 - 10y_0 2 = 0\),

则

\[
x_1 + x_2 = \frac{2(2y_0 2 + x_0)}{1 + y_0 2}
\]"""

result2 = fc.post_process_llm_output(test2)

# 只显示关键部分
import re
lines = result2.split('\n')
for line in lines:
    if 'y_0' in line:
        print(f"  {line}")

print()

# 检查修复
errors = []
if "y_0 2" in result2:
    errors.append("y_0 2 未修复")
if "y_0^2" not in result2:
    errors.append("y_0^2 未出现")

if errors:
    print("❌ 发现问题:")
    for e in errors:
        print(f"   - {e}")
else:
    print("✅ 所有 y_0 2 都已修复为 y_0^2")

print()
print("=" * 80)

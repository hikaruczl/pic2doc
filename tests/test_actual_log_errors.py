#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际日志中发现的OCR错误
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.formula_converter import FormulaConverter
import yaml

# 加载配置
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

formula_converter = FormulaConverter(config)

print("=" * 80)
print("测试实际日志中发现的OCR错误")
print("=" * 80)

# 测试1: y_02 无空格的情况（从实际日志中提取）
print("\n测试1: 下标+数字（无空格）")
print("-" * 80)

test_cases = [
    ("y_02", "y_0^2"),
    ("2y_02", "2y_0^2"),
    ("10y_02", "10y_0^2"),
    ("x_02", "x_0^2"),
    ("(y_02+1)", "(y_0^2+1)"),
    ("2-10y_02", "2-10y_0^2"),
]

for input_text, expected in test_cases:
    result = formula_converter.fix_common_latex_patterns(input_text)
    status = "✅" if result == expected else "❌"
    print(f"  {status} '{input_text}' -> '{expected}'")
    if result != expected:
        print(f"      实际输出: '{result}'")

# 测试2: 带控制字符的 ar{x}1
print("\n测试2: 清理控制字符 + ar修复")
print("-" * 80)

# \x08 是 backspace 字符
test_text_with_control = "(\x08ar{x}1)^2"
expected_output = "(\\bar{x}_1)^2"

result = formula_converter.fix_common_latex_patterns(test_text_with_control)
status = "✅" if result == expected_output else "❌"
print(f"  {status} 带控制字符的text -> '{expected_output}'")
if result != expected_output:
    print(f"      输入: {repr(test_text_with_control)}")
    print(f"      期望: '{expected_output}'")
    print(f"      实际: '{result}'")

# 测试3: 完整的实际日志内容（2025-10-12 03:27:22）
print("\n测试3: 完整实际日志内容")
print("-" * 80)

# 这是从实际日志中提取的LLM输出（有错误的版本）
actual_log_content = r"""当 \(y_0 \neq 0\) 时，由

\(\left\{\begin{array}{l}(x-1)^2+y^2=6,\\x_0x+2y_0y=2,\end{array}\right.\)

得 \((y_02+1)x^2-2(2y_02+x_0)x+2-10y_02=0\),

则

\begin{equation}
x_1+x_2=\frac{2(2y_02+x_0)}{1+y_02},x_1x_2=\frac{2-10y_02}{1+y_02},y_1y_2=\frac{x_02}{4y_02}x_1x_2-\frac{x_0}{2y_02}(x_1+x_2)+\frac{1}{y_02}
\end{equation}"""

# 应用修复
result = formula_converter.post_process_llm_output(actual_log_content)

# 检查关键修复
checks = [
    ("y_02", "y_0^2", "y_0^2" in result and "y_02" not in result),
    ("2y_02", "2y_0^2", "2y_0^2" in result and "2y_02" not in result),
    ("10y_02", "10y_0^2", "10y_0^2" in result and "10y_02" not in result),
    ("x_02", "x_0^2", "x_0^2" in result and "x_02" not in result),
]

print("关键修复检查:")
all_passed = True
for original, fixed, passed in checks:
    status = "✅" if passed else "❌"
    print(f"  {status} '{original}' -> '{fixed}'")
    if not passed:
        all_passed = False
        # 显示相关部分
        import re
        matches = re.findall(r'.{0,20}' + re.escape(original) + r'.{0,20}', result)
        if matches:
            print(f"      在结果中找到: {matches[:2]}")
        elif fixed.replace("^", "_") in result:
            print(f"      ⚠️  修复未生效，原样保留")
        else:
            print(f"      ⚠️  未找到原始错误（可能已部分修复）")

print("\n修复后的内容片段:")
print("-" * 80)
# 显示前300个字符
print(result[:300] + "...")

# 测试4: 组合测试 - 同时包含多种错误
print("\n" + "=" * 80)
print("测试4: 组合错误")
print("-" * 80)

combined_test = "\x08ar{x}1 and y_02 and 2y_02 and x_0 2"
result = formula_converter.fix_common_latex_patterns(combined_test)
print(f"输入:  {repr(combined_test)}")
print(f"输出:  {result}")

expected_fixes = {
    "\\bar{x}_1": "\\bar{x}_1" in result,
    "y_0^2": "y_0^2" in result,
    "2y_0^2": "2y_0^2" in result,
    "x_0^2": "x_0^2" in result,
}

print("\n修复检查:")
all_passed = True
for fix_name, passed in expected_fixes.items():
    status = "✅" if passed else "❌"
    print(f"  {status} {fix_name}")
    if not passed:
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("✅ 所有测试通过！")
else:
    print("❌ 部分测试失败，需要进一步检查")
print("=" * 80)

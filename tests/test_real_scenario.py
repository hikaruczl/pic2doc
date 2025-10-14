#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实际场景测试：模拟真实的OCR错误输入
"""

import sys
import os
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.formula_converter import FormulaConverter
from src.document_generator import DocumentGenerator

# 加载配置
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

formula_converter = FormulaConverter(config)
document_generator = DocumentGenerator(config)

print("=" * 80)
print("实际场景测试：模拟真实的OCR错误输入")
print("=" * 80)

# 用户提供的实际错误内容
user_provided_error = r"""当 $y_0 \neq 0$ 时，由
$$\begin{cases}(ar{x}1)^2 + y^2 = 6, \\x_0 x + 2 y_0 y = 2,\end{cases}$$
得 $(y_0 2 + 1)x^2 - 2(2y_0 2 + x_0)x + 2 - 10y_0 2 = 0$，
则
$$\begin{equation}x_1 + x_2 = \frac{2(2y_0 2 + x_0)}{1 + y_0 2}, x_1 x_2 = \frac{2 - 10y_0 2}{1 + y_0 2}, y_1 y_2 = \frac{x_0 2}{4y_0 2} x_1 x_2 - \frac{x_0}{2y_0 2} (x_1 + x_2) + \frac{1}{y_0 2}\end{equation}$$
$$\begin{equation}= \frac{-5x_0 2 - 4x_0 + 4}{2 + 2y_0 2}.\end{equation}$$
因为
$$\begin{equation}FA \rightarrow \cdot FB \rightarrow = (x_1 + 1, y_1) \cdot (x_2 + 1, y_2) = x_1 x_2 + x_1 + x_2 + 1 + y_1 y_2\end{equation}$$
$$\begin{equation}= \frac{4 - 20y_0 2 + 8y_0 2 + 4x_0 + 2 + 2y_0 2}{2 + 2y_0 2} + \frac{-5x_0 2 - 4x_0 + 4}{2 + 2y_0 2} = \frac{-5(x_0 2 + 2y_0 2) + 10}{2 + 2y_0 2} = 0.\end{equation}$$
所以 $FA \rightarrow \perp FB \rightarrow$，即 $\angle AFB = 90^\circ$。故 $\angle AFB$ 为定值 $90^\circ$。"""

print("\n步骤1: 原始输入（含OCR错误）")
print("-" * 80)
print(user_provided_error[:300] + "...")

# 逐步测试每个修复函数
print("\n步骤2: 应用Unicode修复")
print("-" * 80)
after_unicode = formula_converter.fix_unicode_to_latex(user_provided_error)
if after_unicode == user_provided_error:
    print("⚠️  没有变化（可能没有Unicode符号）")
else:
    print("✅ 有变化")
    # 显示差异
    import difflib
    diff = difflib.unified_diff(
        user_provided_error[:200].split('\n'),
        after_unicode[:200].split('\n'),
        lineterm=''
    )
    for line in list(diff)[:10]:
        print(line)

print("\n步骤3: 应用LaTeX格式修复")
print("-" * 80)
after_latex_fix = formula_converter.fix_common_latex_patterns(after_unicode)

# 检查关键修复
key_fixes = [
    ("ar{x}1", r'\bar{x}_1', after_latex_fix),
    ("y_0 2", "y_0^2", after_latex_fix),
    ("x_0 2", "x_0^2", after_latex_fix),
    ("2y_0 2", "2y_0^2", after_latex_fix),
]

print("关键修复检查:")
for original, expected, text in key_fixes:
    found = expected in text
    status = "✅" if found else "❌"
    print(f"  {status} '{original}' → '{expected}': {found}")
    if not found and original in text:
        print(f"      ⚠️  原始错误仍然存在: '{original}'")

print("\n步骤4: 完整后处理流程")
print("-" * 80)
fully_processed = formula_converter.post_process_llm_output(user_provided_error)

# 再次检查
print("完整后处理后的检查:")
for original, expected, _ in key_fixes:
    found = expected in fully_processed
    still_has_error = original in fully_processed
    status = "✅" if found and not still_has_error else "❌"
    print(f"  {status} '{original}' → '{expected}'")
    if found:
        print(f"      ✓ 修复成功")
    if still_has_error:
        print(f"      ✗ 原始错误仍存在")

print("\n步骤5: 显示修复后的内容")
print("-" * 80)
print(fully_processed[:400] + "...")

print("\n步骤6: 生成Word文档")
print("-" * 80)
try:
    elements = formula_converter.parse_content(fully_processed)
    formatted_elements = formula_converter.format_for_word(elements)

    doc = document_generator.create_document(formatted_elements)
    doc_path = 'output/test_real_scenario.docx'
    document_generator.save_document(doc, 'test_real_scenario.docx')

    file_size = os.path.getsize(doc_path)
    print(f"✅ 文档已生成: {doc_path} ({file_size/1024:.1f} KB)")
    print("\n请在Word中打开此文档，检查:")
    print("  1. 所有 ar{x}1 是否都变成了 x̄₁")
    print("  2. 所有 y_0 2 是否都变成了 y₀²")
    print("  3. 公式是否能正确显示")

except Exception as e:
    print(f"❌ 文档生成失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

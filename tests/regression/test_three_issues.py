#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试三个问题的修复
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / 'config' / 'config.yaml'

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.document_generator import DocumentGenerator
from src.formula_converter import FormulaConverter
from src.main import AdvancedOCR
import yaml

print("\n" + "="*70)
print("问题修复验证测试")
print("="*70)

# 加载配置
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 测试1: f'(x) 不应该变成 f'}(x)
print("\n" + "-"*70)
print("测试1: Prime符号标准化")
print("-"*70)

test_cases_1 = [
    ("f'(x) = 1", "f^{\\prime}(x) = 1"),
    ("f''(x) = 2", "f^{\\prime\\prime}(x) = 2"),
    ("f'(x) + g'(x)", "f^{\\prime}(x) + g^{\\prime}(x)"),
]

for input_latex, expected_output in test_cases_1:
    result = DocumentGenerator._normalize_inline_latex(input_latex)
    if result == expected_output:
        print(f"✓ '{input_latex}' → '{result}'")
    else:
        print(f"✗ '{input_latex}'")
        print(f"  预期: {expected_output}")
        print(f"  实际: {result}")

# 测试2: 修复LLM输出格式问题
print("\n" + "-"*70)
print("测试2: LLM输出预处理")
print("-"*70)

converter = FormulaConverter(config)

# 模拟LLM返回的错误格式
test_llm_output = """$
\\begin{aligned}
& (5)\\ f(x)=\\frac{1}{2}x^{2}\\ln x \\\\
& \\text { 解: 由题知, } x \\in(0,+\\infty)
\\end{aligned}
$
"""

print("原始LLM输出(前100字符):")
print(test_llm_output[:100] + "...")

processed = converter._preprocess_llm_output(test_llm_output)

print("\n预处理后(前200字符):")
print(processed[:200] + "...")

# 检查是否正确拆分为$$$$格式
if "$$" in processed and processed.count("$$") >= 2:
    print("\n✓ 成功将错误的单$转换为双$$格式")
else:
    print("\n✗ 未能正确转换格式")

# 测试3: 重叠检测增强
print("\n" + "-"*70)
print("测试3: 重叠内容检测")
print("-"*70)

test_cases_3 = [
    # (现有文本结尾, 新内容开头, 应该被移除)
    (
        "练习2：讨论下列函数的单调性。\n\n（1）$f(x)=\\frac{e^{-x}}{3}(x^{2}-2x-7)$",
        "（1）$f(x)=\\frac{e^{-x}}{3}(x^{2}-2x-7)$\n\n解：由题知",
        True
    ),
    (
        "因为 $x \\in(0,+\\infty)$ 时，$f''(x)=e^{x}-1>0$",
        "因为 $x \\in (0,+\\infty)$ 时，$f''(x)=e^x-1>0$，所以函数",
        True
    ),
]

for i, (existing, new, should_overlap) in enumerate(test_cases_3, 1):
    result = AdvancedOCR._trim_overlap_text(existing, new)

    # 检查是否移除了重叠
    overlap_removed = len(result) < len(new)

    print(f"\n测试 3.{i}:")
    print(f"  现有文本末尾: ...{existing[-50:]}")
    print(f"  新内容开头: {new[:50]}...")
    print(f"  结果长度: {len(new)} → {len(result)}")

    if should_overlap and overlap_removed:
        print(f"  ✓ 正确检测并移除重叠 ({len(new) - len(result)} 字符)")
    elif not should_overlap and not overlap_removed:
        print(f"  ✓ 正确保留无重叠内容")
    else:
        print(f"  ✗ 检测结果不符合预期")
        print(f"    预期移除重叠: {should_overlap}")
        print(f"    实际移除重叠: {overlap_removed}")

# 综合测试
print("\n" + "="*70)
print("综合测试")
print("="*70)

test_content = """练习：求下列函数的导数。

（1）$f'(x) = 1 - \\frac{1}{2}x - e^{-x}$

解：$f''(x) = -\\frac{1}{2} + e^{-x}$

$$
\\begin{aligned}
& (2)\\ g(x) = x^2 \\\\
& \\text{解: } g'(x) = 2x
\\end{aligned}
$$
"""

print("\n测试内容:")
print(test_content)

print("\n解析结果:")
elements = converter.parse_content(test_content)

for i, elem in enumerate(elements, 1):
    if elem['type'] == 'text':
        content_preview = elem['content'][:80].replace('\n', ' ')
        print(f"  {i}. [文本] {content_preview}...")
    else:
        latex_preview = elem['latex'][:80].replace('\n', ' ')
        print(f"  {i}. [公式] {latex_preview}...")

print("\n" + "="*70)
print("测试完成")
print("="*70)
print("\n请检查:")
print("1. f'(x) 是否正确转换为 f^{\\prime}(x) (不带额外的})")
print("2. 错误的单$格式是否正确转换为双$$")
print("3. 重叠内容是否被正确检测和移除")
print("\n如果所有测试通过，可以运行实际的OCR测试。")

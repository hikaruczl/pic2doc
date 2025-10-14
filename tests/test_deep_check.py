#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度检查：验证Word文档中的OMML结构
"""

import sys
import os
import yaml
from zipfile import ZipFile
from lxml import etree

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
print("深度检查：验证Word文档中的OMML结构")
print("=" * 80)

# ============================================================================
# 检查矩阵OMML结构
# ============================================================================
print("\n检查矩阵OMML结构:")
print("-" * 80)

test_content = r"""
$$\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}$$
"""

elements = formula_converter.parse_content(test_content)
formatted_elements = formula_converter.format_for_word(elements)

doc = document_generator.create_document(formatted_elements)
doc_path = 'output/test_matrix_omml.docx'
document_generator.save_document(doc, 'test_matrix_omml.docx')

# 解压docx并检查document.xml
with ZipFile(doc_path, 'r') as zip_ref:
    document_xml = zip_ref.read('word/document.xml')

# 解析XML
root = etree.fromstring(document_xml)

# 查找所有oMath元素
MATH_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

namespaces = {
    'm': MATH_NS,
    'w': W_NS
}

# 查找所有的 m:d 元素（括号结构）
d_elements = root.findall('.//m:d', namespaces)

print(f"\n找到 {len(d_elements)} 个括号结构 (m:d)")

for i, d_elem in enumerate(d_elements, 1):
    print(f"\n括号结构 {i}:")

    # 查找 m:dPr 属性
    d_pr = d_elem.find('m:dPr', namespaces)
    if d_pr is not None:
        # 查找开闭括号
        beg_chr = d_pr.find('m:begChr', namespaces)
        end_chr = d_pr.find('m:endChr', namespaces)

        beg_val = beg_chr.get(f'{{{MATH_NS}}}val') if beg_chr is not None else None
        end_val = end_chr.get(f'{{{MATH_NS}}}val') if end_chr is not None else None

        print(f"  开括号: {beg_val}")
        print(f"  闭括号: {end_val}")

        # 检查是否包含矩阵 (m:m)
        m_elem = d_elem.find('.//m:m', namespaces)
        if m_elem is not None:
            rows = m_elem.findall('m:mr', namespaces)
            print(f"  ✅ 包含矩阵，{len(rows)} 行")

            # 期望值检查
            if beg_val == '[' and end_val == ']':
                print(f"  ✅ 方括号正确")
            else:
                print(f"  ❌ 方括号不正确（期望 [ ]）")
        else:
            print(f"  ⚠️  不包含矩阵")
    else:
        print(f"  ❌ 未找到括号属性")

# ============================================================================
# 检查用户原始问题中的复杂公式
# ============================================================================
print("\n" + "=" * 80)
print("检查用户原始问题的复杂公式:")
print("-" * 80)

original_problem = r"""
当 $y_0 2 \neq 0$ 时，由
$$\begin{cases}
(ar{x}1)^2 + y^2 = 6, \\
x_0 x + 2 y_0 y = 2,
\end{cases}$$
得 $(y_0 2 + 1)x^2 - 2(2y_0 2 + x_0)x + 2 - 10y_0 2 = 0$，
则
$$x_1 + x_2 = \frac{2(2y_0 2 + x_0)}{1 + y_0 2}, x_1 x_2 = \frac{2 - 10y_0 2}{1 + y_0 2}$$
"""

print("\n原始输入（含OCR错误）:")
print(original_problem[:200] + "...")

# 应用修复
fixed_content = formula_converter.post_process_llm_output(original_problem)

print("\n修复后:")
print(fixed_content[:200] + "...")

# 检查关键修复
fixes_check = [
    ("y_0 2", "y_0^2", "y_0^2" in fixed_content),
    ("ar{x}1", "\\bar{x}_1", "\\bar{x}_1" in fixed_content),
    ("2y_0 2", "2y_0^2", "2y_0^2" in fixed_content),
]

print("\n关键修复检查:")
for original, expected, passed in fixes_check:
    status = "✅" if passed else "❌"
    print(f"  {status} '{original}' → '{expected}'")

# 生成完整文档
print("\n生成完整文档...")
elements = formula_converter.parse_content(fixed_content)
formatted_elements = formula_converter.format_for_word(elements)

doc2 = document_generator.create_document(formatted_elements)
doc2_path = 'output/test_original_problem.docx'
document_generator.save_document(doc2, 'test_original_problem.docx')

file_size = os.path.getsize(doc2_path)
print(f"✅ 文档已生成: {doc2_path} ({file_size/1024:.1f} KB)")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 80)
print("总结")
print("=" * 80)
print("""
生成的测试文档:
  1. output/test_matrix_omml.docx - 矩阵OMML结构检查
  2. output/test_original_problem.docx - 原始问题完整测试

请在Word中打开这些文档，验证：
  1. 矩阵是否显示正确的括号（方括号 []）
  2. 公式是否正确显示（没有OCR错误）
  3. 如果有TikZ代码，图形是否正确渲染

如果文档中显示不正确，请提供具体的错误截图或描述。
""")

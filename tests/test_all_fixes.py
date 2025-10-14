#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试：验证所有三个问题的修复
"""

import sys
import os
import yaml

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.formula_converter import FormulaConverter
from src.document_generator import DocumentGenerator

# 加载配置
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

print("=" * 80)
print("完整测试：验证所有三个问题的修复")
print("=" * 80)

# 初始化
formula_converter = FormulaConverter(config)
document_generator = DocumentGenerator(config)

print("\n初始化成功")
print(f"  FormulaConverter: OK")
print(f"  DocumentGenerator: OK")
print(f"  TikZ enabled: {document_generator.tikz_renderer.enabled}")

# ============================================================================
# 问题1测试：OCR错误修复
# ============================================================================
print("\n" + "=" * 80)
print("问题1测试：OCR错误修复")
print("=" * 80)

test1_input = r"""
当 $y_0 2 \neq 0$ 时，由
\begin{cases}
(ar{x}1)^2 + y^2 = 6, \\
x_0 x + 2 y_0 y = 2,
\end{cases}
得 $(y_0 2 + 1)x^2 - 2(2y_0 2 + x_0)x + 2 - 10y_0 2 = 0$
"""

print("\n原始输入（包含OCR错误）:")
print(test1_input)

# 测试修复
fixed1 = formula_converter.fix_unicode_to_latex(test1_input)
fixed1 = formula_converter.fix_common_latex_patterns(fixed1)

print("\n修复后:")
print(fixed1)

# 检查修复是否生效
checks1 = [
    ("ar{ → \\bar{", r'\bar{x}' in fixed1),
    ("y_0 2 → y_0^2", r'y_0^2' in fixed1 or r'y_0 ^2' in fixed1),
    ("ar{x}1 → \\bar{x}_1", r'\bar{x}_1' in fixed1 or r'\bar{x}_{1}' in fixed1),
]

print("\n修复验证:")
for desc, passed in checks1:
    status = "✅" if passed else "❌"
    print(f"  {status} {desc}")

# ============================================================================
# 问题2测试：矩阵括号
# ============================================================================
print("\n" + "=" * 80)
print("问题2测试：矩阵括号")
print("=" * 80)

test2_cases = [
    ("pmatrix (圆括号)", r"\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}"),
    ("bmatrix (方括号)", r"\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}"),
    ("vmatrix (竖线)", r"\begin{vmatrix} 1 & 2 \\ 3 & 4 \end{vmatrix}"),
]

from latex2mathml.converter import convert as latex_to_mathml
import xml.etree.ElementTree as ET

for name, latex in test2_cases:
    print(f"\n{name}:")
    print(f"  LaTeX: {latex}")

    try:
        mathml = latex_to_mathml(latex)

        # 解析MathML，检查结构
        root = ET.fromstring(mathml)

        # 查找mrow > mo + mtable + mo 结构
        def check_matrix_structure(elem, depth=0):
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

            if tag == 'mrow':
                children = list(elem)
                if len(children) >= 3:
                    first_tag = children[0].tag.split('}')[-1] if '}' in children[0].tag else children[0].tag
                    last_tag = children[-1].tag.split('}')[-1] if '}' in children[-1].tag else children[-1].tag

                    # 检查是否有mtable
                    has_mtable = any(
                        (child.tag.split('}')[-1] if '}' in child.tag else child.tag) == 'mtable'
                        for child in children
                    )

                    if first_tag == 'mo' and last_tag == 'mo' and has_mtable:
                        open_bracket = children[0].text or ''
                        close_bracket = children[-1].text or ''
                        return True, open_bracket, close_bracket

            for child in elem:
                result = check_matrix_structure(child, depth + 1)
                if result[0]:
                    return result

            return False, '', ''

        found, open_br, close_br = check_matrix_structure(root)
        if found:
            print(f"  MathML结构: ✅ 找到矩阵结构")
            print(f"  括号: '{open_br}' ... '{close_br}'")
        else:
            print(f"  MathML结构: ❌ 未找到矩阵结构")

    except Exception as e:
        print(f"  ❌ 转换失败: {e}")

# 测试OMML转换
print("\n测试Word文档生成（OMML转换）:")
test2_doc_content = r"""
这是几个矩阵示例：

圆括号矩阵（pmatrix）：
$$\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}$$

方括号矩阵（bmatrix）：
$$\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}$$

竖线矩阵（vmatrix）：
$$\begin{vmatrix} 1 & 2 \\ 3 & 4 \end{vmatrix}$$
"""

elements = formula_converter.parse_content(test2_doc_content)
formatted_elements = formula_converter.format_for_word(elements)

print(f"  解析元素数: {len(elements)}")
print(f"  格式化元素数: {len(formatted_elements)}")

try:
    doc = document_generator.create_document(formatted_elements)
    output_path = 'output/test_matrices.docx'
    saved_path = document_generator.save_document(doc, 'test_matrices.docx')
    file_size = os.path.getsize(saved_path)
    print(f"  ✅ 文档已生成: {saved_path} ({file_size/1024:.1f} KB)")
except Exception as e:
    print(f"  ❌ 文档生成失败: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# 问题3测试：TikZ渲染
# ============================================================================
print("\n" + "=" * 80)
print("问题3测试：TikZ渲染")
print("=" * 80)

test3_content = r"""
这是一个正方体：

```tikz
\begin{tikzpicture}[scale=2]
  \draw[fill=gray!20] (0,0) -- (1,0) -- (1,1) -- (0,1) -- cycle;
  \draw[fill=gray!40] (0.3,0.3) -- (1.3,0.3) -- (1.3,1.3) -- (0.3,1.3) -- cycle;
  \draw (0,0) -- (0.3,0.3);
  \draw (1,0) -- (1.3,0.3);
  \draw (1,1) -- (1.3,1.3);
  \draw (0,1) -- (0.3,1.3);
\end{tikzpicture}
```

正方体的体积为 $V = a^3$。
"""

print("\n测试TikZ代码检测:")
tikz_blocks = document_generator.tikz_renderer.extract_tikz_blocks(test3_content)
print(f"  找到 {len(tikz_blocks)} 个TikZ代码块")

if tikz_blocks:
    for i, block in enumerate(tikz_blocks, 1):
        print(f"  代码块 {i}: 位置 {block['start']}-{block['end']}")

print("\n测试TikZ渲染:")
if document_generator.tikz_renderer.enabled:
    simple_tikz = r"\begin{tikzpicture}[scale=2]\draw (0,0) -- (1,1);\end{tikzpicture}"
    image = document_generator.tikz_renderer.render_tikz_to_image(simple_tikz)
    if image:
        print(f"  ✅ TikZ渲染成功: {image.size}")
    else:
        print(f"  ❌ TikZ渲染失败")
else:
    print(f"  ⚠️  TikZ渲染器未启用")

print("\n测试完整文档生成（含TikZ）:")
elements3 = formula_converter.parse_content(test3_content)
formatted_elements3 = formula_converter.format_for_word(elements3)

try:
    doc3 = document_generator.create_document(formatted_elements3)
    output_path3 = 'output/test_tikz.docx'
    saved_path3 = document_generator.save_document(doc3, 'test_tikz.docx')
    file_size3 = os.path.getsize(saved_path3)
    print(f"  ✅ 文档已生成: {saved_path3} ({file_size3/1024:.1f} KB)")
except Exception as e:
    print(f"  ❌ 文档生成失败: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)
print("\n请检查生成的文档:")
print("  - output/test_matrices.docx (矩阵括号测试)")
print("  - output/test_tikz.docx (TikZ渲染测试)")
print("\n如有问题，请查看上述测试输出中的 ❌ 标记")

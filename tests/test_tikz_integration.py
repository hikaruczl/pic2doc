#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试：TikZ渲染集成
测试从LLM输出（包含TikZ代码）到生成Word文档的完整流程
"""

import sys
import os
import yaml
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from formula_converter import FormulaConverter
from document_generator import DocumentGenerator

# 加载配置
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

print("=" * 80)
print("端到端测试：TikZ渲染集成")
print("=" * 80)

# 模拟LLM输出，包含文本、公式和TikZ代码
llm_output = """
这是一道立体几何问题。

如图所示，有一个正方体 $ABCD-A'B'C'D'$，其边长为 $a$。

```tikz
\\begin{tikzpicture}[scale=2]
  \\draw[fill=gray!20] (0,0) -- (1,0) -- (1,1) -- (0,1) -- cycle;
  \\draw[fill=gray!40] (0.3,0.3) -- (1.3,0.3) -- (1.3,1.3) -- (0.3,1.3) -- cycle;
  \\draw (0,0) -- (0.3,0.3);
  \\draw (1,0) -- (1.3,0.3);
  \\draw (1,1) -- (1.3,1.3);
  \\draw (0,1) -- (0.3,1.3);
  \\node at (-0.2,0) {A};
  \\node at (1.2,0) {B};
  \\node at (1.2,1) {C};
  \\node at (-0.2,1) {D};
  \\node at (0.1,0.3) {A'};
  \\node at (1.5,0.3) {B'};
  \\node at (1.5,1.3) {C'};
  \\node at (0.1,1.3) {D'};
\\end{tikzpicture}
```

求该正方体的体积和表面积。

解：
正方体的体积为：
$$V = a^3$$

正方体的表面积为：
$$S = 6a^2$$

另外，还有一个圆锥示例：

```tikz
\\begin{tikzpicture}[scale=2]
  \\draw[fill=gray!20] (0,0) ellipse (1 and 0.3);
  \\draw[fill=gray!40] (-1,0) -- (0,2) -- (1,0);
  \\draw[dashed] (-1,0) arc (180:360:1 and 0.3);
  \\node at (0,-0.4) {Base};
  \\node at (0,2.2) {Apex};
\\end{tikzpicture}
```

圆锥的体积为 $V = \\frac{1}{3}\\pi r^2 h$，其中 $r$ 为底面半径，$h$ 为高。
"""

print("\n1. LLM输出内容:")
print("-" * 80)
print(llm_output)
print("-" * 80)

# 初始化转换器
print("\n2. 初始化转换器...")
formula_converter = FormulaConverter(config)
document_generator = DocumentGenerator(config)

print(f"   FormulaConverter: OK")
print(f"   DocumentGenerator: OK (TikZ enabled: {document_generator.tikz_renderer.enabled})")

# 解析内容
print("\n3. 解析内容（提取公式和文本）...")
elements = formula_converter.parse_content(llm_output)
print(f"   解析完成: {len(elements)} 个元素")

for i, elem in enumerate(elements, 1):
    elem_type = elem['type']
    if elem_type == 'text':
        content_preview = elem['content'][:50].replace('\n', ' ')
        print(f"   元素 {i}: 文本 - {content_preview}...")
    elif elem_type == 'formula':
        latex_preview = elem['latex'][:50]
        print(f"   元素 {i}: 公式 - {latex_preview}...")

# 格式化元素
print("\n4. 格式化元素...")
formatted_elements = formula_converter.format_for_word(elements)
print(f"   格式化完成: {len(formatted_elements)} 个元素")

# 生成文档
print("\n5. 生成Word文档...")
try:
    doc = document_generator.create_document(
        formatted_elements,
        original_image=None,
        metadata={'title': 'TikZ集成测试'}
    )
    print("   文档创建成功")

    # 保存文档
    output_path = os.path.join('output', 'test_tikz_integration.docx')
    saved_path = document_generator.save_document(doc, 'test_tikz_integration.docx')
    print(f"   文档已保存到: {saved_path}")

    # 检查文件大小
    file_size = os.path.getsize(saved_path)
    print(f"   文件大小: {file_size / 1024:.2f} KB")

    print("\n" + "=" * 80)
    print("✅ 测试成功！")
    print("=" * 80)
    print(f"\n请打开文档查看结果: {saved_path}")
    print("文档应该包含：")
    print("  - 文本段落")
    print("  - 行内公式 ($...$)")
    print("  - 显示公式 ($$...$$)")
    print("  - TikZ渲染的立体几何图形（正方体和圆锥）")
    print()

except Exception as e:
    print(f"\n❌ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

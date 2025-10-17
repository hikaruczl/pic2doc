#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试文档生成功能"""

import sys
import yaml
from pathlib import Path

# 设置正确的Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 直接导入src模块
import src.document_generator as dg_module
from docx import Document as DocxDocument

print("=" * 80)
print("测试文档生成功能")
print("=" * 80)

# 1. 读取配置
print("\n步骤1: 加载配置文件")
config_path = Path(__file__).parent / 'config' / 'config.yaml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
print(f"✓ 配置文件加载成功: {config_path}")

# 2. 读取LLM输出
print("\n步骤2: 读取LLM输出文件")
llmout_path = Path(__file__).parent / 'llmout'
with open(llmout_path, 'r', encoding='utf-8') as f:
    llm_output = f.read()
print(f"✓ LLM输出读取成功: {len(llm_output)} 字符")

# 3. 使用新的提取函数检测SVG JSON
print("\n步骤3: 检测SVG JSON块")
svg_blocks = dg_module.DocumentGenerator._extract_svg_json_blocks(llm_output)
print(f"检测到 {len(svg_blocks)} 个SVG JSON块")

for i, (start, end, json_str) in enumerate(svg_blocks, 1):
    print(f"\n  块 {i}:")
    print(f"    位置: start={start}, end={end}")
    print(f"    JSON长度: {len(json_str)} 字符")

    # 尝试解析JSON
    import json
    try:
        data = json.loads(json_str)
        print(f"    ✓ JSON解析成功")
        print(f"    img_b64长度: {len(data.get('img_b64', ''))} 字符")
        print(f"    format: {data.get('format')}")

        # 尝试Base64解码
        import base64
        try:
            img_b64 = data.get('img_b64', '')
            svg_bytes = base64.b64decode(img_b64)
            print(f"    ✓ Base64解码成功: {len(svg_bytes)} bytes")

            # 检查SVG完整性
            svg_text = svg_bytes.decode('utf-8')
            if '<svg' in svg_text.lower():
                print(f"    ✓ 包含SVG标签")
                if '</svg>' in svg_text.lower():
                    print(f"    ✓ SVG标签完整")
                else:
                    print(f"    ✗ SVG标签不完整（缺少</svg>）")
            else:
                print(f"    ✗ 未检测到SVG标签")

        except Exception as e:
            print(f"    ✗ Base64解码失败: {e}")

    except json.JSONDecodeError as e:
        print(f"    ✗ JSON解析失败: {e}")

# 4. 创建文档生成器
print("\n" + "=" * 80)
print("步骤4: 创建文档生成器并生成Word文档")
print("=" * 80)

doc_gen = dg_module.DocumentGenerator(config)
print("✓ 文档生成器初始化成功")

# 5. 创建测试元素列表
print("\n创建测试元素...")
elements = [
    {
        'type': 'paragraph',
        'content': llm_output
    }
]

# 6. 生成文档
print("\n生成Word文档...")
doc = doc_gen.create_document(
    elements=elements,
    original_image=None,
    metadata={'source': 'test', 'timestamp': '2025-10-15'},
    minimal_layout=True
)

# 7. 保存文档
output_path = Path(__file__).parent / 'test_output.docx'
doc.save(str(output_path))
print(f"✓ 文档保存成功: {output_path}")

# 8. 验证文档
print("\n" + "=" * 80)
print("步骤5: 验证生成的文档")
print("=" * 80)

# 重新打开文档检查
doc_check = DocxDocument(str(output_path))
print(f"✓ 文档可以正常打开")
print(f"  段落数: {len(doc_check.paragraphs)}")
print(f"  图片数: {len(doc_check.inline_shapes)}")

if len(doc_check.inline_shapes) > 0:
    print(f"\n✓✓✓ 成功！文档中包含 {len(doc_check.inline_shapes)} 张图片")
    for i, shape in enumerate(doc_check.inline_shapes, 1):
        print(f"    图片 {i}: {shape.width} x {shape.height}")
else:
    print(f"\n⚠️  文档中没有图片，可能SVG处理失败")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
print(f"\n请打开文档查看: {output_path}")

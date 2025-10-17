#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试SVG JSON提取功能"""

import json
import sys
sys.path.insert(0, '/mnt/vdb/dev/advanceOCR/src')

from document_generator import DocumentGenerator

# 测试用例1：短Base64字符串
test_text_1 = '''【图形】
{"img_b64": "PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCI+PGNpcmNsZSBjeD0iNTAiIGN5PSI1MCIgcj0iNDAiLz48L3N2Zz4=", "format": "svg"}

这是一些文字。
'''

# 测试用例2：超长Base64字符串（模拟实际情况）
long_b64 = "A" * 10000  # 10000个字符的Base64字符串
test_text_2 = '【图形】\n' + '{"img_b64": "' + long_b64 + '", "format": "svg"}\n\n这是一些文字。\n'

# 测试用例3：没有【图形】标记
test_text_3 = '前面的文字\n{"img_b64": "' + long_b64 + '", "format": "svg"}\n后面的文字\n'

print("=" * 80)
print("测试SVG JSON提取功能")
print("=" * 80)

# 测试1
print("\n测试1: 短Base64字符串")
blocks_1 = DocumentGenerator._extract_svg_json_blocks(test_text_1)
print(f"找到 {len(blocks_1)} 个SVG JSON块")
for i, (start, end, json_str) in enumerate(blocks_1, 1):
    print(f"  块 {i}: start={start}, end={end}")
    try:
        data = json.loads(json_str)
        print(f"    ✓ JSON解析成功")
        print(f"    img_b64长度: {len(data.get('img_b64', ''))}")
        print(f"    format: {data.get('format')}")
    except Exception as e:
        print(f"    ✗ JSON解析失败: {e}")

# 测试2
print("\n测试2: 超长Base64字符串 (10000字符)")
blocks_2 = DocumentGenerator._extract_svg_json_blocks(test_text_2)
print(f"找到 {len(blocks_2)} 个SVG JSON块")
for i, (start, end, json_str) in enumerate(blocks_2, 1):
    print(f"  块 {i}: start={start}, end={end}")
    try:
        data = json.loads(json_str)
        print(f"    ✓ JSON解析成功")
        print(f"    img_b64长度: {len(data.get('img_b64', ''))}")
        print(f"    format: {data.get('format')}")
        # 验证Base64是否完整
        if data.get('img_b64') == long_b64:
            print(f"    ✓ Base64字符串完整匹配")
        else:
            print(f"    ✗ Base64字符串不匹配")
    except Exception as e:
        print(f"    ✗ JSON解析失败: {e}")

# 测试3
print("\n测试3: 没有【图形】标记")
blocks_3 = DocumentGenerator._extract_svg_json_blocks(test_text_3)
print(f"找到 {len(blocks_3)} 个SVG JSON块")
for i, (start, end, json_str) in enumerate(blocks_3, 1):
    print(f"  块 {i}: start={start}, end={end}")
    try:
        data = json.loads(json_str)
        print(f"    ✓ JSON解析成功")
        print(f"    img_b64长度: {len(data.get('img_b64', ''))}")
        print(f"    format: {data.get('format')}")
    except Exception as e:
        print(f"    ✗ JSON解析失败: {e}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

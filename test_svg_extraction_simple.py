#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简化的SVG JSON提取测试"""

import json

def extract_svg_json_blocks(text: str):
    """
    提取文本中的SVG JSON块
    返回: [(start, end, json_string), ...]
    """
    results = []
    i = 0
    while i < len(text):
        # 寻找可能的JSON开始
        marker_pos = text.find('【图形】', i)
        if marker_pos != -1:
            # 跳过【图形】后的空白，找到 {
            j = marker_pos + 4  # len('【图形】') = 4
            while j < len(text) and text[j].isspace():
                j += 1
            if j < len(text) and text[j] == '{':
                start_pos = marker_pos
                json_start = j
            else:
                i = marker_pos + 1
                continue
        else:
            # 没有标记，查找包含 "img_b64" 的 JSON
            json_start = text.find('"img_b64"', i)
            if json_start == -1:
                break
            # 向前查找最近的 {
            brace_pos = text.rfind('{', i, json_start)
            if brace_pos == -1:
                i = json_start + 1
                continue
            start_pos = brace_pos
            json_start = brace_pos

        # 从 { 开始，找到匹配的 }
        brace_count = 0
        in_string = False
        escape = False
        json_end = -1

        for k in range(json_start, len(text)):
            char = text[k]

            if escape:
                escape = False
                continue

            if char == '\\':
                escape = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = k + 1
                        break

        if json_end == -1:
            # 没有找到匹配的 }
            i = json_start + 1
            continue

        # 提取JSON字符串
        json_str = text[json_start:json_end]

        # 验证是否是SVG JSON
        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and 'img_b64' in data and data.get('format', '').lower() == 'svg':
                results.append((start_pos, json_end, json_str))
                i = json_end
            else:
                i = json_start + 1
        except json.JSONDecodeError:
            i = json_start + 1

    return results


# 测试用例
print("=" * 80)
print("测试SVG JSON提取功能")
print("=" * 80)

# 测试1: 短Base64字符串
print("\n测试1: 短Base64字符串")
test_text_1 = '''【图形】
{"img_b64": "PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCI+PGNpcmNsZSBjeD0iNTAiIGN5PSI1MCIgcj0iNDAiLz48L3N2Zz4=", "format": "svg"}

这是一些文字。
'''
blocks_1 = extract_svg_json_blocks(test_text_1)
print(f"找到 {len(blocks_1)} 个SVG JSON块")
for i, (start, end, json_str) in enumerate(blocks_1, 1):
    print(f"  块 {i}: start={start}, end={end}, JSON长度={len(json_str)}")
    try:
        data = json.loads(json_str)
        print(f"    ✓ JSON解析成功")
        print(f"    img_b64长度: {len(data.get('img_b64', ''))}")
        print(f"    format: {data.get('format')}")
    except Exception as e:
        print(f"    ✗ JSON解析失败: {e}")

# 测试2: 超长Base64字符串 (10000字符)
print("\n测试2: 超长Base64字符串 (10000字符)")
long_b64 = "A" * 10000
test_text_2 = '【图形】\n' + '{"img_b64": "' + long_b64 + '", "format": "svg"}\n\n这是一些文字。\n'
blocks_2 = extract_svg_json_blocks(test_text_2)
print(f"找到 {len(blocks_2)} 个SVG JSON块")
for i, (start, end, json_str) in enumerate(blocks_2, 1):
    print(f"  块 {i}: start={start}, end={end}, JSON长度={len(json_str)}")
    try:
        data = json.loads(json_str)
        print(f"    ✓ JSON解析成功")
        print(f"    img_b64长度: {len(data.get('img_b64', ''))}")
        print(f"    format: {data.get('format')}")
        # 验证Base64是否完整
        if data.get('img_b64') == long_b64:
            print(f"    ✓ Base64字符串完整匹配")
        else:
            print(f"    ✗ Base64字符串不匹配 (期望{len(long_b64)}, 实际{len(data.get('img_b64', ''))})")
    except Exception as e:
        print(f"    ✗ JSON解析失败: {e}")

# 测试3: 没有【图形】标记
print("\n测试3: 没有【图形】标记")
test_text_3 = '前面的文字\n{"img_b64": "' + long_b64 + '", "format": "svg"}\n后面的文字\n'
blocks_3 = extract_svg_json_blocks(test_text_3)
print(f"找到 {len(blocks_3)} 个SVG JSON块")
for i, (start, end, json_str) in enumerate(blocks_3, 1):
    print(f"  块 {i}: start={start}, end={end}, JSON长度={len(json_str)}")
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

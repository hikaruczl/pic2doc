#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立测试脚本 - 验证三个问题的修复
不需要完整的依赖环境
"""

import re

print("\n" + "="*70)
print("问题修复验证测试 (独立版本)")
print("="*70)

# ============================================================================
# 测试1: Prime符号标准化
# ============================================================================
print("\n" + "-"*70)
print("测试1: f'(x) 不应变成 f'}(x)")
print("-"*70)

def normalize_inline_latex(latex: str) -> str:
    """将形如 f' 或 f'' 等用 prime 表示的记号转换为标准LaTeX"""
    def repl(match: re.Match) -> str:
        base = match.group(1)
        primes = match.group(2)
        prime_str = "\\\\prime" * len(primes)
        return f"{base}^{{{prime_str}}}"

    converted = re.sub(r"([A-Za-z])('{1,4})(?![a-zA-Z])", repl, latex)
    return converted

test_cases_1 = [
    ("f'(x) = 1", "f^{\\\\prime}(x) = 1"),
    ("f''(x) = 2", "f^{\\\\prime\\\\prime}(x) = 2"),
    ("f'(x) + g'(x)", "f^{\\\\prime}(x) + g^{\\\\prime}(x)"),
    ("f'(x) = 1 - \\\\frac{1}{2}x", "f^{\\\\prime}(x) = 1 - \\\\frac{1}{2}x"),
]

test1_passed = 0
test1_total = len(test_cases_1)

for input_latex, expected_output in test_cases_1:
    result = normalize_inline_latex(input_latex)
    if result == expected_output:
        print(f"✓ '{input_latex}' → '{result}'")
        test1_passed += 1
    else:
        print(f"✗ '{input_latex}'")
        print(f"  预期: {expected_output}")
        print(f"  实际: {result}")

print(f"\n结果: {test1_passed}/{test1_total} 通过")

# ============================================================================
# 测试2: LLM输出预处理
# ============================================================================
print("\n" + "-"*70)
print("测试2: 修复整段文本被识别为公式")
print("-"*70)

def preprocess_llm_output(content: str) -> str:
    """预处理LLM输出，修复常见的格式问题"""
    def fix_wrapped_content(match):
        inner = match.group(1)

        has_env = any(env in inner for env in [
            r'\\begin{aligned}', r'\\begin{gathered}',
            r'\\begin{array}', r'\\begin{cases}'
        ])

        if not has_env:
            return match.group(0)

        env_pattern = r'(\\\\begin\\{(?:aligned|gathered|array|cases)\\}.*?\\\\end\\{(?:aligned|gathered|array|cases)\\})'
        parts = re.split(env_pattern, inner, flags=re.DOTALL)

        result = []
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue

            if i % 2 == 1:
                result.append(f"$${part}$$")
            else:
                part = part.strip('$').strip()
                if part:
                    result.append(part)

        return '\\n\\n'.join(result) if result else match.group(0)

    pattern = r'(?<!\\$)\\$(?!\\$)((?:[^$]|\\$(?!\\$))*?\\\\begin\\{(?:aligned|gathered|array|cases)\\}.*?)(?<!\\$)\\$(?!\\$)'
    content = re.sub(pattern, fix_wrapped_content, content, flags=re.DOTALL)
    return content

# 模拟LLM错误输出
test_input_2 = """$
\\begin{aligned}
& (5)\\ f(x)=\\frac{1}{2}x^{2}\\ln x \\\\
& \\text { 解: 由题知, } x \\in(0,+\\infty)
\\end{aligned}
$"""

print("原始输入(模拟LLM输出):")
print(test_input_2[:100] + "...")

result_2 = preprocess_llm_output(test_input_2)

print("\n处理后:")
print(result_2[:200])

if "$$" in result_2 and result_2.count("$$") >= 2:
    print("\n✓ 成功: 错误的单$已转换为双$$格式")
    test2_passed = True
else:
    print("\n✗ 失败: 未能正确转换格式")
    test2_passed = False

# ============================================================================
# 测试3: 重叠检测
# ============================================================================
print("\n" + "-"*70)
print("测试3: 重叠内容检测和移除")
print("-"*70)

def trim_overlap_text(existing: str, new_content: str, max_overlap: int = 2000,
                     min_overlap: int = 50) -> str:
    """去除与已合并文本重复的前缀"""
    if not new_content:
        return ""

    candidate = new_content.lstrip()
    if not candidate:
        return ""

    if not existing:
        return candidate

    def normalize_for_comparison(text: str) -> str:
        text = re.sub(r'[ \\t]+', ' ', text)
        text = re.sub(r'\\n{3,}', '\\n\\n', text)
        return text.strip()

    existing_normalized = normalize_for_comparison(existing)
    candidate_normalized = normalize_for_comparison(candidate)

    if candidate_normalized in existing_normalized:
        return ""

    existing_tail = existing_normalized[-max_overlap:]
    max_len = min(len(existing_tail), len(candidate_normalized))

    best_overlap_len = 0
    for overlap in range(max_len, min_overlap - 1, -1):
        suffix = existing_tail[-overlap:]
        prefix = candidate_normalized[:overlap]

        if suffix == prefix:
            best_overlap_len = overlap
            break

        if overlap >= min_overlap * 1.2:
            similarity = sum(c1 == c2 for c1, c2 in zip(suffix, prefix)) / overlap
            if similarity > 0.80:
                best_overlap_len = overlap
                break

    if best_overlap_len > 0:
        remaining_normalized = candidate_normalized[best_overlap_len:].lstrip()

        if not remaining_normalized:
            return ""

        search_prefix = remaining_normalized[:min(50, len(remaining_normalized))]
        remaining_start = candidate.find(search_prefix)

        if remaining_start > 0:
            return candidate[remaining_start:].lstrip()
        else:
            ratio = best_overlap_len / len(candidate_normalized) if len(candidate_normalized) > 0 else 0
            cut_pos = int(len(candidate) * ratio)
            return candidate[cut_pos:].lstrip()

    return candidate

test_cases_3 = [
    (
        "练习2：讨论下列函数的单调性。\\n\\n（1）$f(x)=\\\\frac{e^{-x}}{3}(x^{2}-2x-7)$",
        "（1）$f(x)=\\\\frac{e^{-x}}{3}(x^{2}-2x-7)$\\n\\n解：由题知，$x \\\\in R$",
        True,
        "题号重复"
    ),
    (
        "因为 $x \\\\in(0,+\\\\infty)$ 时，$f''(x)=e^{x}-1>0$，所以函数 $f'(x)$ 在 $(0,+\\\\infty)$ 上单调递增；",
        "因为 $x \\\\in (0,+\\\\infty)$ 时，$f''(x)=e^x-1>0$，所以函数 $f'(x)$ 在 $(0,+\\\\infty)$ 上单调递增；\\n\\n所以 $f'(x) \\\\ge f'(0)=0$",
        True,
        "句子重复"
    ),
]

test3_passed = 0
test3_total = len(test_cases_3)

for i, (existing, new, should_overlap, desc) in enumerate(test_cases_3, 1):
    result = trim_overlap_text(existing, new)
    overlap_removed = len(result) < len(new)

    print(f"\\n测试 3.{i} ({desc}):")
    print(f"  现有末尾: ...{existing[-40:]}")
    print(f"  新开头: {new[:40]}...")
    print(f"  长度: {len(new)} → {len(result)} (移除 {len(new) - len(result)} 字符)")

    if should_overlap and overlap_removed:
        print(f"  ✓ 正确检测并移除重叠")
        test3_passed += 1
    elif not should_overlap and not overlap_removed:
        print(f"  ✓ 正确保留无重叠内容")
        test3_passed += 1
    else:
        print(f"  ✗ 检测结果不符合预期")

print(f"\\n结果: {test3_passed}/{test3_total} 通过")

# ============================================================================
# 总结
# ============================================================================
print("\\n" + "="*70)
print("测试总结")
print("="*70)

all_passed = test1_passed == test1_total and test2_passed and test3_passed == test3_total

print(f"\\n问题1 (Prime符号): {test1_passed}/{test1_total} 通过")
print(f"问题2 (LLM格式): {'✓ 通过' if test2_passed else '✗ 失败'}")
print(f"问题3 (重叠检测): {test3_passed}/{test3_total} 通过")

if all_passed:
    print("\\n" + "="*70)
    print("✓✓✓ 所有测试通过! ✓✓✓")
    print("="*70)
    print("\\n可以使用实际图片进行完整测试。")
else:
    print("\\n" + "="*70)
    print("✗ 部分测试未通过，请检查修复")
    print("="*70)

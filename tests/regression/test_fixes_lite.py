#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试 - 验证重叠内容去除和公式预处理修复
不需要完整的依赖环境
"""

import re


def normalize_for_comparison(text: str) -> str:
    """归一化文本用于重复检测:压缩空白符,但保留换行"""
    # 将多个空格/制表符压缩为单个空格
    text = re.sub(r'[ \t]+', ' ', text)
    # 将多个连续换行压缩为最多两个换行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def trim_overlap_text(existing: str, new_content: str, max_overlap: int = 1500,
                     min_overlap: int = 80) -> str:
    """去除与已合并文本重复的前缀,缓解切片重叠导致的重复"""
    if not new_content:
        return ""

    candidate = new_content.lstrip()
    if not candidate:
        return ""

    if not existing:
        return candidate

    existing_normalized = normalize_for_comparison(existing)
    candidate_normalized = normalize_for_comparison(candidate)

    # 检查完全重复
    if candidate_normalized in existing_normalized:
        return ""

    # 获取尾部用于比较
    existing_tail = existing_normalized[-max_overlap:]
    max_len = min(len(existing_tail), len(candidate_normalized))

    # 尝试找到最长的重叠部分
    best_overlap_len = 0
    for overlap in range(max_len, min_overlap - 1, -1):
        suffix = existing_tail[-overlap:]
        prefix = candidate_normalized[:overlap]

        # 精确匹配
        if suffix == prefix:
            best_overlap_len = overlap
            break

        # 模糊匹配:允许少量差异(如空白符差异)
        # 计算相似度
        if overlap >= min_overlap * 1.5:  # 只对较长的重叠做模糊匹配
            similarity = sum(c1 == c2 for c1, c2 in zip(suffix, prefix)) / overlap
            if similarity > 0.85:  # 85%相似度
                best_overlap_len = overlap
                break

    if best_overlap_len > 0:
        # 在原始文本中找到对应位置(考虑归一化可能改变了长度)
        # 使用归一化后的位置作为参考,在原始文本中找最接近的切分点
        remaining_normalized = candidate_normalized[best_overlap_len:].lstrip()

        # 在原始candidate中找到remaining_normalized的开始位置
        remaining_start = candidate.find(remaining_normalized[:min(50, len(remaining_normalized))])
        if remaining_start > 0:
            return candidate[remaining_start:].lstrip()
        else:
            # 回退:使用归一化长度的比例估算
            ratio = best_overlap_len / len(candidate_normalized) if len(candidate_normalized) > 0 else 0
            cut_pos = int(len(candidate) * ratio)
            return candidate[cut_pos:].lstrip()

    return candidate


def preprocess_aligned_environment(latex: str) -> str:
    """
    预处理aligned环境,将其转换为latex2mathml能处理的格式
    """
    # 匹配aligned环境
    aligned_pattern = r'\\begin\{aligned\}(.*?)\\end\{aligned\}'

    def process_aligned_content(match):
        content = match.group(1)

        # 移除对齐符 &
        content = content.replace('&', '')

        # 将 \\\\ 替换为换行符,然后每行转换为独立的公式
        lines = re.split(r'\\\\\\\\', content)  # 匹配 \\\\
        lines = [line.strip() for line in lines if line.strip()]

        # 如果只有一行或内容较简单,保持原样但移除对齐符
        if len(lines) <= 1:
            return content.replace('&', '').strip()

        # 多行内容:使用gathered环境
        processed_lines = []
        for line in lines:
            line = line.strip()
            if line:
                # 移除行首的对齐符
                line = re.sub(r'^\s*&\s*', '', line)
                processed_lines.append(line)

        # 使用gathered环境(类似aligned但没有对齐符)
        if processed_lines:
            return r'\begin{gathered}' + r'\\'.join(processed_lines) + r'\end{gathered}'
        else:
            return content

    # 替换所有aligned环境
    result = re.sub(aligned_pattern, process_aligned_content, latex, flags=re.DOTALL)

    return result


def test_overlap_removal():
    """测试重叠内容去除功能"""
    print("\n" + "="*60)
    print("测试 1: 重叠内容去除")
    print("="*60)

    # 模拟切片重叠的情况 - 第一段的结尾和第二段的开头重叠
    existing_text = """
这是第一段内容,包含一些数学题目。

解: 由题知, x ∈(0,+∞), f'(x)=x ln x+1/2 x+ln x+1/2=(x+1)(1/2+ln x),

令 f'(x)=0, 因为 x+1>0, 即 1/2+ln x=0, 解得 x=1/√e,

因为 x ∈(0, 1/√e) 时, ln x<-1/2,
    """

    # 第二段从重叠部分开始(模拟图片切片的实际情况)
    new_text = """
因为 x ∈(0, 1/√e) 时, ln x<-1/2, 故 f'(x)<0, 所以函数 f(x) 在 (0, 1/√e) 上单调递减;

因为 x ∈(1/√e,+∞) 时, ln x>-1/2, 故 f'(x)>0, 所以函数 f(x) 在 (1/√e,+∞) 上单调递增.
    """

    result = trim_overlap_text(existing_text, new_text)

    print("\n现有文本(最后100字符):")
    print(repr(existing_text[-100:]))
    print("\n新内容(前100字符):")
    print(repr(new_text[:100]))
    print("\n去除重叠后的结果(前100字符):")
    print(repr(result[:min(100, len(result))]))
    print("\n结果长度:", len(result))

    # 验证重叠部分被移除 - 检查结果是否不再以重叠内容开始
    result_start = result[:50].strip()
    overlap_text = "因为 x ∈(0, 1/√e) 时, ln x<-1/2,"

    # 结果应该跳过重叠部分,从"故 f'(x)<0"开始
    if "故 f'(x)<0" in result[:100] and not result_start.startswith(overlap_text):
        print("\n✓ 测试通过: 重叠内容已成功移除")
        return True
    else:
        print("\n✗ 测试失败: 重叠内容未被移除")
        print(f"  预期: 结果应从'故 f'(x)<0'开始")
        print(f"  实际开始: {result_start}")
        return False


def test_aligned_preprocessing():
    """测试aligned环境预处理"""
    print("\n" + "="*60)
    print("测试 2: Aligned环境预处理")
    print("="*60)

    # 测试包含aligned环境的公式
    test_latex = r"""
\begin{aligned}
& (5)\ f(x)=\frac{1}{2}x^{2}\ln x+x\ln x-\frac{1}{2}x \\
& \text { 解: 由题知, } x \in(0,+\infty),\ f^{\prime}(x)=x \ln x+\frac{1}{2}x+\ln x+\frac{1}{2}=(x+1)\left(\frac{1}{2}+\ln x\right), \\
& \text { 令 } f^{\prime}(x)=0, \text { 因为 } x+1>0
\end{aligned}
    """

    print("\n原始LaTeX:")
    print(test_latex[:200] + "...")

    # 预处理
    preprocessed = preprocess_aligned_environment(test_latex)
    print("\n预处理后的LaTeX:")
    print(preprocessed[:300])

    # 检查是否移除了对齐符&
    has_ampersand = '&' in preprocessed
    has_gathered = 'gathered' in preprocessed
    no_aligned = 'aligned' not in preprocessed

    print(f"\n包含&符号: {has_ampersand}")
    print(f"转换为gathered: {has_gathered}")
    print(f"移除aligned: {no_aligned}")

    if not has_ampersand and has_gathered and no_aligned:
        print("\n✓ 测试通过: aligned环境预处理成功")
        return True
    else:
        print("\n✗ 测试失败: aligned环境预处理未完成")
        return False


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "="*60)
    print("测试 3: 边界情况")
    print("="*60)

    all_passed = True

    # 测试3.1: 完全重复的内容
    print("\n测试 3.1: 完全重复的内容")
    existing = "这是一段文本"
    new = "这是一段文本"
    result = trim_overlap_text(existing, new)
    if result == "":
        print("✓ 通过: 完全重复的内容被正确识别")
    else:
        print("✗ 失败: 完全重复的内容未被识别")
        all_passed = False

    # 测试3.2: 无重叠
    print("\n测试 3.2: 无重叠内容")
    existing = "第一段文本"
    new = "完全不同的第二段文本"
    result = trim_overlap_text(existing, new)
    if result == new.lstrip():
        print("✓ 通过: 无重叠内容保持不变")
    else:
        print("✗ 失败: 无重叠内容被错误修改")
        all_passed = False

    # 测试3.3: 空输入
    print("\n测试 3.3: 空输入")
    result1 = trim_overlap_text("现有文本", "")
    result2 = trim_overlap_text("", "新文本")
    if result1 == "" and result2 == "新文本":
        print("✓ 通过: 空输入处理正确")
    else:
        print("✗ 失败: 空输入处理不正确")
        all_passed = False

    # 测试3.4: 简单aligned环境(单行)
    print("\n测试 3.4: 简单aligned环境")
    simple_aligned = r"\begin{aligned} x = 1 \end{aligned}"
    result = preprocess_aligned_environment(simple_aligned)
    if '&' not in result:
        print("✓ 通过: 简单aligned环境处理正确")
    else:
        print("✗ 失败: 简单aligned环境处理失败")
        all_passed = False

    return all_passed


def main():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# 修复验证测试套件 (轻量级版本)")
    print("# 测试重叠去除和公式预处理逻辑")
    print("#"*60)

    results = []

    # 测试1: 重叠内容去除
    results.append(("重叠内容去除", test_overlap_removal()))

    # 测试2: Aligned预处理
    results.append(("Aligned预处理", test_aligned_preprocessing()))

    # 测试3: 边界情况
    results.append(("边界情况", test_edge_cases()))

    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")

    all_passed = all(result[1] for result in results)

    print("\n" + "="*60)
    if all_passed:
        print("✓✓✓ 所有测试通过! ✓✓✓")
        print("="*60)
        print("\n修复说明:")
        print("1. 重叠内容去除: 使用文本归一化和模糊匹配,更智能地检测重复")
        print("2. Aligned环境: 预处理移除&符号,转换为gathered环境")
        print("3. MathML转换: 增加对mtable元素的支持,正确处理多行公式")
        return 0
    else:
        print("✗✗✗ 部分测试失败! ✗✗✗")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())

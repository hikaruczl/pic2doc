#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 验证重叠内容去除和公式转换修复
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / 'config' / 'config.yaml'

# 确保可以导入项目源码
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.main import AdvancedOCR
from src.formula_converter import FormulaConverter
import yaml


def test_overlap_removal():
    """测试重叠内容去除功能"""
    print("\n" + "="*60)
    print("测试 1: 重叠内容去除")
    print("="*60)

    # 模拟切片重叠的情况
    existing_text = """
这是第一段内容,包含一些数学题目。

解: 由题知, x ∈(0,+∞), f'(x)=x ln x+1/2 x+ln x+1/2=(x+1)(1/2+ln x),

令 f'(x)=0, 因为 x+1>0, 即 1/2+ln x=0, 解得 x=1/√e,

因为 x ∈(0, 1/√e) 时, ln x<-1/2,
    """

    new_text = """
令 f'(x)=0, 因为 x+1>0, 即 1/2+ln x=0, 解得 x=1/√e,

因为 x ∈(0, 1/√e) 时, ln x<-1/2, 故 f'(x)<0, 所以函数 f(x) 在 (0, 1/√e) 上单调递减;

因为 x ∈(1/√e,+∞) 时, ln x>-1/2, 故 f'(x)>0, 所以函数 f(x) 在 (1/√e,+∞) 上单调递增.
    """

    result = AdvancedOCR._trim_overlap_text(existing_text, new_text)

    print("\n现有文本(最后200字符):")
    print(existing_text[-200:])
    print("\n新内容(前200字符):")
    print(new_text[:200])
    print("\n去除重叠后的结果:")
    print(result)

    # 验证重叠部分被移除
    if "令 f'(x)=0" not in result:
        print("\n✓ 测试通过: 重叠内容已成功移除")
        return True
    else:
        print("\n✗ 测试失败: 重叠内容未被移除")
        return False


def test_aligned_formula_conversion():
    """测试aligned环境的公式转换"""
    print("\n" + "="*60)
    print("测试 2: Aligned环境公式转换")
    print("="*60)

    # 加载配置
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    converter = FormulaConverter(config)

    # 测试包含aligned环境的公式
    test_latex = r"""
\begin{aligned}
& (5)\ f(x)=\frac{1}{2}x^{2}\ln x+x\ln x-\frac{1}{2}x \\
& \text { 解: 由题知, } x \in(0,+\infty),\ f^{\prime}(x)=x \ln x+\frac{1}{2}x+\ln x+\frac{1}{2}=(x+1)\left(\frac{1}{2}+\ln x\right), \\
& \text { 令 } f^{\prime}(x)=0, \text { 因为 } x+1>0, \text { 即 } \frac{1}{2}+\ln x=0, \text { 解得 } x=\frac{1}{\sqrt{e}}, \\
& \text { 因为 } x \in\left(0, \frac{1}{\sqrt{e}}\right) \text { 时, } \ln x<-\frac{1}{2}, \text { 故 } f^{\prime}(x)<0, \text { 所以函数 } f(x) \text { 在 }\left(0, \frac{1}{\sqrt{e}}\right) \text { 上单调递减; } \\
& \text { 因为 } x \in\left(\frac{1}{\sqrt{e}},+\infty\right) \text { 时, } \ln x>-\frac{1}{2}, \text { 故 } f^{\prime}(x)>0, \text { 所以函数 } f(x) \text { 在 }\left(\frac{1}{\sqrt{e}},+\infty\right) \text { 上单调递增. }
\end{aligned}
    """

    print("\n原始LaTeX:")
    print(test_latex[:200] + "...")

    # 预处理
    preprocessed = converter._preprocess_latex(test_latex)
    print("\n预处理后的LaTeX:")
    print(preprocessed[:200] + "...")

    # 检查是否移除了对齐符&
    if '&' in preprocessed:
        print("\n✗ 预处理失败: 对齐符&未被移除")
        return False

    # 尝试转换为MathML
    try:
        mathml = converter.convert_latex_to_mathml(test_latex)
        print("\n✓ MathML转换成功!")
        print(f"MathML长度: {len(mathml)} 字符")

        # 检查是否包含有效的MathML结构
        if '<math' in mathml and '</math>' in mathml:
            print("✓ MathML结构有效")
            return True
        else:
            print("✗ MathML结构无效")
            return False

    except Exception as e:
        print(f"\n✗ MathML转换失败: {str(e)}")
        return False


def test_multiple_aligned_formulas():
    """测试多个aligned公式"""
    print("\n" + "="*60)
    print("测试 3: 多个Aligned公式转换")
    print("="*60)

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    converter = FormulaConverter(config)

    test_content = r"""
这里是一些文字说明。

$$\begin{aligned}
& (5)\ f(x)=\frac{1}{2}x^{2}\ln x \\
& \text { 解: } f^{\prime}(x)=x \ln x
\end{aligned}$$

继续一些文字。

$$\begin{aligned}
& (6)\ f(x)=e^{2 x}-3 e^{x}-2 x \\
& \text { 解: } f^{\prime}(x)=2 e^{2 x}-3 e^{x}-2
\end{aligned}$$

结束。
    """

    print("\n测试内容:")
    print(test_content[:150] + "...")

    try:
        # 解析内容
        elements = converter.parse_content(test_content)
        print(f"\n解析出 {len(elements)} 个元素")

        # 统计公式数量
        formula_count = sum(1 for e in elements if e['type'] == 'formula')
        print(f"其中 {formula_count} 个公式")

        # 检查每个公式的MathML
        all_success = True
        for i, element in enumerate(elements):
            if element['type'] == 'formula':
                mathml = element.get('mathml', '')
                if '<math' in mathml and '</math>' in mathml:
                    print(f"✓ 公式 {i+1} 转换成功")
                else:
                    print(f"✗ 公式 {i+1} 转换失败")
                    all_success = False

        if all_success:
            print("\n✓ 所有公式转换成功!")
            return True
        else:
            print("\n✗ 部分公式转换失败")
            return False

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# 修复验证测试套件")
    print("#"*60)

    results = []

    # 测试1: 重叠内容去除
    results.append(("重叠内容去除", test_overlap_removal()))

    # 测试2: Aligned公式转换
    results.append(("Aligned公式转换", test_aligned_formula_conversion()))

    # 测试3: 多个公式
    results.append(("多个Aligned公式", test_multiple_aligned_formulas()))

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
        print("所有测试通过! ✓")
        return 0
    else:
        print("部分测试失败! ✗")
        return 1


if __name__ == '__main__':
    sys.exit(main())

# -*- coding: utf-8 -*-
"""
测试数学符号显示问题
测试三个具体问题:
1. 同时有角标和幂次时显示成两个平铺开
2. 向量符号展开
3. 矩阵符号变小
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.formula_converter import FormulaConverter
from src.document_generator import DocumentGenerator
from docx import Document
import yaml


def test_subscript_superscript():
    """测试同时有下标和上标的情况"""
    print("=" * 80)
    print("问题1: 测试同时有下标和上标")
    print("=" * 80)

    # 加载配置
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    converter = FormulaConverter(config)

    # 测试用例: 同时有下标和上标
    test_cases = [
        ("x_i^2", "变量x，下标i，上标2"),
        ("a_1^n", "变量a，下标1，上标n"),
        ("y_{ij}^{2}", "变量y，下标ij，上标2"),
        ("\\sum_{i=1}^{N}", "求和符号，下标i=1，上标N"),
    ]

    for latex, description in test_cases:
        print(f"\n测试: {description}")
        print(f"LaTeX: {latex}")

        # 转换为MathML
        mathml = converter.convert_latex_to_mathml(latex)
        print(f"MathML长度: {len(mathml)} 字符")
        print(f"MathML预览: {mathml[:200]}...")

        # 检查MathML是否包含正确的标签
        if "msubsup" in mathml:
            print("✓ MathML使用了msubsup（同时下标上标）")
        elif "msub" in mathml and "msup" in mathml:
            print("✗ MathML分别使用了msub和msup（可能导致平铺）")
        else:
            print("? MathML结构未知")

    return True


def test_vector_symbols():
    """测试向量符号"""
    print("\n" + "=" * 80)
    print("问题2: 测试向量符号")
    print("=" * 80)

    # 加载配置
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    converter = FormulaConverter(config)

    # 测试用例: 向量符号
    test_cases = [
        ("\\vec{x}", "向量x"),
        ("\\vec{AB}", "向量AB"),
        ("\\overrightarrow{AB}", "向量AB（箭头形式）"),
        ("\\hat{x}", "单位向量x"),
    ]

    for latex, description in test_cases:
        print(f"\n测试: {description}")
        print(f"LaTeX: {latex}")

        # 转换为MathML
        mathml = converter.convert_latex_to_mathml(latex)
        print(f"MathML长度: {len(mathml)} 字符")
        print(f"MathML预览: {mathml[:300]}...")

        # 检查MathML是否包含正确的标签
        if "mover" in mathml:
            print("✓ MathML使用了mover（上方符号）")
        else:
            print("✗ MathML未使用mover标签")

    return True


def test_matrix_symbols():
    """测试矩阵符号"""
    print("\n" + "=" * 80)
    print("问题3: 测试矩阵符号")
    print("=" * 80)

    # 加载配置
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    converter = FormulaConverter(config)

    # 测试用例: 矩阵
    test_cases = [
        ("\\begin{bmatrix} 1 & 2 \\\\ 3 & 4 \\end{bmatrix}", "2x2矩阵"),
        ("\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}", "2x2矩阵（圆括号）"),
        ("[A]", "矩阵符号简写"),
    ]

    for latex, description in test_cases:
        print(f"\n测试: {description}")
        print(f"LaTeX: {latex}")

        try:
            # 转换为MathML
            mathml = converter.convert_latex_to_mathml(latex)
            print(f"MathML长度: {len(mathml)} 字符")
            print(f"MathML预览: {mathml[:500]}...")

            # 检查MathML是否包含正确的标签
            if "mtable" in mathml:
                print("✓ MathML使用了mtable（表格/矩阵）")
            if "mfenced" in mathml or "mo" in mathml:
                print("✓ MathML包含括号符号")
            else:
                print("? MathML结构未知")
        except Exception as e:
            print(f"✗ 转换失败: {str(e)}")

    return True


def test_omml_conversion():
    """测试OMML转换"""
    print("\n" + "=" * 80)
    print("测试OMML转换（检查document_generator.py的转换逻辑）")
    print("=" * 80)

    # 加载配置
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    converter = FormulaConverter(config)
    doc_gen = DocumentGenerator(config)

    # 测试同时有下标和上标
    latex = "x_i^2"
    print(f"\n测试LaTeX: {latex}")

    mathml = converter.convert_latex_to_mathml(latex)
    print(f"MathML: {mathml[:200]}...")

    # 测试OMML转换
    omml = doc_gen._convert_mathml_to_omml(mathml)
    if omml is not None:
        from lxml import etree
        omml_str = etree.tostring(omml, encoding='unicode', pretty_print=True)
        print(f"\nOMMI输出:")
        print(omml_str[:500])

        # 检查OMML结构
        if "sSubSup" in omml_str or "m:sSubSup" in omml_str:
            print("✓ OMML使用了sSubSup（同时下标上标）")
        elif ("sSub" in omml_str or "m:sSub" in omml_str) and ("sSup" in omml_str or "m:sSup" in omml_str):
            print("✗ OMML分别使用了sSub和sSup（可能导致平铺）")
    else:
        print("✗ OMML转换失败")

    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("数学符号显示问题诊断")
    print("=" * 80 + "\n")

    tests = [
        ("同时有下标和上标", test_subscript_superscript),
        ("向量符号", test_vector_symbols),
        ("矩阵符号", test_matrix_symbols),
        ("OMML转换", test_omml_conversion),
    ]

    for test_name, test_func in tests:
        try:
            test_func()
            print()
        except Exception as e:
            print(f"测试 {test_name} 出现异常: {str(e)}")
            import traceback
            traceback.print_exc()
            print()

    print("=" * 80)
    print("诊断完成")
    print("=" * 80)


if __name__ == "__main__":
    main()

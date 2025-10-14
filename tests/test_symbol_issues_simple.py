# -*- coding: utf-8 -*-
"""
简化的数学符号显示问题诊断
直接测试latex2mathml转换
"""

from latex2mathml.converter import convert as latex_to_mathml


def test_subscript_superscript():
    """测试同时有下标和上标的情况"""
    print("=" * 80)
    print("问题1: 测试同时有下标和上标")
    print("=" * 80)

    # 测试用例: 同时有下标和上标
    test_cases = [
        ("x_i^2", "变量x，下标i，上标2"),
        ("a_1^n", "变量a，下标1，上标n"),
        ("y_{ij}^{2}", "变量y，下标ij，上标2"),
        (r"\sum_{i=1}^{N}", "求和符号，下标i=1，上标N"),
    ]

    for latex, description in test_cases:
        print("\n测试: {}".format(description))
        print("LaTeX: {}".format(latex))

        # 转换为MathML
        try:
            mathml = latex_to_mathml(latex)
            print("MathML长度: {} 字符".format(len(mathml)))
            print("MathML预览: {}...".format(mathml[:200]))

            # 检查MathML是否包含正确的标签
            if "msubsup" in mathml:
                print("✓ MathML使用了msubsup（同时下标上标）")
            elif "msub" in mathml and "msup" in mathml:
                print("✗ MathML分别使用了msub和msup（可能导致平铺）")
            else:
                print("? MathML结构未知")
        except Exception as e:
            print("✗ 转换失败: {}".format(str(e)))

    return True


def test_vector_symbols():
    """测试向量符号"""
    print("\n" + "=" * 80)
    print("问题2: 测试向量符号")
    print("=" * 80)

    # 测试用例: 向量符号
    test_cases = [
        (r"\vec{x}", "向量x"),
        (r"\vec{AB}", "向量AB"),
        (r"\overrightarrow{AB}", "向量AB（箭头形式）"),
        (r"\hat{x}", "单位向量x"),
    ]

    for latex, description in test_cases:
        print("\n测试: {}".format(description))
        print("LaTeX: {}".format(latex))

        try:
            # 转换为MathML
            mathml = latex_to_mathml(latex)
            print("MathML长度: {} 字符".format(len(mathml)))
            print("MathML预览: {}...".format(mathml[:300]))

            # 检查MathML是否包含正确的标签
            if "mover" in mathml:
                print("✓ MathML使用了mover（上方符号）")
            else:
                print("✗ MathML未使用mover标签")
        except Exception as e:
            print("✗ 转换失败: {}".format(str(e)))

    return True


def test_matrix_symbols():
    """测试矩阵符号"""
    print("\n" + "=" * 80)
    print("问题3: 测试矩阵符号")
    print("=" * 80)

    # 测试用例: 矩阵
    test_cases = [
        (r"\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}", "2x2矩阵（方括号）"),
        (r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}", "2x2矩阵（圆括号）"),
        (r"\begin{matrix} 1 & 0 \\ 0 & 1 \end{matrix}", "2x2矩阵（无括号）"),
    ]

    for latex, description in test_cases:
        print("\n测试: {}".format(description))
        print("LaTeX: {}".format(latex))

        try:
            # 转换为MathML
            mathml = latex_to_mathml(latex)
            print("MathML长度: {} 字符".format(len(mathml)))
            print("MathML预览: {}...".format(mathml[:500]))

            # 检查MathML是否包含正确的标签
            if "mtable" in mathml:
                print("✓ MathML使用了mtable（表格/矩阵）")
            if "mfenced" in mathml or ("mo" in mathml and ("[" in mathml or "(" in mathml)):
                print("✓ MathML包含括号符号")
            else:
                print("? MathML结构未知")
        except Exception as e:
            print("✗ 转换失败: {}".format(str(e)))

    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("数学符号显示问题诊断（MathML层面）")
    print("=" * 80 + "\n")

    tests = [
        ("同时有下标和上标", test_subscript_superscript),
        ("向量符号", test_vector_symbols),
        ("矩阵符号", test_matrix_symbols),
    ]

    for test_name, test_func in tests:
        try:
            test_func()
            print()
        except Exception as e:
            print("测试 {} 出现异常: {}".format(test_name, str(e)))
            import traceback
            traceback.print_exc()
            print()

    print("=" * 80)
    print("诊断完成")
    print("=" * 80)


if __name__ == "__main__":
    main()

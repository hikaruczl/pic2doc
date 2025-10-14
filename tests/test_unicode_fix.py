"""
测试Unicode到LaTeX的后处理修复功能
验证 formula_converter 的 Unicode 符号修复
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.formula_converter import FormulaConverter


def test_unicode_to_latex():
    """测试Unicode符号转LaTeX命令"""
    print("=" * 80)
    print("测试 Unicode → LaTeX 转换")
    print("=" * 80)

    config = {}
    converter = FormulaConverter(config)

    # 测试用例
    test_cases = [
        # (输入, 期望输出中应包含的内容, 描述)
        ("求和符号：Σ", r"\sum", "求和符号 Σ"),
        ("求和符号：∑", r"\sum", "求和符号 ∑ (小写)"),
        ("乘积：∏", r"\prod", "乘积符号"),
        ("积分：∫", r"\int", "积分符号"),
        ("根号：√2", r"\sqrt", "根号"),
        ("无穷：∞", r"\infty", "无穷大"),
        ("约等于：x ≈ 3.14", r"\approx", "约等于"),
        ("不等于：a ≠ b", r"\neq", "不等于"),
        ("小于等于：x ≤ 10", r"\leq", "小于等于"),
        ("大于等于：y ≥ 0", r"\geq", "大于等于"),
        ("希腊字母：α, β, γ, δ", r"\alpha.*\beta.*\gamma.*\delta", "希腊字母"),
        ("更多希腊字母：θ, λ, μ, π, σ", r"\theta.*\lambda.*\mu.*\pi.*\sigma", "希腊字母2"),
        ("乘除：2×3÷4", r"\times.*\div", "乘除号"),
        ("正负：±1", r"\pm", "正负号"),
        ("箭头：a→b", r"\rightarrow", "右箭头"),
        ("双箭头：a⇔b", r"\Leftrightarrow", "双向箭头"),
        ("集合符号：x∈S, A⊂B, C∪D", r"\in.*\subset.*\cup", "集合符号"),
        ("逻辑符号：∀x∃y", r"\forall.*\exists", "逻辑符号"),
    ]

    passed = 0
    failed = 0

    for input_text, expected_pattern, description in test_cases:
        result = converter.fix_unicode_to_latex(input_text)

        # 使用正则表达式匹配（允许灵活匹配）
        import re
        if re.search(expected_pattern, result):
            print(f"✓ 通过: {description}")
            print(f"  输入:  {input_text}")
            print(f"  输出:  {result}")
            passed += 1
        else:
            print(f"✗ 失败: {description}")
            print(f"  输入:     {input_text}")
            print(f"  期望包含: {expected_pattern}")
            print(f"  实际输出: {result}")
            failed += 1
        print()

    print("=" * 80)
    print(f"测试结果: {passed}/{len(test_cases)} 通过")
    print("=" * 80)

    return failed == 0


def test_latex_pattern_fixes():
    """测试LaTeX格式修复"""
    print("\n" + "=" * 80)
    print("测试 LaTeX 格式修复")
    print("=" * 80)

    config = {}
    converter = FormulaConverter(config)

    # 测试用例
    test_cases = [
        # (输入, 期望输出中应包含的内容, 描述)
        ("平均值 Ȳ", r"\bar{Y}", "组合字符上划线"),
        ("$Y-$", r"\bar{Y}", "Y- → \\bar{Y}"),
        ("$x-$", r"\bar{x}", "x- → \\bar{x}"),
    ]

    passed = 0
    failed = 0

    for input_text, expected_pattern, description in test_cases:
        result = converter.fix_common_latex_patterns(input_text)

        import re
        if re.search(expected_pattern, result):
            print(f"✓ 通过: {description}")
            print(f"  输入:  {input_text}")
            print(f"  输出:  {result}")
            passed += 1
        else:
            print(f"✗ 失败: {description}")
            print(f"  输入:     {input_text}")
            print(f"  期望包含: {expected_pattern}")
            print(f"  实际输出: {result}")
            failed += 1
        print()

    print("=" * 80)
    print(f"测试结果: {passed}/{len(test_cases)} 通过")
    print("=" * 80)

    return failed == 0


def test_full_post_process():
    """测试完整的后处理流程"""
    print("\n" + "=" * 80)
    print("测试完整后处理流程")
    print("=" * 80)

    config = {}
    converter = FormulaConverter(config)

    # 模拟LLM可能返回的错误输出
    test_input = """
平均值的计算公式：

$$Ȳ = \\frac{Y_1+Y_2+\\cdots+Y_N}{N} = \\frac{1}{N}ΣY_i$$

其中：
- N 是样本数量
- Y_i 是第 i 个观测值
- Ȳ 是平均值

标准差公式：

$$σ = √{\\frac{Σ(x_i-μ)^2}{n}}$$

其中 μ 是总体均值，σ 是标准差。
    """

    print("输入内容:")
    print(test_input)
    print("\n处理中...\n")

    result = converter.post_process_llm_output(test_input)

    print("输出内容:")
    print(result)
    print()

    # 检查关键修复
    checks = [
        (r"\\sum", "Σ → \\sum"),
        (r"\\bar{Y}", "Ȳ → \\bar{Y}"),
        (r"\\sigma", "σ → \\sigma"),
        (r"\\sqrt", "√ → \\sqrt"),
        (r"\\mu", "μ → \\mu"),
    ]

    all_passed = True
    for pattern, description in checks:
        import re
        if re.search(pattern, result):
            print(f"✓ {description}")
        else:
            print(f"✗ {description} (未找到)")
            all_passed = False

    print()
    print("=" * 80)
    if all_passed:
        print("✓ 完整流程测试通过")
    else:
        print("✗ 完整流程测试失败")
    print("=" * 80)

    return all_passed


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("Unicode到LaTeX修复功能测试套件")
    print("=" * 80 + "\n")

    tests = [
        ("Unicode转LaTeX", test_unicode_to_latex),
        ("LaTeX格式修复", test_latex_pattern_fixes),
        ("完整后处理", test_full_post_process),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ 测试 {test_name} 出现异常: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # 打印总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {test_name}")

    print(f"\n总计: {passed}/{total} 测试通过")
    print("=" * 80)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

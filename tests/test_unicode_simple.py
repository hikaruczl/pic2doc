"""
简化的Unicode到LaTeX转换测试
不依赖完整环境，仅测试核心映射逻辑
"""


def test_unicode_mapping():
    """测试Unicode到LaTeX的映射字典"""

    # 从 formula_converter.py 复制的映射
    UNICODE_TO_LATEX = {
        # 数学运算符
        'Σ': r'\sum', '∑': r'\sum',
        'Π': r'\prod', '∏': r'\prod',
        '∫': r'\int',
        '√': r'\sqrt',
        '∞': r'\infty',

        # 关系符号
        '≈': r'\approx',
        '≠': r'\neq',
        '≤': r'\leq', '≥': r'\geq',
        '∈': r'\in',

        # 希腊字母（小写）
        'α': r'\alpha', 'β': r'\beta',
        'γ': r'\gamma', 'δ': r'\delta',
        'θ': r'\theta', 'λ': r'\lambda',
        'μ': r'\mu', 'π': r'\pi',
        'σ': r'\sigma', 'φ': r'\phi',
        'ω': r'\omega',

        # 其他
        '×': r'\times', '÷': r'\div',
        '±': r'\pm',
        '→': r'\rightarrow',
    }

    def fix_unicode(text):
        """简化版的Unicode修复函数"""
        for unicode_char, latex_cmd in UNICODE_TO_LATEX.items():
            if unicode_char in text:
                text = text.replace(unicode_char, latex_cmd)
        return text

    # 测试用例
    tests = [
        ("Σ", r"\sum", "求和符号大写"),
        ("∑", r"\sum", "求和符号小写"),
        ("α", r"\alpha", "希腊字母alpha"),
        ("β", r"\beta", "希腊字母beta"),
        ("π", r"\pi", "希腊字母pi"),
        ("σ", r"\sigma", "希腊字母sigma"),
        ("≈", r"\approx", "约等于"),
        ("≠", r"\neq", "不等于"),
        ("≤", r"\leq", "小于等于"),
        ("≥", r"\geq", "大于等于"),
        ("∞", r"\infty", "无穷大"),
        ("√", r"\sqrt", "根号"),
        ("×", r"\times", "乘号"),
        ("÷", r"\div", "除号"),
        ("→", r"\rightarrow", "右箭头"),
    ]

    print("=" * 70)
    print("Unicode → LaTeX 映射测试")
    print("=" * 70)

    passed = 0
    failed = 0

    for input_char, expected_latex, description in tests:
        result = fix_unicode(input_char)
        if result == expected_latex:
            print(f"✓ {description:20s} | {input_char} → {result}")
            passed += 1
        else:
            print(f"✗ {description:20s} | {input_char} → {result} (期望: {expected_latex})")
            failed += 1

    print("=" * 70)
    print(f"结果: {passed}/{len(tests)} 通过")
    print("=" * 70)
    print()

    return failed == 0


def test_real_world_examples():
    """测试实际场景中的转换"""

    UNICODE_TO_LATEX = {
        'Σ': r'\sum', '∑': r'\sum',
        'Π': r'\prod', '∏': r'\prod',
        '∫': r'\int', '√': r'\sqrt',
        '∞': r'\infty',
        '≈': r'\approx', '≠': r'\neq',
        '≤': r'\leq', '≥': r'\geq',
        '×': r'\times', '÷': r'\div',
        '±': r'\pm',
        'α': r'\alpha', 'β': r'\beta',
        'γ': r'\gamma', 'δ': r'\delta',
        'θ': r'\theta', 'λ': r'\lambda',
        'μ': r'\mu', 'π': r'\pi',
        'σ': r'\sigma', 'φ': r'\phi',
        'ω': r'\omega',
    }

    def fix_unicode(text):
        for unicode_char, latex_cmd in UNICODE_TO_LATEX.items():
            if unicode_char in text:
                text = text.replace(unicode_char, latex_cmd)
        return text

    print("=" * 70)
    print("实际场景测试")
    print("=" * 70)

    examples = [
        (
            "求和公式：Σ(i=1 to N) xi",
            r"\sum(i=1 to N) xi",
            "求和公式"
        ),
        (
            "标准差：σ = √(Σ(xi-μ)²/n)",
            r"\sigma = \sqrt(\sum(xi-\mu)²/n)",
            "标准差公式"
        ),
        (
            "不等式：a ≤ b < c ≥ d",
            r"不等式：a \leq b < c \geq d",
            "不等式"
        ),
        (
            "近似值：π ≈ 3.14159",
            r"近似值：\pi \approx 3.14159",
            "圆周率近似"
        ),
        (
            "积分：∫f(x)dx from 0 to ∞",
            r"积分：\intf(x)dx from 0 to \infty",
            "积分公式"
        ),
    ]

    all_passed = True

    for input_text, expected_output, description in examples:
        result = fix_unicode(input_text)
        passed = (result == expected_output)

        print(f"\n{'✓' if passed else '✗'} {description}")
        print(f"  输入:  {input_text}")
        print(f"  输出:  {result}")
        if not passed:
            print(f"  期望:  {expected_output}")
            all_passed = False

    print("\n" + "=" * 70)
    print(f"{'✓ 所有实际场景测试通过' if all_passed else '✗ 部分测试失败'}")
    print("=" * 70)
    print()

    return all_passed


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("Unicode到LaTeX转换功能测试")
    print("=" * 70)
    print()

    test1_passed = test_unicode_mapping()
    test2_passed = test_real_world_examples()

    print("\n" + "=" * 70)
    print("总体测试结果")
    print("=" * 70)
    print(f"基础映射测试: {'✓ 通过' if test1_passed else '✗ 失败'}")
    print(f"实际场景测试: {'✓ 通过' if test2_passed else '✗ 失败'}")
    print("=" * 70)

    if test1_passed and test2_passed:
        print("\n✓ 所有测试通过！Unicode到LaTeX转换功能正常工作。")
        return True
    else:
        print("\n✗ 部分测试失败，需要检查映射逻辑。")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

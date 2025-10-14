"""
测试数学符号识别的准确性
特别关注求和符号、平均数符号和分数的识别
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import AdvancedOCR
import re


def test_summation_recognition():
    """测试求和符号识别"""
    # 预期的LaTeX模式
    summation_patterns = [
        r'\\sum_\{[^}]+\}\^?\{[^}]*\}',  # \sum_{i=1}^{N}
        r'\\sum_\{[^}]+\}',               # \sum_{i=1}
        r'\\sum\^?\{[^}]*\}',             # \sum^{N}
    ]

    print("=" * 80)
    print("测试求和符号识别")
    print("=" * 80)

    # 这里需要一个包含求和符号的测试图片
    test_image = "tests/sample_images/summation_test.png"

    if not os.path.exists(test_image):
        print(f"警告: 测试图片 {test_image} 不存在，跳过测试")
        return False

    ocr = AdvancedOCR()
    result = ocr.process_image(test_image)

    if not result['success']:
        print(f"错误: OCR处理失败 - {result['error']}")
        return False

    content = result.get('content', '')

    # 检查是否包含求和符号
    found_summation = False
    for pattern in summation_patterns:
        if re.search(pattern, content):
            print(f"✓ 找到求和符号: {pattern}")
            found_summation = True
            break

    if not found_summation:
        print("✗ 未找到正确的求和符号格式")
        print(f"内容预览:\n{content[:500]}")
        return False

    return True


def test_mean_symbol_recognition():
    """测试平均值符号识别"""
    # 预期的LaTeX模式
    mean_patterns = [
        r'\\bar\{[^}]+\}',       # \bar{Y}
        r'\\overline\{[^}]+\}',  # \overline{Y}
    ]

    print("=" * 80)
    print("测试平均值符号识别")
    print("=" * 80)

    test_image = "tests/sample_images/mean_test.png"

    if not os.path.exists(test_image):
        print(f"警告: 测试图片 {test_image} 不存在，跳过测试")
        return False

    ocr = AdvancedOCR()
    result = ocr.process_image(test_image)

    if not result['success']:
        print(f"错误: OCR处理失败 - {result['error']}")
        return False

    content = result.get('content', '')

    # 检查是否包含平均值符号
    found_mean = False
    for pattern in mean_patterns:
        if re.search(pattern, content):
            print(f"✓ 找到平均值符号: {pattern}")
            found_mean = True
            break

    if not found_mean:
        print("✗ 未找到正确的平均值符号格式")
        print(f"内容预览:\n{content[:500]}")
        return False

    return True


def test_fraction_recognition():
    """测试分数识别"""
    # 预期的LaTeX模式
    fraction_pattern = r'\\frac\{[^}]+\}\{[^}]+\}'

    print("=" * 80)
    print("测试分数识别")
    print("=" * 80)

    test_image = "tests/sample_images/fraction_test.png"

    if not os.path.exists(test_image):
        print(f"警告: 测试图片 {test_image} 不存在，跳过测试")
        return False

    ocr = AdvancedOCR()
    result = ocr.process_image(test_image)

    if not result['success']:
        print(f"错误: OCR处理失败 - {result['error']}")
        return False

    content = result.get('content', '')

    # 检查是否包含分数
    if re.search(fraction_pattern, content):
        print(f"✓ 找到分数格式: \\frac{{}}{{}} ")
        return True
    else:
        print("✗ 未找到正确的分数格式")
        print(f"内容预览:\n{content[:500]}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("数学符号识别测试套件")
    print("=" * 80 + "\n")

    tests = [
        ("求和符号识别", test_summation_recognition),
        ("平均值符号识别", test_mean_symbol_recognition),
        ("分数识别", test_fraction_recognition),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print()
        except Exception as e:
            print(f"测试 {test_name} 出现异常: {str(e)}")
            results.append((test_name, False))
            print()

    # 打印总结
    print("=" * 80)
    print("测试总结")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {test_name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

# -*- coding: utf-8 -*-
"""
测试 lxml 修复
"""
import sys
from pathlib import Path
import yaml
import logging

# 设置日志级别为DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / 'config' / 'config.yaml'

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.document_generator import DocumentGenerator
from src.formula_converter import FormulaConverter
from docx import Document

# 加载配置
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 创建实例
doc_gen = DocumentGenerator(config)
formula_converter = FormulaConverter(config)

# 测试公式
test_formulas = [
    ("x^2 + y^2 = z^2", "inline"),
    ("\\frac{a}{b}", "display"),
    ("E = mc^2", "inline"),
]

print("=" * 80)
print("测试lxml修复")
print("=" * 80)

success_count = 0
fail_count = 0

for latex, formula_type in test_formulas:
    print(f"\n测试公式: {latex} ({formula_type})")
    print("-" * 40)
    
    try:
        # 1. 转换LaTeX到MathML
        mathml = formula_converter.convert_latex_to_mathml(latex)
        print(f"✓ MathML转换成功 (长度: {len(mathml)})")
        
        # 2. 转换MathML到OMML
        omml_element = doc_gen._convert_mathml_to_omml(mathml)
        
        if omml_element is not None:
            from lxml import etree
            # 检查类型
            if isinstance(omml_element, etree._Element):
                print(f"✓ OMML元素类型正确: lxml.etree._Element")
                print(f"✓ OMML子元素数量: {len(list(omml_element))}")
                success_count += 1
            else:
                print(f"✗ OMML元素类型错误: {type(omml_element)}")
                fail_count += 1
        else:
            print(f"✗ OMML转换失败")
            fail_count += 1
            
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        fail_count += 1

print("\n" + "=" * 80)
print(f"测试完成: {success_count} 成功, {fail_count} 失败")
print("=" * 80)

if fail_count == 0:
    print("\n✓ 所有测试通过! lxml修复生效")
    sys.exit(0)
else:
    print(f"\n✗ {fail_count} 个测试失败")
    sys.exit(1)

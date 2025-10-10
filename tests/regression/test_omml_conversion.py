# -*- coding: utf-8 -*-
"""
测试 MathML 到 OMML 转换
"""
from xml.etree import ElementTree as ET

def qn(tag):
    """Quick Name - 添加命名空间"""
    namespace = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
    return f'{{{namespace}}}{tag}'

def test_mathml_to_omml():
    """测试简单的 MathML 到 OMML 转换"""
    
    # 简单的 MathML 例子
    test_cases = [
        # 简单数字
        '<math><mn>42</mn></math>',
        # 变量
        '<math><mi>x</mi></math>',
        # 简单表达式
        '<math><mrow><mi>x</mi><mo>+</mo><mn>2</mn></mrow></math>',
        # 分数
        '<math><mfrac><mn>1</mn><mn>2</mn></mfrac></math>',
        # 上标
        '<math><msup><mi>x</mi><mn>2</mn></msup></math>',
        # 平方根
        '<math><msqrt><mi>x</mi></msqrt></math>',
    ]
    
    print("测试 MathML 到 OMML 转换")
    print("=" * 60)
    
    for i, mathml in enumerate(test_cases, 1):
        print(f"\n测试 {i}:")
        print(f"MathML: {mathml}")
        
        try:
            # 解析 MathML
            root = ET.fromstring(mathml)
            
            # 创建 OMML
            omath = ET.Element(qn('oMath'))
            
            # 简单转换
            convert_element(root, omath)
            
            # 输出结果
            omml_str = ET.tostring(omath, encoding='unicode')
            print(f"✓ 转换成功")
            print(f"OMML: {omml_str[:200]}...")
            
        except Exception as e:
            print(f"✗ 转换失败: {str(e)}")
            import traceback
            traceback.print_exc()

def convert_element(mathml_elem, omml_parent):
    """简单的元素转换"""
    tag = mathml_elem.tag.split('}')[-1] if '}' in mathml_elem.tag else mathml_elem.tag
    
    if tag == 'math':
        for child in mathml_elem:
            convert_element(child, omml_parent)
    
    elif tag == 'mrow':
        for child in mathml_elem:
            convert_element(child, omml_parent)
    
    elif tag in ['mi', 'mn', 'mo']:
        r = ET.SubElement(omml_parent, qn('r'))
        t = ET.SubElement(r, qn('t'))
        t.text = mathml_elem.text or ''
    
    elif tag == 'mfrac':
        f = ET.SubElement(omml_parent, qn('f'))
        num = ET.SubElement(f, qn('num'))
        den = ET.SubElement(f, qn('den'))
        
        children = list(mathml_elem)
        if len(children) >= 2:
            convert_element(children[0], num)
            convert_element(children[1], den)
    
    elif tag == 'msup':
        ssup = ET.SubElement(omml_parent, qn('sSup'))
        e = ET.SubElement(ssup, qn('e'))
        sup = ET.SubElement(ssup, qn('sup'))
        
        children = list(mathml_elem)
        if len(children) >= 2:
            convert_element(children[0], e)
            convert_element(children[1], sup)
    
    elif tag == 'msqrt':
        rad = ET.SubElement(omml_parent, qn('rad'))
        radPr = ET.SubElement(rad, qn('radPr'))
        degHide = ET.SubElement(radPr, qn('degHide'))
        degHide.set(qn('val'), '1')
        e = ET.SubElement(rad, qn('e'))
        
        for child in mathml_elem:
            convert_element(child, e)

if __name__ == '__main__':
    test_mathml_to_omml()
    print("\n" + "=" * 60)
    print("测试完成")

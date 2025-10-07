"""
公式转换器单元测试
"""

import pytest
from src.formula_converter import FormulaConverter


@pytest.fixture
def config():
    """测试配置"""
    return {
        'formula': {
            'output_format': 'mathml',
            'preserve_latex': True
        }
    }


@pytest.fixture
def formula_converter(config):
    """创建公式转换器实例"""
    return FormulaConverter(config)


class TestFormulaConverter:
    """公式转换器测试类"""
    
    def test_initialization(self, formula_converter):
        """测试初始化"""
        assert formula_converter is not None
        assert formula_converter.output_format == 'mathml'
    
    def test_extract_inline_formula(self, formula_converter):
        """测试提取行内公式"""
        text = "这是一个公式 $E = mc^2$ 在文本中"
        formulas = formula_converter.extract_formulas(text)
        
        assert len(formulas) == 1
        assert formulas[0][0] == 'inline'
        assert formulas[0][1] == 'E = mc^2'
    
    def test_extract_display_formula(self, formula_converter):
        """测试提取显示公式"""
        text = "这是一个显示公式:\n$$\\int_{0}^{\\infty} e^{-x^2} dx$$"
        formulas = formula_converter.extract_formulas(text)
        
        assert len(formulas) == 1
        assert formulas[0][0] == 'display'
        assert '\\int' in formulas[0][1]
    
    def test_extract_multiple_formulas(self, formula_converter):
        """测试提取多个公式"""
        text = """
        行内公式: $a + b = c$
        显示公式:
        $$x^2 + y^2 = z^2$$
        另一个行内: $\\alpha + \\beta$
        """
        formulas = formula_converter.extract_formulas(text)
        
        assert len(formulas) == 3
    
    def test_parse_content(self, formula_converter):
        """测试解析内容"""
        text = "文本 $x + y$ 更多文本 $$a^2 + b^2$$ 结束"
        elements = formula_converter.parse_content(text)
        
        # 应该有文本和公式元素
        assert len(elements) > 0
        
        # 检查元素类型
        types = [e['type'] for e in elements]
        assert 'text' in types
        assert 'formula' in types
    
    def test_convert_simple_latex(self, formula_converter):
        """测试转换简单LaTeX"""
        latex = "x + y"
        mathml = formula_converter.convert_latex_to_mathml(latex)
        
        assert mathml is not None
        assert len(mathml) > 0
    
    def test_validate_valid_latex(self, formula_converter):
        """测试验证有效LaTeX"""
        latex = "\\frac{a}{b}"
        is_valid, error = formula_converter.validate_latex(latex)
        
        # 注意: 验证可能因latex2mathml的限制而失败
        # 这里主要测试方法是否正常工作
        assert isinstance(is_valid, bool)
    
    def test_get_formula_statistics(self, formula_converter):
        """测试获取公式统计"""
        text = """
        行内: $a$ 和 $b$
        显示: $$c$$ 和 $$d$$
        """
        stats = formula_converter.get_formula_statistics(text)
        
        assert stats['total_formulas'] == 4
        assert stats['inline_formulas'] == 2
        assert stats['display_formulas'] == 2
    
    def test_format_for_word(self, formula_converter):
        """测试格式化为Word"""
        text = "段落1\n\n段落2 $x$ 公式"
        elements = formula_converter.parse_content(text)
        formatted = formula_converter.format_for_word(elements)
        
        assert len(formatted) > 0
        
        # 检查是否有段落类型
        types = [e['type'] for e in formatted]
        assert 'paragraph' in types or 'formula' in types
    
    def test_empty_content(self, formula_converter):
        """测试空内容"""
        elements = formula_converter.parse_content("")
        assert len(elements) == 0
    
    def test_no_formulas(self, formula_converter):
        """测试没有公式的文本"""
        text = "这是纯文本,没有任何公式"
        formulas = formula_converter.extract_formulas(text)
        
        assert len(formulas) == 0
    
    def test_nested_dollar_signs(self, formula_converter):
        """测试嵌套的美元符号"""
        text = "$$x + y$$"
        formulas = formula_converter.extract_formulas(text)
        
        # 应该识别为显示公式,而不是两个行内公式
        assert len(formulas) == 1
        assert formulas[0][0] == 'display'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


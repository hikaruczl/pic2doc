"""
公式格式转换模块
将LaTeX公式转换为Office Math ML格式
"""

import re
import logging
from typing import List, Tuple, Dict, Optional
from latex2mathml.converter import convert as latex_to_mathml

logger = logging.getLogger(__name__)


class FormulaConverter:
    """公式转换器类"""
    
    # LaTeX公式匹配模式
    DISPLAY_FORMULA_PATTERN = r'\$\$(.*?)\$\$'
    INLINE_FORMULA_PATTERN = r'\$(.*?)\$'
    
    def __init__(self, config: dict):
        """
        初始化公式转换器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.output_format = config.get('formula', {}).get('output_format', 'mathml')
        self.preserve_latex = config.get('formula', {}).get('preserve_latex', True)
        
        logger.info("FormulaConverter initialized")
    
    def parse_content(self, content: str) -> List[Dict]:
        """
        解析内容,提取文本和公式
        只提取显示公式($$...$$)作为单独元素，行内公式($...$)保留在文本中
        
        Args:
            content: LLM返回的内容
            
        Returns:
            包含文本和公式的结构化列表
        """
        elements = []
        current_pos = 0
        
        # 只查找显示公式 $$...$$
        display_formulas = []
        for match in re.finditer(self.DISPLAY_FORMULA_PATTERN, content, re.DOTALL):
            display_formulas.append({
                'type': 'display',
                'latex': match.group(1).strip(),
                'start': match.start(),
                'end': match.end(),
                'full_match': match.group(0)
            })
        
        # 构建元素列表
        for formula in display_formulas:
            # 添加公式前的文本（包含行内公式）
            if current_pos < formula['start']:
                text = content[current_pos:formula['start']].strip()
                if text:
                    elements.append({
                        'type': 'text',
                        'content': text
                    })
            
            # 添加显示公式
            elements.append({
                'type': 'formula',
                'formula_type': formula['type'],
                'latex': formula['latex'],
                'mathml': self._convert_to_mathml(formula['latex'])
            })
            
            current_pos = formula['end']
        
        # 添加剩余文本（包含行内公式）
        if current_pos < len(content):
            text = content[current_pos:].strip()
            if text:
                elements.append({
                    'type': 'text',
                    'content': text
                })
        
        # 统计行内公式数量
        inline_count = len(re.findall(self.INLINE_FORMULA_PATTERN, content))
        # 排除显示公式中的$
        for formula in display_formulas:
            inline_count -= content[formula['start']:formula['end']].count('$') // 2
        
        logger.info(f"解析完成: {len(elements)} 个元素 ({len(display_formulas)} 个显示公式, {inline_count} 个行内公式保留在文本中)")
        return elements
    
    def _convert_to_mathml(self, latex: str) -> str:
        """
        将LaTeX转换为MathML
        
        Args:
            latex: LaTeX公式字符串
            
        Returns:
            MathML字符串
        """
        try:
            # 预处理LaTeX
            latex_preprocessed = self._preprocess_latex(latex)
            
            # 转换为MathML
            mathml = latex_to_mathml(latex_preprocessed)
            
            logger.debug(f"LaTeX转MathML成功")
            logger.debug(f"  原始LaTeX: {latex[:100]}{'...' if len(latex) > 100 else ''}")
            logger.debug(f"  MathML长度: {len(mathml)} 字符")
            return mathml
            
        except Exception as e:
            logger.error(f"LaTeX转换失败: {latex[:100]}... - {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            # 返回原始LaTeX作为后备
            return f"<math><mtext>{latex}</mtext></math>"
    
    def _preprocess_latex(self, latex: str) -> str:
        """
        预处理LaTeX公式
        
        Args:
            latex: 原始LaTeX字符串
            
        Returns:
            处理后的LaTeX字符串
        """
        # 移除多余的空白
        latex = latex.strip()
        
        # 处理常见的LaTeX命令别名
        replacements = {
            r'\begin{align}': r'\begin{aligned}',
            r'\end{align}': r'\end{aligned}',
            r'\begin{equation}': '',
            r'\end{equation}': '',
            r'\begin{gather}': r'\begin{gathered}',
            r'\end{gather}': r'\end{gathered}',
        }
        
        for old, new in replacements.items():
            latex = latex.replace(old, new)
        
        return latex
    
    def extract_formulas(self, content: str) -> List[Tuple[str, str]]:
        """
        从内容中提取所有公式
        
        Args:
            content: 文本内容
            
        Returns:
            (公式类型, LaTeX) 元组列表
        """
        formulas = []
        
        # 提取显示公式
        for match in re.finditer(self.DISPLAY_FORMULA_PATTERN, content, re.DOTALL):
            formulas.append(('display', match.group(1).strip()))
        
        # 提取行内公式
        for match in re.finditer(self.INLINE_FORMULA_PATTERN, content):
            # 检查是否是显示公式的一部分
            is_display = False
            for display_match in re.finditer(self.DISPLAY_FORMULA_PATTERN, content, re.DOTALL):
                if match.start() >= display_match.start() and match.end() <= display_match.end():
                    is_display = True
                    break
            
            if not is_display:
                formulas.append(('inline', match.group(1).strip()))
        
        return formulas
    
    def convert_latex_to_mathml(self, latex: str) -> str:
        """
        公开的LaTeX到MathML转换方法
        
        Args:
            latex: LaTeX公式
            
        Returns:
            MathML字符串
        """
        return self._convert_to_mathml(latex)
    
    def format_for_word(self, elements: List[Dict]) -> List[Dict]:
        """
        格式化元素以便插入Word文档
        
        Args:
            elements: 解析后的元素列表
            
        Returns:
            格式化后的元素列表
        """
        formatted = []
        
        for element in elements:
            if element['type'] == 'text':
                # 分段处理文本
                paragraphs = element['content'].split('\n\n')
                for para in paragraphs:
                    para = para.strip()
                    if para:
                        formatted.append({
                            'type': 'paragraph',
                            'content': para
                        })
            
            elif element['type'] == 'formula':
                formatted.append({
                    'type': 'formula',
                    'formula_type': element['formula_type'],
                    'latex': element['latex'],
                    'mathml': element['mathml']
                })
        
        return formatted
    
    def validate_latex(self, latex: str) -> Tuple[bool, Optional[str]]:
        """
        验证LaTeX公式
        
        Args:
            latex: LaTeX公式字符串
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 尝试转换
            self._convert_to_mathml(latex)
            return True, None
        except Exception as e:
            return False, str(e)
    
    def get_formula_statistics(self, content: str) -> Dict:
        """
        获取公式统计信息
        
        Args:
            content: 文本内容
            
        Returns:
            统计信息字典
        """
        formulas = self.extract_formulas(content)
        
        display_count = sum(1 for f in formulas if f[0] == 'display')
        inline_count = sum(1 for f in formulas if f[0] == 'inline')
        
        return {
            'total_formulas': len(formulas),
            'display_formulas': display_count,
            'inline_formulas': inline_count,
            'formulas': formulas
        }


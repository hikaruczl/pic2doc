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
        # 预处理：修复LLM可能返回的格式问题
        content = self._preprocess_llm_output(content)

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

    def _preprocess_llm_output(self, content: str) -> str:
        """
        预处理LLM输出，修复常见的格式问题

        Args:
            content: 原始LLM输出

        Returns:
            清理后的内容
        """
        import re

        logger.info("=" * 80)
        logger.info("预处理LLM输出（拆分aligned环境为多行）")
        logger.info("=" * 80)

        # 问题: LLM有时会将整段内容用$$...$$包裹，且内部包含aligned环境
        # 解决: 将aligned环境拆分成多个独立的显示公式（每行一个）

        lines = content.split('\n')
        result_lines = []
        i = 0
        conversion_count = 0

        logger.info(f"原始内容共 {len(lines)} 行")

        # 调试：显示前几行内容
        for idx in range(min(5, len(lines))):
            logger.info(f"  行{idx+1}: [{repr(lines[idx])}]")

        while i < len(lines):
            line = lines[i]

            # 检测$$开头（显示公式标记）
            if line.strip() in ['$', '$$']:
                logger.info(f"✓ 检测到{repr(line.strip())} (行 {i+1})")

                if i + 1 >= len(lines):
                    logger.info(f"  但后面没有内容了，跳过")
                    result_lines.append(line)
                    i += 1
                    continue

                # 向前查找是否有\begin{aligned}
                j = i + 1
                found_begin = False
                found_end = False
                end_pos = -1
                aligned_content_lines = []

                # 查找aligned环境（可能在一行或多行）
                while j < len(lines):
                    current_line = lines[j]

                    # 检查是否包含\begin{aligned}
                    if '\\begin{aligned}' in current_line or '\\begin{gathered}' in current_line:
                        found_begin = True
                        logger.info(f"  ✓ 找到\\begin{{aligned/gathered}} (行 {j+1}): {current_line[:60]}...")

                        # 检查是否在同一行就有\end{aligned}（单行情况）
                        if ('\\end{aligned}' in current_line or '\\end{gathered}' in current_line):
                            logger.info(f"  ✓ 同一行包含\\end{{aligned/gathered}}")
                            # 提取aligned环境内容
                            match = re.search(r'\\begin\{(?:aligned|gathered)\}(.*?)\\end\{(?:aligned|gathered)\}',
                                            current_line, re.DOTALL)
                            if match:
                                aligned_content_lines = [match.group(1)]
                                found_end = True
                                # 查找结束的$或$$
                                k = j + 1
                                while k < len(lines):
                                    if lines[k].strip() in ['$', '$$']:
                                        end_pos = k
                                        logger.info(f"  ✓ 找到结束{repr(lines[k].strip())} (行 {k+1})")
                                        break
                                    k += 1
                                break
                        else:
                            # 多行情况：继续收集
                            j += 1
                            while j < len(lines):
                                if '\\end{aligned}' in lines[j] or '\\end{gathered}' in lines[j]:
                                    found_end = True
                                    logger.info(f"  ✓ 找到\\end{{aligned/gathered}} (行 {j+1})")
                                    # 查找结束的$或$$
                                    k = j + 1
                                    while k < len(lines):
                                        if lines[k].strip() in ['$', '$$']:
                                            end_pos = k
                                            logger.info(f"  ✓ 找到结束{repr(lines[k].strip())} (行 {k+1})")
                                            break
                                        k += 1
                                    break
                                else:
                                    # 收集aligned内容
                                    aligned_content_lines.append(lines[j])
                                j += 1
                            break
                    j += 1

                # 如果找到了完整的 $$...\begin{aligned}...\end{aligned}...$$ 结构
                if found_begin and found_end and end_pos > 0 and aligned_content_lines:
                    logger.info(f"✓✓✓ 成功拆分aligned环境: 行{i+1}到行{end_pos+1}")

                    # 拆分每一行（以 \\ 分隔）
                    full_aligned_content = '\n'.join(aligned_content_lines)
                    logger.info(f"Aligned内容长度: {len(full_aligned_content)} 字符")

                    # 按 \\ 分割
                    parts = re.split(r'\\\\', full_aligned_content)
                    logger.info(f"拆分成 {len(parts)} 部分")

                    for part_idx, part in enumerate(parts):
                        part = part.strip()
                        if not part:
                            logger.debug(f"  跳过空部分 {part_idx+1}")
                            continue

                        # 移除行首的 & 符号
                        part = re.sub(r'^&\s*', '', part)

                        # 每一行作为独立的显示公式
                        result_lines.append('$$')
                        result_lines.append(part)
                        result_lines.append('$$')
                        result_lines.append('')  # 空行分隔

                        logger.info(f"  拆分行 {part_idx+1}: {part[:50]}...")

                    i = end_pos + 1
                    conversion_count += 1
                    continue
                else:
                    logger.info(f"  未找到完整结构: begin={found_begin}, end={found_end}, end_pos={end_pos}, content_lines={len(aligned_content_lines)}")

            result_lines.append(line)
            i += 1

        logger.info(f"预处理完成: 拆分了 {conversion_count} 个aligned环境")
        logger.info("=" * 80)

        return '\n'.join(result_lines)
    
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

        # 检查是否包含aligned环境
        if '\\begin{aligned}' in latex or '\\begin{align}' in latex:
            # aligned环境需要特殊处理
            latex = self._preprocess_aligned_environment(latex)

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

    def _preprocess_aligned_environment(self, latex: str) -> str:
        """
        预处理aligned环境,将其转换为latex2mathml能处理的格式
        aligned环境通常包含 & 对齐符和 \\\\ 换行符,这些在MathML转换中会有问题

        Args:
            latex: 包含aligned环境的LaTeX字符串

        Returns:
            处理后的LaTeX字符串
        """
        import re

        # 匹配aligned环境 - 注意要用非贪婪匹配
        aligned_pattern = r'\\begin\{aligned\}(.*?)\\end\{aligned\}'

        def process_aligned_content(match):
            content = match.group(1)

            # 将 \\\\ 分割行 (在Python字符串中, \\\\ 表示两个反斜杠)
            lines = re.split(r'\\\\', content)
            lines = [line.strip() for line in lines if line.strip()]

            # 如果只有一行,简单处理
            if len(lines) <= 1:
                # 移除对齐符 &
                processed = content.replace('&', '').strip()
                return processed

            # 多行内容:处理每一行并移除对齐符
            processed_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    # 移除所有对齐符 &
                    line = line.replace('&', '')
                    line = line.strip()
                    if line:
                        processed_lines.append(line)

            # 使用gathered环境(类似aligned但没有对齐符)
            # gathered环境对latex2mathml更友好
            if processed_lines:
                # 用 \\\\ 连接各行
                return r'\begin{gathered}' + r'\\'.join(processed_lines) + r'\end{gathered}'
            else:
                return content.replace('&', '').strip()

        # 替换所有aligned环境
        result = re.sub(aligned_pattern, process_aligned_content, latex, flags=re.DOTALL)

        return result
    
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


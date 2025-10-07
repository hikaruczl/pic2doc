"""
Word文档生成模块
使用python-docx生成包含公式的Word文档
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from io import BytesIO

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """Word文档生成器类"""
    
    def __init__(self, config: dict):
        """
        初始化文档生成器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.doc_config = config.get('document', {})
        self.output_dir = config.get('output', {}).get('directory', 'output')
        
        # 确保输出目录存在
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info("DocumentGenerator initialized")
    
    def create_document(self, elements: List[Dict], original_image: Optional[Image.Image] = None,
                       metadata: Optional[Dict] = None) -> Document:
        """
        创建Word文档
        
        Args:
            elements: 格式化的元素列表
            original_image: 原始图像 (可选)
            metadata: 元数据 (可选)
            
        Returns:
            Document对象
        """
        doc = Document()
        
        # 设置文档属性
        self._set_document_properties(doc, metadata)
        
        # 设置页边距
        self._set_page_margins(doc)
        
        # 添加标题
        self._add_title(doc, metadata)
        
        # 添加原始图像 (如果配置允许)
        if original_image and self.doc_config.get('include_original_image', True):
            self._add_original_image(doc, original_image)
        
        # 添加分隔线
        doc.add_paragraph('_' * 50)
        
        # 添加内容元素
        for element in elements:
            self._add_element(doc, element)
        
        # 添加页脚
        self._add_footer(doc, metadata)
        
        logger.info(f"文档创建完成,共 {len(elements)} 个元素")
        return doc
    
    def save_document(self, doc: Document, filename: Optional[str] = None) -> str:
        """
        保存文档到文件
        
        Args:
            doc: Document对象
            filename: 文件名 (可选,默认使用时间戳)
            
        Returns:
            保存的文件路径
        """
        if filename is None:
            # 使用配置的文件名模式
            pattern = self.config.get('output', {}).get('filename_pattern', 
                                                        'math_problem_{timestamp}.docx')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = pattern.format(timestamp=timestamp)
        
        # 确保文件名以.docx结尾
        if not filename.endswith('.docx'):
            filename += '.docx'
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            doc.save(filepath)
            logger.info(f"文档已保存: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存文档失败: {str(e)}")
            raise
    
    def _set_document_properties(self, doc: Document, metadata: Optional[Dict]):
        """设置文档属性"""
        core_properties = doc.core_properties
        core_properties.author = "Advanced OCR System"
        core_properties.title = "Math Problem Analysis"
        
        if metadata:
            if 'title' in metadata:
                core_properties.title = metadata['title']
            if 'author' in metadata:
                core_properties.author = metadata['author']
            if 'subject' in metadata:
                core_properties.subject = metadata['subject']
    
    def _set_page_margins(self, doc: Document):
        """设置页边距"""
        sections = doc.sections
        for section in sections:
            margins = self.doc_config.get('page_margins', {})
            section.top_margin = Inches(margins.get('top', 1.0))
            section.bottom_margin = Inches(margins.get('bottom', 1.0))
            section.left_margin = Inches(margins.get('left', 1.0))
            section.right_margin = Inches(margins.get('right', 1.0))
    
    def _add_title(self, doc: Document, metadata: Optional[Dict]):
        """添加标题"""
        title = "数学问题分析结果"
        if metadata and 'title' in metadata:
            title = metadata['title']
        
        heading = doc.add_heading(title, level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 设置标题字体
        run = heading.runs[0]
        run.font.size = Pt(self.doc_config.get('heading_font_size', 14))
        run.font.name = self.doc_config.get('default_font', 'Arial')
        run.font.color.rgb = RGBColor(0, 0, 0)
    
    def _add_original_image(self, doc: Document, image: Image.Image):
        """添加原始图像"""
        # 添加小标题
        doc.add_heading('原始图像', level=2)
        
        # 保存图像到BytesIO
        img_buffer = BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # 添加图像到文档
        width = self.doc_config.get('image_width_inches', 6.0)
        doc.add_picture(img_buffer, width=Inches(width))
        
        # 添加空行
        doc.add_paragraph()
    
    def _add_element(self, doc: Document, element: Dict):
        """添加单个元素到文档"""
        if element['type'] == 'paragraph':
            self._add_paragraph(doc, element['content'])
        
        elif element['type'] == 'formula':
            self._add_formula(doc, element)
    
    def _add_paragraph(self, doc: Document, text: str):
        """添加段落，支持行内公式"""
        import re
        from latex2mathml.converter import convert as latex_to_mathml
        
        paragraph = doc.add_paragraph()
        
        # 查找所有行内公式 $...$（排除 $$...$$）
        # 使用负向预测和回顾来排除双$
        inline_formula_pattern = r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)'
        last_pos = 0
        
        for match in re.finditer(inline_formula_pattern, text):
            # 添加公式前的文本
            if match.start() > last_pos:
                run = paragraph.add_run(text[last_pos:match.start()])
                run.font.size = Pt(self.doc_config.get('default_font_size', 11))
                run.font.name = self.doc_config.get('default_font', 'Arial')
            
            # 添加行内公式
            latex = match.group(1).strip()
            try:
                mathml = latex_to_mathml(latex)
                self._insert_mathml(paragraph, mathml)
            except Exception as e:
                logger.warning(f"插入行内公式失败，使用文本: {str(e)}")
                # 回退到文本显示
                run = paragraph.add_run(f"${latex}$")
                run.font.name = 'Courier New'
                run.font.size = Pt(10)
            
            last_pos = match.end()
        
        # 添加剩余文本
        if last_pos < len(text):
            run = paragraph.add_run(text[last_pos:])
            run.font.size = Pt(self.doc_config.get('default_font_size', 11))
            run.font.name = self.doc_config.get('default_font', 'Arial')
        
        # 如果段落为空（没有内容），添加文本以避免空段落
        if not paragraph.runs:
            run = paragraph.add_run(text)
            run.font.size = Pt(self.doc_config.get('default_font_size', 11))
            run.font.name = self.doc_config.get('default_font', 'Arial')
    
    def _add_formula(self, doc: Document, element: Dict):
        """添加公式"""
        formula_type = element['formula_type']
        latex = element['latex']
        mathml = element['mathml']
        
        # 创建段落
        paragraph = doc.add_paragraph()
        
        if formula_type == 'display':
            # 居中显示公式
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 尝试插入MathML
        try:
            self._insert_mathml(paragraph, mathml)
        except Exception as e:
            logger.warning(f"插入MathML失败,使用LaTeX文本: {str(e)}")
            logger.debug(f"LaTeX: {latex[:100]}...")
            logger.debug(f"MathML: {mathml[:200]}...")
            # 后备方案:插入LaTeX文本
            run = paragraph.add_run(f"${latex}$" if formula_type == 'inline' else f"$${latex}$$")
            run.font.name = 'Courier New'
            run.font.size = Pt(10)
    
    def _insert_mathml(self, paragraph, mathml: str):
        """
        插入MathML到段落
        
        Args:
            paragraph: 段落对象
            mathml: MathML字符串
        """
        from lxml import etree
        
        # 转换MathML为OMML
        omml_element = self._convert_mathml_to_omml(mathml)
        
        if omml_element is not None:
            # 插入OMML到段落
            run = paragraph.add_run()
            run._element.append(omml_element)
        else:
            raise Exception("MathML to OMML conversion failed")
    
    def _convert_mathml_to_omml(self, mathml: str):
        """
        将MathML转换为OMML (Office Math Markup Language)
        
        Args:
            mathml: MathML字符串
            
        Returns:
            OMML lxml Element对象,如果转换失败返回None
        """
        try:
            from lxml import etree
            
            # 解析MathML
            mathml_clean = mathml.strip()
            if not mathml_clean.startswith('<math'):
                logger.debug(f"MathML格式错误: 不以<math开头")
                return None
            
            # 解析MathML
            try:
                root = etree.fromstring(mathml_clean.encode('utf-8'))
            except Exception as e:
                logger.debug(f"MathML解析失败: {str(e)}")
                return None
            
            # 创建OMML根元素
            MATH_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
            omath = etree.Element('{%s}oMath' % MATH_NS, nsmap={'m': MATH_NS})
            
            # 递归转换MathML元素为OMML
            self._convert_mathml_element_to_omml(root, omath)
            
            logger.debug(f"OMML转换成功: {len(list(omath))} 个子元素")
            return omath
            
        except Exception as e:
            logger.debug(f"MathML到OMML转换失败: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def _convert_mathml_element_to_omml(self, mathml_elem, omml_parent):
        """
        递归转换MathML元素为OMML元素
        
        Args:
            mathml_elem: MathML lxml元素
            omml_parent: OMML lxml父元素
        """
        from lxml import etree
        
        MATH_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
        
        # 获取标签名(去除命名空间)
        tag = mathml_elem.tag.split('}')[-1] if '}' in mathml_elem.tag else mathml_elem.tag
        
        # 处理不同的MathML标签
        if tag == 'math':
            # 根元素,处理子元素
            for child in mathml_elem:
                self._convert_mathml_element_to_omml(child, omml_parent)
        
        elif tag == 'mrow':
            # 行,处理子元素
            for child in mathml_elem:
                self._convert_mathml_element_to_omml(child, omml_parent)
        
        elif tag in ['mi', 'mn', 'mo', 'mtext']:
            # 标识符、数字、运算符、文本
            r = etree.SubElement(omml_parent, '{%s}r' % MATH_NS)
            t = etree.SubElement(r, '{%s}t' % MATH_NS)
            text = mathml_elem.text or ''
            t.text = text
            
        elif tag == 'mfrac':
            # 分数
            f = etree.SubElement(omml_parent, '{%s}f' % MATH_NS)
            num = etree.SubElement(f, '{%s}num' % MATH_NS)
            den = etree.SubElement(f, '{%s}den' % MATH_NS)
            
            children = list(mathml_elem)
            if len(children) >= 2:
                self._convert_mathml_element_to_omml(children[0], num)
                self._convert_mathml_element_to_omml(children[1], den)
        
        elif tag == 'msup':
            # 上标
            ssup = etree.SubElement(omml_parent, '{%s}sSup' % MATH_NS)
            e = etree.SubElement(ssup, '{%s}e' % MATH_NS)
            sup = etree.SubElement(ssup, '{%s}sup' % MATH_NS)
            
            children = list(mathml_elem)
            if len(children) >= 2:
                self._convert_mathml_element_to_omml(children[0], e)
                self._convert_mathml_element_to_omml(children[1], sup)
        
        elif tag == 'msub':
            # 下标
            ssub = etree.SubElement(omml_parent, '{%s}sSub' % MATH_NS)
            e = etree.SubElement(ssub, '{%s}e' % MATH_NS)
            sub = etree.SubElement(ssub, '{%s}sub' % MATH_NS)
            
            children = list(mathml_elem)
            if len(children) >= 2:
                self._convert_mathml_element_to_omml(children[0], e)
                self._convert_mathml_element_to_omml(children[1], sub)
        
        elif tag == 'msqrt':
            # 平方根
            rad = etree.SubElement(omml_parent, '{%s}rad' % MATH_NS)
            radPr = etree.SubElement(rad, '{%s}radPr' % MATH_NS)
            degHide = etree.SubElement(radPr, '{%s}degHide' % MATH_NS)
            degHide.set('{%s}val' % MATH_NS, '1')
            e = etree.SubElement(rad, '{%s}e' % MATH_NS)
            
            for child in mathml_elem:
                self._convert_mathml_element_to_omml(child, e)
        
        elif tag == 'mroot':
            # n次根
            rad = etree.SubElement(omml_parent, '{%s}rad' % MATH_NS)
            deg = etree.SubElement(rad, '{%s}deg' % MATH_NS)
            e = etree.SubElement(rad, '{%s}e' % MATH_NS)
            
            children = list(mathml_elem)
            if len(children) >= 2:
                self._convert_mathml_element_to_omml(children[0], e)
                self._convert_mathml_element_to_omml(children[1], deg)
        
        else:
            # 未处理的标签,尝试处理子元素
            logger.debug(f"未处理的MathML标签: {tag}")
            for child in mathml_elem:
                self._convert_mathml_element_to_omml(child, omml_parent)
    
    def _add_footer(self, doc: Document, metadata: Optional[Dict]):
        """添加页脚"""
        # 添加分隔线
        doc.add_paragraph('_' * 50)
        
        # 添加生成信息
        footer_text = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        if metadata and 'provider' in metadata:
            footer_text += f" | 使用模型: {metadata['provider']}"
        
        footer = doc.add_paragraph(footer_text)
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        run = footer.runs[0]
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(128, 128, 128)
        run.italic = True
    
    def create_from_analysis(self, analysis_result: Dict, original_image: Image.Image,
                            elements: List[Dict]) -> str:
        """
        从分析结果创建并保存文档
        
        Args:
            analysis_result: LLM分析结果
            original_image: 原始图像
            elements: 格式化的元素列表
            
        Returns:
            保存的文件路径
        """
        # 准备元数据
        metadata = {
            'title': '数学问题分析',
            'provider': f"{analysis_result.get('provider', 'unknown')} - {analysis_result.get('model', 'unknown')}",
            'subject': 'Math Problem OCR'
        }
        
        # 创建文档
        doc = self.create_document(elements, original_image, metadata)
        
        # 保存文档
        filepath = self.save_document(doc)
        
        return filepath


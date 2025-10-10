#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格式转换测试脚本
直接输入文本进行公式解析和Word文档生成，用于测试格式转换功能
无需调用LLM API，降低测试成本
"""

import os
import sys
import yaml
import logging
import argparse
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.formula_converter import FormulaConverter
from src.document_generator import DocumentGenerator


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def load_config():
    """加载配置文件"""
    config_path = ROOT_DIR / 'config' / 'config.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_format_conversion(text: str, output_filename: str = None):
    """
    测试格式转换
    
    Args:
        text: 待转换的文本（包含LaTeX公式）
        output_filename: 输出文件名（可选）
    """
    logger = logging.getLogger(__name__)
    
    # 加载配置
    config = load_config()
    
    # 创建转换器
    formula_converter = FormulaConverter(config)
    document_generator = DocumentGenerator(config)
    
    logger.info("=" * 80)
    logger.info("输入文本:")
    logger.info("=" * 80)
    logger.info(text)
    logger.info("=" * 80)
    
    # 解析内容
    logger.info("开始解析内容...")
    elements = formula_converter.parse_content(text)
    
    logger.info(f"解析完成，共 {len(elements)} 个元素:")
    for i, elem in enumerate(elements, 1):
        if elem['type'] == 'text':
            logger.info(f"  {i}. [文本] {elem['content'][:50]}..." if len(elem['content']) > 50 else f"  {i}. [文本] {elem['content']}")
        elif elem['type'] == 'formula':
            logger.info(f"  {i}. [公式-{elem['formula_type']}] {elem['latex'][:50]}..." if len(elem['latex']) > 50 else f"  {i}. [公式-{elem['formula_type']}] {elem['latex']}")
    
    # 格式化为Word文档格式
    logger.info("格式化为Word格式...")
    formatted_elements = formula_converter.format_for_word(elements)
    
    logger.info(f"格式化完成，共 {len(formatted_elements)} 个段落/公式")
    
    # 生成文档
    logger.info("生成Word文档...")
    metadata = {
        'title': '格式转换测试',
        'provider': '测试模式（无LLM调用）',
        'subject': 'Format Conversion Test'
    }
    
    doc = document_generator.create_document(
        elements=formatted_elements,
        original_image=None,
        metadata=metadata
    )
    
    # 保存文档
    if output_filename:
        # 确保文件名有正确的扩展名
        if not output_filename.endswith('.docx'):
            output_filename += '.docx'
        filepath = document_generator.save_document(doc, output_filename)
    else:
        # 使用默认文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'format_test_{timestamp}.docx'
        filepath = document_generator.save_document(doc, filename)
    
    logger.info("=" * 80)
    logger.info(f"✓ 文档生成成功: {filepath}")
    logger.info("=" * 80)
    
    return filepath


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='格式转换测试工具 - 直接测试文本到Word的转换',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 从文件读取文本
  python test_format_conversion.py -f sample_text.txt
  
  # 从文件读取并指定输出文件名
  python test_format_conversion.py -f sample_text.txt -o output.docx
  
  # 直接输入文本
  python test_format_conversion.py -t "这是一个测试公式 $x^2 + y^2 = z^2$"
  
  # 从标准输入读取（支持多行）
  cat sample_text.txt | python test_format_conversion.py
        """
    )
    
    parser.add_argument('-f', '--file', help='从文件读取文本')
    parser.add_argument('-t', '--text', help='直接输入文本')
    parser.add_argument('-o', '--output', help='输出文件名')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 获取输入文本
    text = None
    
    if args.file:
        # 从文件读取
        file_path = args.file
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return 1
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        logger.info(f"从文件读取文本: {file_path}")
    
    elif args.text:
        # 直接使用命令行参数
        text = args.text
        logger.info("使用命令行文本")
    
    elif not sys.stdin.isatty():
        # 从标准输入读取
        text = sys.stdin.read()
        logger.info("从标准输入读取文本")
    
    else:
        # 没有输入
        logger.error("请提供输入文本！使用 -h 查看帮助")
        return 1
    
    if not text or not text.strip():
        logger.error("输入文本为空！")
        return 1
    
    # 执行测试
    try:
        test_format_conversion(text, args.output)
        return 0
    except Exception as e:
        logger.error(f"转换失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main())

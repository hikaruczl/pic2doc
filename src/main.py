"""
主程序入口
整合所有模块,实现完整的工作流程
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

import yaml
from dotenv import load_dotenv
import colorlog

from .image_processor import ImageProcessor
from .llm_client import LLMClient
from .formula_converter import FormulaConverter
from .document_generator import DocumentGenerator


class AdvancedOCR:
    """高级OCR主类"""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        初始化AdvancedOCR
        
        Args:
            config_path: 配置文件路径
        """
        # 加载环境变量
        load_dotenv()
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 设置日志
        self._setup_logging()
        
        # 初始化组件
        self.image_processor = ImageProcessor(self.config)
        self.llm_client = LLMClient(self.config, self.image_processor)
        self.formula_converter = FormulaConverter(self.config)
        self.document_generator = DocumentGenerator(self.config)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("AdvancedOCR系统初始化完成")
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            # 返回默认配置
            return {}
    
    def _setup_logging(self):
        """设置日志系统"""
        log_config = self.config.get('logging', {})
        log_level = os.getenv('LOG_LEVEL', log_config.get('level', 'INFO'))
        log_dir = os.getenv('LOG_DIR', self.config.get('output', {}).get('directory', 'logs'))
        
        # 创建日志目录
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # 设置日志格式
        log_format = log_config.get('format', 
                                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 创建彩色日志格式器
        color_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 控制台处理器
        if log_config.get('console_output', True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(color_formatter)
            root_logger.addHandler(console_handler)
        
        # 文件处理器
        log_file = os.path.join(log_dir, f'advanceocr_{datetime.now().strftime("%Y%m%d")}.log')
        
        if log_config.get('file_rotation', True):
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=log_config.get('max_bytes', 10485760),
                backupCount=log_config.get('backup_count', 5)
            )
        else:
            file_handler = logging.FileHandler(log_file)
        
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    def process_image(self, image_path: str, output_filename: Optional[str] = None) -> dict:
        """
        处理单个图像文件
        
        Args:
            image_path: 图像文件路径
            output_filename: 输出文件名 (可选)
            
        Returns:
            处理结果字典
        """
        self.logger.info(f"开始处理图像: {image_path}")
        
        try:
            # 1. 验证图像
            self.logger.info("步骤 1/5: 验证图像")
            is_valid, error_msg = self.image_processor.validate_image(image_path)
            if not is_valid:
                raise ValueError(f"图像验证失败: {error_msg}")
            
            # 2. 处理图像
            self.logger.info("步骤 2/5: 处理图像")
            images = self.image_processor.process_image(image_path)
            
            # 处理第一张图像 (如果是PDF,只处理第一页)
            image = images[0]
            
            # 3. 调用LLM分析图像
            self.logger.info("步骤 3/5: 调用LLM分析图像")
            analysis_result = self.llm_client.analyze_image(image)
            
            content = analysis_result['content']
            self.logger.info(f"LLM分析完成,内容长度: {len(content)} 字符")
            self.logger.debug(f"LLM提供商: {analysis_result.get('provider', 'unknown')}")
            self.logger.debug(f"LLM模型: {analysis_result.get('model', 'unknown')}")
            # 记录原始输出(前1000字符)
            if len(content) <= 1000:
                self.logger.debug(f"LLM原始输出:\n{content}")
            else:
                self.logger.debug(f"LLM原始输出(前1000字符):\n{content[:1000]}\n... (共{len(content)}字符)")
            
            # 4. 解析和转换公式
            self.logger.info("步骤 4/5: 解析和转换公式")
            elements = self.formula_converter.parse_content(content)
            formatted_elements = self.formula_converter.format_for_word(elements)
            
            # 获取公式统计
            stats = self.formula_converter.get_formula_statistics(content)
            self.logger.info(f"公式统计: {stats['total_formulas']} 个公式 "
                           f"(显示: {stats['display_formulas']}, 行内: {stats['inline_formulas']})")
            
            # 5. 生成Word文档
            self.logger.info("步骤 5/5: 生成Word文档")
            output_path = self.document_generator.create_from_analysis(
                analysis_result, image, formatted_elements
            )
            
            self.logger.info(f"处理完成! 输出文件: {output_path}")
            
            return {
                'success': True,
                'output_path': output_path,
                'analysis': analysis_result,
                'statistics': stats,
                'elements_count': len(formatted_elements)
            }
            
        except Exception as e:
            self.logger.error(f"处理失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_batch(self, image_paths: List[str]) -> List[dict]:
        """
        批量处理多个图像
        
        Args:
            image_paths: 图像文件路径列表
            
        Returns:
            处理结果列表
        """
        self.logger.info(f"开始批量处理 {len(image_paths)} 个图像")
        
        results = []
        for idx, image_path in enumerate(image_paths, 1):
            self.logger.info(f"处理进度: {idx}/{len(image_paths)}")
            result = self.process_image(image_path)
            results.append(result)
        
        # 统计
        success_count = sum(1 for r in results if r['success'])
        self.logger.info(f"批量处理完成: {success_count}/{len(image_paths)} 成功")
        
        return results


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced OCR - 数学问题图像转Word文档')
    parser.add_argument('image', help='输入图像文件路径')
    parser.add_argument('-o', '--output', help='输出文件名', default=None)
    parser.add_argument('-c', '--config', help='配置文件路径', default='config/config.yaml')
    
    args = parser.parse_args()
    
    # 创建OCR实例
    ocr = AdvancedOCR(config_path=args.config)
    
    # 处理图像
    result = ocr.process_image(args.image, args.output)
    
    # 输出结果
    if result['success']:
        print(f"\n✓ 处理成功!")
        print(f"输出文件: {result['output_path']}")
        print(f"公式数量: {result['statistics']['total_formulas']}")
        print(f"元素数量: {result['elements_count']}")
    else:
        print(f"\n✗ 处理失败: {result['error']}")
        sys.exit(1)


if __name__ == '__main__':
    main()


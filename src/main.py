"""
主程序入口
整合所有模块,实现完整的工作流程
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
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
            processed_images, original_image = self.image_processor.process_image(image_path)

            # 3. 调用LLM分析图像
            self.logger.info(
                "步骤 3/5: 调用LLM分析图像 (分片数量: %s)",
                len(processed_images)
            )

            analysis_segments = self.llm_client.analyze_images(processed_images)
            analysis_result = self._merge_analysis_segments(analysis_segments)

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
                analysis_result, original_image, formatted_elements
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

    @staticmethod
    def _merge_analysis_segments(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多段LLM分析结果"""
        # 在静态方法开始时获取logger实例
        _logger = logging.getLogger(__name__)

        if not segments:
            raise ValueError("LLM未返回任何内容")

        def _ordered_unique(items: List[Optional[str]]) -> List[str]:
            seen = set()
            ordered: List[str] = []
            for item in items:
                if not item:
                    continue
                if item in seen:
                    continue
                ordered.append(item)
                seen.add(item)
            return ordered

        providers: List[str] = []
        models: List[str] = []
        total_usage: Dict[str, int] = {}
        normalized_segments: List[Dict[str, Any]] = []

        combined_content = ""

        for idx, segment in enumerate(segments):
            segment_content = (segment.get('content') or '').strip()

            # 应用重叠检测和移除
            trimmed_content = AdvancedOCR._trim_overlap_text(combined_content, segment_content)

            # 记录处理结果
            if len(trimmed_content) < len(segment_content):
                removed = len(segment_content) - len(trimmed_content)
                _logger.info(f"分片 {idx+1}/{len(segments)}: 移除 {removed} 字符重叠")
            else:
                _logger.debug(f"分片 {idx+1}/{len(segments)}: 无重叠")

            segment_copy = dict(segment)
            segment_copy['content_trimmed'] = trimmed_content
            normalized_segments.append(segment_copy)

            provider = segment.get('provider')
            if provider:
                providers.append(provider)

            model = segment.get('model')
            if model:
                models.append(model)

            usage = segment.get('usage') or {}
            for key, value in usage.items():
                if value is None:
                    continue
                total_usage[key] = total_usage.get(key, 0) + int(value)

            if not trimmed_content:
                continue

            if combined_content:
                combined_content = f"{combined_content}\n\n{trimmed_content}"
            else:
                combined_content = trimmed_content
        provider_list = _ordered_unique(providers) or ['unknown']
        model_list = _ordered_unique(models) or ['unknown']

        if len(provider_list) == 1:
            provider_label = provider_list[0]
        else:
            provider_label = f"multi ({', '.join(provider_list)})"

        if len(model_list) == 1:
            model_label = model_list[0]
        else:
            model_label = f"segments={len(segments)}"

        merged: Dict[str, Any] = {
            'provider': provider_label,
            'model': model_label,
            'content': combined_content,
            'segments': normalized_segments,
            'segment_count': len(segments),
            'providers': provider_list,
            'models': model_list,
        }

        if total_usage:
            merged['usage'] = total_usage

        return merged

    @staticmethod
    def _trim_overlap_text(existing: str, new_content: str, max_overlap: int = 2000,
                           min_overlap: int = 30) -> str:
        """去除与已合并文本重复的前缀,缓解切片重叠导致的重复"""
        # 获取logger实例(在静态方法中)
        _logger = logging.getLogger(__name__)

        if not new_content:
            _logger.debug("新内容为空，跳过")
            return ""

        candidate = new_content.lstrip()
        if not candidate:
            _logger.debug("新内容去除前导空白后为空，跳过")
            return ""

        if not existing:
            _logger.debug(f"无已有内容，保留完整新内容 ({len(candidate)} 字符)")
            return candidate

        import re

        # 完全移除空格的归一化（最激进）
        def remove_all_spaces(text: str) -> str:
            """完全移除所有空白符，只保留内容"""
            return re.sub(r'\s+', '', text)

        # 完全无空格版本
        existing_no_space = remove_all_spaces(existing)
        candidate_no_space = remove_all_spaces(candidate)

        _logger.debug(
            "重叠检测: 已有内容 %s 字符(去空格后 %s), 新内容 %s 字符(去空格后 %s)",
            len(existing),
            len(existing_no_space),
            len(candidate),
            len(candidate_no_space)
        )

        # 检查完全重复（无空格版本）
        if candidate_no_space in existing_no_space:
            _logger.info(
                "✓ 检测到完全重复内容（忽略空格），跳过新内容\n"
                "  新内容前50字符(去空格): %s...",
                candidate_no_space[:50]
            )
            return ""

        # 获取尾部用于比较（无空格版本）
        existing_tail_no_space = existing_no_space[-max_overlap:]
        max_len = min(len(existing_tail_no_space), len(candidate_no_space))

        _logger.debug(
            "搜索重叠: 在已有内容尾部 %s 字符中，搜索 %s-%s 字符的匹配",
            len(existing_tail_no_space),
            min_overlap,
            max_len
        )

        # 尝试找到最长的重叠部分（无空格版本）
        best_overlap_len = 0
        best_suffix = None
        best_prefix = None

        for overlap in range(max_len, min_overlap - 1, -1):
            suffix = existing_tail_no_space[-overlap:]
            prefix = candidate_no_space[:overlap]

            # 精确匹配（无空格）
            if suffix == prefix:
                best_overlap_len = overlap
                best_suffix = suffix
                best_prefix = prefix
                _logger.info(
                    "✓ 发现重叠(无空格): %s 字符\n"
                    "  重叠内容前50字符: %s...",
                    overlap,
                    prefix[:50]
                )
                break

        if best_overlap_len > 0:
            # 找到重叠，需要在原始文本中找到切分位置
            # 使用比例估算
            ratio = best_overlap_len / len(candidate_no_space) if len(candidate_no_space) > 0 else 0
            cut_pos = int(len(candidate) * ratio)

            _logger.debug(
                "计算切分位置: 重叠比例 %.2f%%, 初始切分位置 %s",
                ratio * 100,
                cut_pos
            )

            # 在附近寻找自然边界（换行、句号、公式边界）
            search_range = min(150, len(candidate) - cut_pos)
            found_separator = None

            if search_range > 0:
                chunk = candidate[cut_pos:cut_pos + search_range]
                # 优先在双换行处切分，其次单换行，最后句号
                best_sep_pos = -1
                for sep in ['\n\n', '\n', '。', '. ', '$$', '$']:
                    sep_pos = chunk.find(sep)
                    if sep_pos >= 0:
                        best_sep_pos = sep_pos + len(sep)
                        found_separator = repr(sep)
                        break

                if best_sep_pos >= 0:
                    cut_pos = cut_pos + best_sep_pos
                    _logger.debug(
                        "在自然边界切分: 找到分隔符 %s, 调整切分位置到 %s",
                        found_separator,
                        cut_pos
                    )

            result = candidate[cut_pos:].lstrip()

            if result:
                removed_chars = len(candidate) - len(result)
                _logger.info(
                    "✓ 移除重叠内容: 删除 %s 字符, 保留 %s 字符\n"
                    "  保留内容前50字符: %s...",
                    removed_chars,
                    len(result),
                    result[:50]
                )
                return result
            else:
                _logger.info("✓ 移除重叠后无剩余内容，跳过整个分片")
                return ""

        _logger.debug(
            "✗ 未发现重叠（搜索了 %s-%s 字符），保留完整内容 (%s 字符)\n"
            "  新内容前50字符(去空格): %s...\n"
            "  已有尾部50字符(去空格): ...%s",
            min_overlap,
            max_len,
            len(candidate),
            candidate_no_space[:50],
            existing_tail_no_space[-50:]
        )
        return candidate
    
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

"""
图像预处理模块
负责图像验证、格式转换和预处理
"""

import os
import shutil
import base64
import logging
from pathlib import Path
from typing import Optional, Tuple, List
from io import BytesIO

from PIL import Image
import cv2
import numpy as np
from PyPDF2 import PdfReader
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


class ImageProcessor:
    """图像处理器类"""
    
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.pdf'}
    
    def __init__(self, config: dict):
        """
        初始化图像处理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.max_size_mb = config.get('image', {}).get('max_size_mb', 10)
        self.max_dimension = config.get('image', {}).get('preprocessing', {}).get('max_dimension', 1600)
        self.quality = config.get('image', {}).get('quality', 95)
        self.base64_format = config.get('image', {}).get('base64_format', 'PNG').upper()
        if self.base64_format == 'JPG':
            self.base64_format = 'JPEG'
        self.base64_quality = config.get('image', {}).get('base64_quality', 85)
        self.base64_max_bytes = int(config.get('image', {}).get('base64_max_bytes', 0) or 0)

        slicing_cfg = config.get('image', {}).get('slicing', {}) or {}
        self.slice_enabled = slicing_cfg.get('enable', False)
        self.slice_min_height = slicing_cfg.get('min_height', 2200)
        self.slice_aspect_ratio = slicing_cfg.get('aspect_ratio_threshold', 2.0)
        self.slice_target_height = slicing_cfg.get('target_height', 1100)
        self.slice_min_segment_height = slicing_cfg.get('min_segment_height', 700)
        self.slice_overlap = slicing_cfg.get('overlap', 160)
        self.slice_whitespace_window = slicing_cfg.get('whitespace_window', 150)
        self.slice_whitespace_density_threshold = slicing_cfg.get('whitespace_density_threshold', 0.08)
        self.slice_max_segments = slicing_cfg.get('max_segments', 0)
        self.slice_whitespace_value = slicing_cfg.get('whitespace_value_threshold', 240)

        # 自适应overlap配置
        adaptive_cfg = slicing_cfg.get('adaptive_overlap', {}) or {}
        self.adaptive_overlap_enabled = adaptive_cfg.get('enable', True)
        self.adaptive_excellent_threshold = adaptive_cfg.get('excellent_threshold', 0.05)
        self.adaptive_good_threshold = adaptive_cfg.get('good_threshold', 0.10)
        self.adaptive_excellent_overlap = adaptive_cfg.get('excellent_overlap', 0)
        self.adaptive_good_overlap = adaptive_cfg.get('good_overlap', 30)
        self.adaptive_default_overlap = adaptive_cfg.get('default_overlap', 160)

        debug_cfg = slicing_cfg.get('debug', {}) or {}
        self.slice_debug_save = debug_cfg.get('save_segments', False)
        self.slice_debug_dir = Path(debug_cfg.get('output_dir', 'logs/segments'))
        self.slice_debug_clear = debug_cfg.get('clear_before_save', True)

        page_break_cfg = slicing_cfg.get('page_break_detection', {}) or {}
        self.page_break_enabled = page_break_cfg.get('enable', False)
        self.page_break_whiteness = float(page_break_cfg.get('whiteness_threshold', 0.97))
        self.page_break_min_blank = int(page_break_cfg.get('min_blank_height', 200))
        self.page_break_margin_ratio = float(page_break_cfg.get('margin_ratio', 0.05))

        logger.info("ImageProcessor initialized")
    
    def validate_image(self, image_path: str) -> Tuple[bool, Optional[str]]:
        """
        验证图像文件
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            path = Path(image_path)
            
            # 检查文件是否存在
            if not path.exists():
                return False, f"文件不存在: {image_path}"
            
            # 检查文件扩展名
            if path.suffix.lower() not in self.SUPPORTED_FORMATS:
                return False, f"不支持的文件格式: {path.suffix}. 支持的格式: {', '.join(self.SUPPORTED_FORMATS)}"
            
            # 检查文件大小
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_size_mb:
                return False, f"文件过大: {file_size_mb:.2f}MB (最大: {self.max_size_mb}MB)"
            
            # 尝试打开图像
            if path.suffix.lower() == '.pdf':
                # 验证PDF
                try:
                    reader = PdfReader(str(path))
                    if len(reader.pages) == 0:
                        return False, "PDF文件为空"
                except Exception as e:
                    return False, f"无效的PDF文件: {str(e)}"
            else:
                # 验证图像文件
                try:
                    with Image.open(path) as img:
                        img.verify()
                except Exception as e:
                    return False, f"无效的图像文件: {str(e)}"
            
            logger.info(f"图像验证成功: {image_path}")
            return True, None
            
        except Exception as e:
            logger.error(f"图像验证失败: {str(e)}")
            return False, f"验证过程出错: {str(e)}"
    
    def process_image(self, image_path: str) -> Tuple[List[Image.Image], Image.Image]:
        """
        处理图像文件,返回PIL Image对象列表及原始图像
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            (预处理后的图像列表, 原始图像)
        """
        path = Path(image_path)
        images: List[Image.Image] = []
        original_image: Optional[Image.Image] = None

        try:
            debug_base_dir: Optional[Path] = None
            if self.slice_debug_save:
                debug_base_dir = self.slice_debug_dir / path.stem
                if self.slice_debug_clear and debug_base_dir.exists():
                    shutil.rmtree(debug_base_dir)
                debug_base_dir.mkdir(parents=True, exist_ok=True)

            if path.suffix.lower() == '.pdf':
                # 处理PDF文件
                logger.info(f"转换PDF文件: {image_path}")
                images = convert_from_path(str(path), dpi=300)
                logger.info(f"PDF转换完成,共 {len(images)} 页")
                if images:
                    original_image = images[0].copy()
            else:
                # 处理图像文件
                img = Image.open(path)
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                original_image = img.copy()
                images = [img]
                logger.info(f"图像加载成功: {image_path}")

            # 预处理图像
            processed_images = []
            for idx, img in enumerate(images):
                page_images = self._split_pages_if_needed(img)

                for page_idx, page_image in enumerate(page_images):
                    segments = self._slice_image_if_needed(page_image)
                    if len(segments) > 1:
                        logger.info(
                            "图像 %s-分页%s 切分为 %s 段 (原尺寸: %sx%s)",
                            idx + 1,
                            page_idx + 1,
                            len(segments),
                            page_image.width,
                            page_image.height
                        )

                    page_debug_dir: Optional[Path] = None
                    if debug_base_dir is not None:
                        page_debug_dir = debug_base_dir / f"page_{idx + 1:02d}" / f"split_{page_idx + 1:02d}"
                        page_debug_dir.mkdir(parents=True, exist_ok=True)

                    for segment_idx, segment in enumerate(segments):
                        processed_img = self._preprocess_image(segment)
                        processed_images.append(processed_img)
                        logger.debug(
                            "图像 %s-分页%s 段 %s 预处理完成 (%sx%s)",
                            idx + 1,
                            page_idx + 1,
                            segment_idx + 1,
                            processed_img.width,
                            processed_img.height
                        )

                        if page_debug_dir is not None:
                            self._save_debug_segment(
                                processed_img,
                                page_debug_dir,
                                segment_idx
                            )

            if not processed_images:
                raise ValueError("图像处理后无有效内容")

            if original_image is None:
                original_image = processed_images[0].copy()

            return processed_images, original_image

        except Exception as e:
            logger.error(f"图像处理失败: {str(e)}")
            raise

    def _slice_image_if_needed(self, image: Image.Image) -> List[Image.Image]:
        """根据配置决定是否对图像进行切分"""
        if not self.slice_enabled:
            return [image]

        width, height = image.size

        if height < self.slice_min_height:
            return [image]

        if width == 0:
            return [image]

        aspect_ratio = height / max(width, 1)
        if aspect_ratio < self.slice_aspect_ratio and height < self.slice_target_height * 1.5:
            return [image]

        # 计算内容密度曲线（用于查找空白切分点）
        gray = np.array(image.convert('L'))
        dark_threshold = np.clip(self.slice_whitespace_value, 10, 255)
        dark_ratio = (gray < dark_threshold).mean(axis=1)
        window = max(3, int(self.slice_whitespace_window // 3) or 3)
        kernel = np.ones(window) / window
        smoothed = np.convolve(dark_ratio, kernel, mode='same')

        segments: List[Image.Image] = []
        start = 0
        segment_count = 0
        max_segments = max(0, int(self.slice_max_segments))

        logger.info("开始切分图像 (高度: %s, 自适应overlap: %s)",
                   height, "启用" if self.adaptive_overlap_enabled else "禁用")

        while start < height:
            segment_count += 1

            if max_segments and segment_count >= max_segments:
                logger.warning(
                    "达到切片上限 %s，剩余内容将合并到最后一段 (剩余高度: %s)",
                    max_segments,
                    height - start
                )
                end = height
                cut_quality = 1.0  # 强制切分，质量未知
            else:
                target_end = min(start + self.slice_target_height, height)
                remaining = height - start

                if remaining <= self.slice_min_segment_height:
                    end = height
                    cut_quality = 0.0  # 最后一段，无需overlap
                else:
                    search_start = max(start + self.slice_min_segment_height,
                                       target_end - self.slice_whitespace_window)
                    search_end = min(height - self.slice_min_segment_height,
                                     target_end + self.slice_whitespace_window)
                    end = self._find_cut_line(smoothed, search_start, search_end, target_end)

                    # 获取切分点的内容密度（用于评估切分质量）
                    cut_quality = float(smoothed[end]) if end < len(smoothed) else 1.0

            if end <= start:
                end = min(start + self.slice_min_segment_height, height)
                cut_quality = 1.0

            # 创建当前段
            segment = image.crop((0, start, width, end))
            segments.append(segment)

            logger.info(
                "段 %s/%s: 行 %s-%s (高度 %s), 切分点密度: %.3f",
                segment_count,
                "?" if not max_segments else max_segments,
                start,
                end,
                end - start,
                cut_quality
            )

            if end >= height:
                break

            # 根据切分点质量动态计算overlap
            if self.adaptive_overlap_enabled:
                if cut_quality <= self.adaptive_excellent_threshold:
                    # 非常好的切分点（几乎完全空白）
                    overlap = self.adaptive_excellent_overlap
                    quality_desc = "极佳空白"
                elif cut_quality <= self.adaptive_good_threshold:
                    # 较好的切分点（较空白）
                    overlap = self.adaptive_good_overlap
                    quality_desc = "良好空白"
                else:
                    # 不理想的切分点（在内容中间）
                    overlap = self.adaptive_default_overlap
                    quality_desc = "内容区域"

                logger.info(
                    "  → 切分质量: %s, 应用overlap: %spx",
                    quality_desc,
                    overlap
                )
            else:
                # 禁用自适应，使用固定overlap
                overlap = self.slice_overlap
                logger.debug("  → 使用固定overlap: %spx", overlap)

            # 计算下一段的起始位置
            next_start = max(end - overlap, start + 1)
            if next_start <= start:
                next_start = end
            start = min(next_start, height)

        logger.info("图像切分完成: %s 段", len(segments))
        return segments

    def _split_pages_if_needed(self, image: Image.Image) -> List[Image.Image]:
        """检测大幅空白行以识别分页"""
        if not self.page_break_enabled:
            return [image]

        width, height = image.size
        if height < self.slice_min_height * 1.2:
            return [image]

        gray = np.array(image.convert('L'), dtype=np.float32) / 255.0
        row_mean = gray.mean(axis=1)
        threshold = np.clip(self.page_break_whiteness, 0.0, 1.0)
        blank_mask = row_mean >= threshold

        margin = int(height * max(self.page_break_margin_ratio, 0))
        min_blank = max(1, self.page_break_min_blank)

        breaks: List[int] = []
        run_start = None
        for idx, is_blank in enumerate(blank_mask):
            if is_blank:
                if run_start is None:
                    run_start = idx
            else:
                if run_start is not None:
                    run_len = idx - run_start
                    if run_len >= min_blank and run_start > margin and idx < height - margin:
                        cut = run_start + run_len // 2
                        breaks.append(cut)
                    run_start = None

        if run_start is not None:
            run_len = height - run_start
            if run_len >= min_blank and run_start > margin:
                cut = run_start + run_len // 2
                breaks.append(cut)

        if not breaks:
            return [image]

        pages: List[Image.Image] = []
        last = 0
        for cut in breaks:
            if cut - last < self.slice_min_segment_height:
                continue
            pages.append(image.crop((0, last, width, cut)))
            last = cut

        if height - last >= self.slice_min_segment_height:
            pages.append(image.crop((0, last, width, height)))

        if not pages:
            return [image]

        logger.info("检测到 %s 个分页分隔, 输出 %s 页", len(breaks), len(pages))
        return pages

    def _find_cut_line(self, density_profile: np.ndarray, search_start: int,
                        search_end: int, default_end: int) -> int:
        """在给定范围内查找最适合的切分位置"""
        if search_start >= search_end or search_start >= len(density_profile):
            return default_end

        window = density_profile[search_start:search_end]
        if window.size == 0:
            return default_end

        best_index = int(np.argmin(window))
        best_density = float(window[best_index])
        cut_position = search_start + best_index

        if best_density <= self.slice_whitespace_density_threshold:
            return cut_position

        return default_end

    def _save_debug_segment(self, image: Image.Image, directory: Path, index: int):
        """保存调试用的切片图像"""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            filename = directory / f"segment_{index + 1:02d}_{image.width}x{image.height}.png"
            image.save(filename, format='PNG')
        except Exception as exc:  # noqa: BLE001
            logger.warning("保存切片调试图像失败: %s", exc)
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        预处理单个图像
        
        Args:
            image: PIL Image对象
            
        Returns:
            处理后的PIL Image对象
        """
        # 调整大小
        if self.config.get('image', {}).get('preprocessing', {}).get('resize_if_large', True):
            image = self._resize_if_needed(image)
        
        # 增强对比度 (可选)
        if self.config.get('image', {}).get('preprocessing', {}).get('enhance_contrast', False):
            image = self._enhance_contrast(image)
        
        # 降噪 (可选)
        if self.config.get('image', {}).get('preprocessing', {}).get('denoise', False):
            image = self._denoise(image)
        
        return image
    
    def _resize_if_needed(self, image: Image.Image) -> Image.Image:
        """
        如果图像过大则调整大小
        
        Args:
            image: PIL Image对象
            
        Returns:
            调整后的图像
        """
        width, height = image.size
        max_dim = max(width, height)
        
        if max_dim > self.max_dimension:
            scale = self.max_dimension / max_dim
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(f"图像已调整大小: {width}x{height} -> {new_width}x{new_height}")
        
        return image
    
    def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        """
        增强图像对比度
        
        Args:
            image: PIL Image对象
            
        Returns:
            增强后的图像
        """
        # 转换为numpy数组
        img_array = np.array(image)
        
        # 转换为灰度图
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # 应用CLAHE (对比度受限自适应直方图均衡化)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # 转换回RGB
        enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
        
        return Image.fromarray(enhanced_rgb)
    
    def _denoise(self, image: Image.Image) -> Image.Image:
        """
        图像降噪
        
        Args:
            image: PIL Image对象
            
        Returns:
            降噪后的图像
        """
        img_array = np.array(image)
        denoised = cv2.fastNlMeansDenoisingColored(img_array, None, 10, 10, 7, 21)
        return Image.fromarray(denoised)
    
    def image_to_base64(self, image: Image.Image) -> str:
        """
        将PIL Image转换为base64字符串
        
        Args:
            image: PIL Image对象
            
        Returns:
            base64编码的字符串
        """
        encode_image = image.copy()
        if self.base64_format in {"JPEG", "WEBP"} and encode_image.mode != 'RGB':
            encode_image = encode_image.convert('RGB')

        quality = self.base64_quality
        min_quality = 50
        attempts = 0
        data = None

        while True:
            buffered = BytesIO()
            save_kwargs = {}

            if self.base64_format in {"JPEG", "WEBP"}:
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            elif self.base64_format == "PNG":
                save_kwargs['optimize'] = True

            encode_image.save(buffered, format=self.base64_format, **save_kwargs)
            data = buffered.getvalue()

            if not self.base64_max_bytes or len(data) <= self.base64_max_bytes or attempts >= 6:
                if self.base64_max_bytes and len(data) > self.base64_max_bytes:
                    logger.warning(
                        "Base64图像大小仍超过限制: %s > %s bytes, 已达压缩上限",
                        len(data),
                        self.base64_max_bytes
                    )
                break

            attempts += 1
            logger.debug(
                "图像编码大小 %s bytes 超过限制 %s bytes, 第 %s 次尝试压缩",
                len(data),
                self.base64_max_bytes,
                attempts
            )

            if self.base64_format in {"JPEG", "WEBP"} and quality > min_quality:
                new_quality = max(min_quality, int(quality * 0.8))
                if new_quality == quality and quality > min_quality:
                    new_quality = quality - 5
                if new_quality < min_quality:
                    new_quality = min_quality
                quality = new_quality
                continue

            width, height = encode_image.size
            new_width = int(width * 0.85)
            new_height = int(height * 0.85)

            if new_width < 512 or new_height < 512:
                logger.warning(
                    "图像缩放已接近最小尺寸: %sx%s, 无法继续压缩",
                    new_width,
                    new_height
                )
                break

            encode_image = encode_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        img_str = base64.b64encode(data).decode()
        log_level = logging.INFO if self.slice_enabled else logging.DEBUG
        logger.log(
            log_level,
            "最终图像编码大小: %s bytes (格式: %s, 尺寸: %sx%s)",
            len(data),
            self.base64_format,
            encode_image.width,
            encode_image.height
        )
        return img_str
    
    def save_image(self, image: Image.Image, output_path: str) -> str:
        """
        保存图像到文件
        
        Args:
            image: PIL Image对象
            output_path: 输出路径
            
        Returns:
            保存的文件路径
        """
        try:
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 保存图像
            image.save(output_path, quality=self.quality, optimize=True)
            logger.info(f"图像已保存: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"保存图像失败: {str(e)}")
            raise

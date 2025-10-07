"""
图像预处理模块
负责图像验证、格式转换和预处理
"""

import os
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
        self.max_dimension = config.get('image', {}).get('preprocessing', {}).get('max_dimension', 2048)
        self.quality = config.get('image', {}).get('quality', 95)
        
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
    
    def process_image(self, image_path: str) -> List[Image.Image]:
        """
        处理图像文件,返回PIL Image对象列表
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            PIL Image对象列表 (PDF可能有多页)
        """
        path = Path(image_path)
        images = []
        
        try:
            if path.suffix.lower() == '.pdf':
                # 处理PDF文件
                logger.info(f"转换PDF文件: {image_path}")
                images = convert_from_path(str(path), dpi=300)
                logger.info(f"PDF转换完成,共 {len(images)} 页")
            else:
                # 处理图像文件
                img = Image.open(path)
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                images = [img]
                logger.info(f"图像加载成功: {image_path}")
            
            # 预处理图像
            processed_images = []
            for idx, img in enumerate(images):
                processed_img = self._preprocess_image(img)
                processed_images.append(processed_img)
                logger.debug(f"图像 {idx+1}/{len(images)} 预处理完成")
            
            return processed_images
            
        except Exception as e:
            logger.error(f"图像处理失败: {str(e)}")
            raise
    
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
        buffered = BytesIO()
        image.save(buffered, format="PNG", quality=self.quality)
        img_str = base64.b64encode(buffered.getvalue()).decode()
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


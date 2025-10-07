"""
图像处理器单元测试
"""

import os
import pytest
from pathlib import Path
from PIL import Image
import tempfile

from src.image_processor import ImageProcessor


@pytest.fixture
def config():
    """测试配置"""
    return {
        'image': {
            'max_size_mb': 10,
            'quality': 95,
            'preprocessing': {
                'resize_if_large': True,
                'max_dimension': 2048,
                'enhance_contrast': False,
                'denoise': False
            }
        }
    }


@pytest.fixture
def image_processor(config):
    """创建图像处理器实例"""
    return ImageProcessor(config)


@pytest.fixture
def sample_image():
    """创建测试图像"""
    img = Image.new('RGB', (800, 600), color='white')
    return img


class TestImageProcessor:
    """图像处理器测试类"""
    
    def test_initialization(self, image_processor):
        """测试初始化"""
        assert image_processor is not None
        assert image_processor.max_size_mb == 10
        assert image_processor.quality == 95
    
    def test_validate_nonexistent_file(self, image_processor):
        """测试验证不存在的文件"""
        is_valid, error = image_processor.validate_image('nonexistent.png')
        assert not is_valid
        assert '不存在' in error
    
    def test_validate_unsupported_format(self, image_processor):
        """测试验证不支持的格式"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = f.name
            f.write(b'test')
        
        try:
            is_valid, error = image_processor.validate_image(temp_path)
            assert not is_valid
            assert '不支持' in error
        finally:
            os.unlink(temp_path)
    
    def test_validate_valid_image(self, image_processor, sample_image):
        """测试验证有效图像"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            sample_image.save(temp_path)
        
        try:
            is_valid, error = image_processor.validate_image(temp_path)
            assert is_valid
            assert error is None
        finally:
            os.unlink(temp_path)
    
    def test_process_image(self, image_processor, sample_image):
        """测试处理图像"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            sample_image.save(temp_path)
        
        try:
            images = image_processor.process_image(temp_path)
            assert len(images) == 1
            assert isinstance(images[0], Image.Image)
        finally:
            os.unlink(temp_path)
    
    def test_resize_large_image(self, image_processor):
        """测试调整大图像大小"""
        # 创建大图像
        large_image = Image.new('RGB', (4000, 3000), color='white')
        
        resized = image_processor._resize_if_needed(large_image)
        
        max_dim = max(resized.size)
        assert max_dim <= image_processor.max_dimension
    
    def test_image_to_base64(self, image_processor, sample_image):
        """测试图像转base64"""
        base64_str = image_processor.image_to_base64(sample_image)
        
        assert isinstance(base64_str, str)
        assert len(base64_str) > 0
    
    def test_save_image(self, image_processor, sample_image):
        """测试保存图像"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'test_output.png')
            
            saved_path = image_processor.save_image(sample_image, output_path)
            
            assert os.path.exists(saved_path)
            assert saved_path == output_path
    
    def test_validate_oversized_file(self, image_processor, sample_image):
        """测试验证过大的文件"""
        # 修改配置为更小的限制
        image_processor.max_size_mb = 0.001  # 1KB
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            sample_image.save(temp_path)
        
        try:
            is_valid, error = image_processor.validate_image(temp_path)
            assert not is_valid
            assert '过大' in error
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


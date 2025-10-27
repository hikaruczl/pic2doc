"""
LLM API客户端模块
支持多种多模态LLM: OpenAI GPT-4 Vision, Anthropic Claude 3, Google Gemini, Qwen-VL
"""

import os
import re
import time
import json
import logging
import inspect
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any, List
from PIL import Image

import httpx
from openai import OpenAI
import openai
from anthropic import Anthropic

# Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Google Generative AI library not installed. Gemini support disabled.")

# Alibaba Qwen-VL
try:
    import dashscope
    from dashscope import MultiModalConversation
    QWEN_AVAILABLE = True
except ImportError:
    QWEN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("DashScope library not installed. Qwen-VL support disabled.")

# Geometry rendering
try:
    from src.geometry_renderer import GeometryRenderer, parse_geometry_json
    GEOMETRY_RENDERER_AVAILABLE = True
except ImportError:
    GEOMETRY_RENDERER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Geometry renderer not available. Cairo may not be installed.")

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM API客户端类"""
    
    def __init__(self, config: dict, image_processor):
        """
        初始化LLM客户端
        
        Args:
            config: 配置字典
            image_processor: 图像处理器实例
        """
        self.config = config
        self.image_processor = image_processor
        
        # 获取API密钥
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_api_key = (
            os.getenv('GEMINI_API_KEY')
            or os.getenv('AISTUDIO_API_KEY')
            or os.getenv('GOOGLE_API_KEY')
        )
        self._gemini_key_source = None
        if os.getenv('GEMINI_API_KEY'):
            self._gemini_key_source = 'GEMINI_API_KEY'
        elif os.getenv('AISTUDIO_API_KEY'):
            self._gemini_key_source = 'AISTUDIO_API_KEY'
        elif os.getenv('GOOGLE_API_KEY'):
            self._gemini_key_source = 'GOOGLE_API_KEY'
        self.qwen_api_key = os.getenv('QWEN_API_KEY')

        # 获取配置
        self.primary_provider = os.getenv('PRIMARY_LLM_PROVIDER',
                                         config.get('llm', {}).get('primary_provider', 'openai'))
        self.fallback_provider = os.getenv('FALLBACK_LLM_PROVIDER',
                                           config.get('llm', {}).get('fallback_provider'))

        # 请求超时配置
        self.request_timeout = int(os.getenv(
            'LLM_REQUEST_TIMEOUT_SECONDS',
            config.get('llm', {}).get('request_timeout_seconds', 300)
        ))

        concurrency_cfg = config.get('llm', {}).get('concurrency', {}) or {}
        self.concurrent_enabled = concurrency_cfg.get('enable', True)
        self.max_parallel_requests = int(os.getenv(
            'LLM_MAX_PARALLEL_REQUESTS',
            concurrency_cfg.get('max_parallel_requests', 2)
        ))

        # 初始化客户端
        self.openai_client = None
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            openai_base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
            openai_http_client = httpx.Client(
                base_url=openai_base_url,
                timeout=self.request_timeout,
                follow_redirects=True,
                trust_env=False
            )
            self.openai_client = OpenAI(
                api_key=self.openai_api_key,
                base_url=openai_base_url,
                timeout=self.request_timeout,
                http_client=openai_http_client
            )
            logger.info("OpenAI客户端已初始化")

        self.anthropic_client = None
        if self.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=self.anthropic_api_key, timeout=self.request_timeout)
            logger.info("Anthropic客户端已初始化")

        self._gemini_request_options = None
        self._gemini_supports_timeout_kwarg = False
        if self.gemini_api_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.gemini_api_key)
            source = self._gemini_key_source or 'unknown source'
            logger.info("Google Gemini客户端已初始化 (key source: %s)", source)
            try:
                if hasattr(genai, 'types') and hasattr(genai.types, 'RequestOptions'):
                    self._gemini_request_options = genai.types.RequestOptions(timeout=self.request_timeout)
            except Exception:
                logger.debug("Gemini RequestOptions 未可用, 使用默认超时行为")

            try:
                params = inspect.signature(genai.GenerativeModel.generate_content).parameters
                self._gemini_supports_timeout_kwarg = 'timeout' in params
            except (ValueError, TypeError):
                self._gemini_supports_timeout_kwarg = False

        self._qwen_supports_timeout = False
        if self.qwen_api_key and QWEN_AVAILABLE:
            dashscope.api_key = self.qwen_api_key
            logger.info("Qwen-VL客户端已初始化")
            try:
                params = inspect.signature(MultiModalConversation.call).parameters
                self._qwen_supports_timeout = 'timeout' in params
            except (ValueError, TypeError):
                self._qwen_supports_timeout = False
        
        # 重试配置
        self.max_retries = config.get('llm', {}).get('retry', {}).get('max_attempts', 3)
        self.retry_delay = config.get('llm', {}).get('retry', {}).get('delay_seconds', 2)
        self.backoff_multiplier = config.get('llm', {}).get('retry', {}).get('backoff_multiplier', 2)
        
        logger.info(f"LLMClient initialized - Primary: {self.primary_provider}, Fallback: {self.fallback_provider}")
    
    def analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        """分析图像并提取数学内容"""
        try:
            providers = self._build_provider_chain()
            last_result: Optional[Dict[str, Any]] = None

            for provider in providers:
                result = self._analyze_with_retry(image, provider)
                if not result:
                    continue

                result = self._normalize_llm_result(result)
                content = result.get('content', '')
                if not self._content_lacks_transcription(content):
                    return result

                logger.warning("提供商 %s 返回内容缺少完整文本或仅包含代码，尝试下一个提供商", provider)
                last_result = result

            if last_result:
                logger.warning("所有可用提供商均未返回完整转录，使用最后一次结果")
                return last_result

            raise Exception("所有LLM提供商都无法处理图像")

        except Exception as e:
            logger.error(f"图像分析失败: {str(e)}")
            raise
    
    def _analyze_with_retry(self, image: Image.Image, provider: str) -> Optional[Dict[str, Any]]:
        """
        使用重试机制分析图像

        Args:
            image: PIL Image对象
            provider: 提供商名称 ('openai', 'anthropic', 'gemini', 'qwen')

        Returns:
            分析结果或None
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"尝试使用 {provider} 分析图像 (尝试 {attempt + 1}/{self.max_retries})")

                if provider == 'openai':
                    result = self._analyze_with_openai(image)
                elif provider == 'anthropic':
                    result = self._analyze_with_anthropic(image)
                elif provider == 'gemini':
                    result = self._analyze_with_gemini(image)
                elif provider == 'qwen':
                    result = self._analyze_with_qwen(image)
                else:
                    raise ValueError(f"不支持的提供商: {provider}")
                
                logger.info(f"使用 {provider} 分析成功")
                return result
                
            except Exception as e:
                logger.warning(f"尝试 {attempt + 1} 失败: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (self.backoff_multiplier ** attempt)
                    logger.info(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)
                else:
                    logger.error(f"使用 {provider} 的所有重试都失败")
        
        return None

    def analyze_images(self, images: List[Image.Image], original_image: Optional[Image.Image] = None) -> List[Dict[str, Any]]:
        """并行或串行分析多张图像"""
        if not images:
            return []

        # 获取原图尺寸用于坐标转换
        original_size = original_image.size if original_image else None

        if len(images) == 1 or not self.concurrent_enabled or self.max_parallel_requests <= 1:
            sequential_results: List[Dict[str, Any]] = []
            for idx, img in enumerate(images):
                logger.info("串行处理图像分片 %s/%s", idx + 1, len(images))
                result = self.analyze_image(img)
                result = self._post_process_geometry(result, img, original_size)
                result['segment_index'] = idx
                sequential_results.append(result)
            return sequential_results

        max_workers = max(1, min(self.max_parallel_requests, len(images)))
        results: List[Optional[Dict[str, Any]]] = [None] * len(images)

        def _worker(index: int, img: Image.Image) -> Dict[str, Any]:
            logger.info("并行处理图像分片 %s/%s", index + 1, len(images))
            result = self.analyze_image(img)
            result = self._post_process_geometry(result, img, original_size)
            result['segment_index'] = index
            return result

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(_worker, idx, img): idx
                for idx, img in enumerate(images)
            }

            for future in as_completed(future_map):
                idx = future_map[future]
                try:
                    results[idx] = future.result()
                except Exception as exc:  # noqa: BLE001
                    logger.error("分片 %s 处理失败: %s", idx + 1, exc)
                    # 取消其他任务
                    for pending_future in future_map:
                        if not pending_future.done():
                            pending_future.cancel()
                    raise

        return [res for res in results if res is not None]

    GEOMETRY_PLACEHOLDER_PATTERN = re.compile(
        r'```(?:latex|tex)?\s*\\begin\{figure\}.*?\\includegraphics[^{}]*\{placeholder\.png\}.*?```',
        re.DOTALL | re.IGNORECASE
    )
    # 简化正则表达式，只匹配关键部分，支持任意长度的Base64字符串
    GEOMETRY_SVG_JSON_PATTERN = re.compile(
        r'\{\s*"img_b64"\s*:\s*"([^"]+)"\s*,\s*"format"\s*:\s*"svg"\s*\}',
        re.IGNORECASE | re.DOTALL
    )

    @staticmethod
    def _parse_svg_json_format(content: str) -> Optional[Dict[str, str]]:
        """
        解析SVG-in-JSON格式: {"text": "...", "figure_svg": "<svg>...</svg>", "geometry_crop_box": [...]}

        Args:
            content: LLM返回的原始内容

        Returns:
            包含text、figure_svg和geometry_crop_box的字典，解析失败返回None
        """
        # 清理可能的Markdown代码块标记
        cleaned_content = content.strip()
        if cleaned_content.startswith('```'):
            # 移除首尾的```json或```标记
            lines = cleaned_content.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            cleaned_content = '\n'.join(lines).strip()

        # 尝试直接解析JSON
        try:
            data = json.loads(cleaned_content)
            if isinstance(data, dict) and 'text' in data:
                logger.info("成功解析SVG-in-JSON格式")
                return {
                    'text': data.get('text', ''),
                    'figure_svg': data.get('figure_svg', ''),
                    'geometry_crop_box': data.get('geometry_crop_box', None)
                }
        except json.JSONDecodeError:
            # JSON解析失败，可能不是这种格式
            pass

        return None

    def _post_process_geometry(self, result: Dict[str, Any], image: Image.Image, original_image_size: Optional[tuple] = None) -> Dict[str, Any]:
        """检测并处理几何图形JSON或SVG-in-JSON格式"""
        content = result.get('content')
        if not content or not isinstance(content, str):
            return result

        metadata = result.setdefault('metadata', {})

        # 获取几何处理策略
        geometry_config = self.config.get('llm', {}).get('geometry', {})
        geometry_strategy = geometry_config.get('strategy', 'crop')
        # 不再使用默认坐标，完全依赖LLM返回的真实坐标

        # 计算坐标缩放比例
        current_width, current_height = image.size
        scale_x = 1.0
        scale_y = 1.0
        if original_image_size:
            original_width, original_height = original_image_size
            scale_x = current_width / original_width
            scale_y = current_height / original_height
            logger.info(f"图片尺寸变换: 原图{original_width}x{original_height} -> 当前{current_width}x{current_height}, 缩放比例: {scale_x:.3f}x{scale_y:.3f}")

        # 尝试解析SVG-in-JSON格式: {"text": "...", "figure_svg": "<svg>...</svg>", "geometry_crop_box": [...]}
        svg_json_data = self._parse_svg_json_format(content)
        if svg_json_data:
            text_content = svg_json_data.get('text', '')
            figure_svg = svg_json_data.get('figure_svg', '')
            geometry_crop_box = svg_json_data.get('geometry_crop_box', None)

            # 更新result中的content为提取的text
            if text_content:
                result['content'] = text_content
                logger.info("成功解析SVG-in-JSON格式，提取了文本内容")

            # 如果有裁剪坐标，使用裁剪策略
            if geometry_crop_box and geometry_strategy == 'crop':
                logger.info(f"原始裁剪坐标: {geometry_crop_box}")
                try:
                    # 转换坐标系统：如果有原图尺寸，按比例转换
                    if original_image_size and (scale_x != 1.0 or scale_y != 1.0):
                        adjusted_crop_box = [
                            int(geometry_crop_box[0] * scale_x),
                            int(geometry_crop_box[1] * scale_y),
                            int(geometry_crop_box[2] * scale_x),
                            int(geometry_crop_box[3] * scale_y)
                        ]
                        logger.info(f"调整后裁剪坐标: {adjusted_crop_box}")
                    else:
                        adjusted_crop_box = geometry_crop_box

                    # 验证坐标在图片范围内
                    left, top, right, bottom = adjusted_crop_box
                    left = max(0, min(left, current_width))
                    top = max(0, min(top, current_height))
                    right = max(0, min(right, current_width))
                    bottom = max(0, min(bottom, current_height))

                    # 智能添加边距 - 检测边缘内容密度，只向空白方向扩展
                    original_left, original_top, original_right, original_bottom = left, top, right, bottom

                    # 转换为numpy数组进行边缘检测
                    import numpy as np
                    img_array = np.array(image)

                    # 计算当前裁剪区域内边缘的像素密度作为参考
                    crop_area = img_array[top:bottom, left:right]
                    if len(crop_area.shape) > 2:
                        crop_gray = np.mean(crop_area, axis=2)
                    else:
                        crop_gray = crop_area
                    crop_std = np.std(crop_gray)

                    logger.debug("裁剪区域内像素密度: %.2f (作为参考基准)", crop_std)

                    # 检测各个边缘 - 检查空白区域
                    # 扩大检测范围到20像素，降低阈值到50%以捕获字母标注
                    padding = 20
                    density_threshold = 0.5  # 50%阈值（原30%），更宽松

                    # 检测上边缘
                    found_blank_top = False
                    for offset in range(1, padding):
                        check_y = max(0, top - offset)
                        # 扩大检测区域宽度，确保捕获字母标注
                        edge_region = img_array[check_y:check_y+1, max(0, left-10):min(current_width, right+10)]
                        if len(edge_region.shape) > 2:
                            edge_gray = np.mean(edge_region, axis=2)
                        else:
                            edge_gray = edge_region.flatten()
                        edge_std = np.std(edge_gray)
                        if edge_std < crop_std * density_threshold:
                            top = check_y
                            found_blank_top = True
                            logger.info("上边缘检测: 边缘密度=%.2f < 基准密度=%.2f*%.0f%%, 扩展到 y=%s", edge_std, crop_std, density_threshold*100, check_y)
                            break

                    if not found_blank_top:
                        logger.debug("上边缘: 无空白区域，不扩展")

                    # 检测下边缘
                    found_blank_bottom = False
                    for offset in range(1, padding):
                        check_y = min(current_height - 1, bottom + offset)
                        edge_region = img_array[check_y:check_y+1, max(0, left-10):min(current_width, right+10)]
                        if len(edge_region.shape) > 2:
                            edge_gray = np.mean(edge_region, axis=2)
                        else:
                            edge_gray = edge_region.flatten()
                        edge_std = np.std(edge_gray)
                        if edge_std < crop_std * density_threshold:
                            bottom = check_y + 1
                            found_blank_bottom = True
                            logger.info("下边缘检测: 边缘密度=%.2f < 基准密度=%.2f*%.0f%%, 扩展到 y=%s", edge_std, crop_std, density_threshold*100, check_y + 1)
                            break

                    if not found_blank_bottom:
                        logger.debug("下边缘: 无空白区域，不扩展")

                    # 检测左边缘
                    found_blank_left = False
                    for offset in range(1, padding):
                        check_x = max(0, left - offset)
                        # 扩大检测区域高度，确保捕获字母标注
                        edge_region = img_array[max(0, top-10):min(current_height, bottom+10), check_x:check_x+1]
                        if len(edge_region.shape) > 2:
                            edge_gray = np.mean(edge_region, axis=1)
                        else:
                            edge_gray = edge_region.flatten()
                        edge_std = np.std(edge_gray)
                        if edge_std < crop_std * density_threshold:
                            left = check_x
                            found_blank_left = True
                            logger.info("左边缘检测: 边缘密度=%.2f < 基准密度=%.2f*%.0f%%, 扩展到 x=%s", edge_std, crop_std, density_threshold*100, check_x)
                            break

                    if not found_blank_left:
                        logger.debug("左边缘: 无空白区域，不扩展")

                    # 检测右边缘
                    found_blank_right = False
                    for offset in range(1, padding):
                        check_x = min(current_width - 1, right + offset)
                        edge_region = img_array[max(0, top-10):min(current_height, bottom+10), check_x:check_x+1]
                        if len(edge_region.shape) > 2:
                            edge_gray = np.mean(edge_region, axis=1)
                        else:
                            edge_gray = edge_region.flatten()
                        edge_std = np.std(edge_gray)
                        if edge_std < crop_std * density_threshold:
                            right = check_x + 1
                            found_blank_right = True
                            logger.info("右边缘检测: 边缘密度=%.2f < 基准密度=%.2f*%.0f%%, 扩展到 x=%s", edge_std, crop_std, density_threshold*100, check_x + 1)
                            break

                    if not found_blank_right:
                        logger.debug("右边缘: 无空白区域，不扩展")

                    # 如果所有方向都没有扩展，强制添加最小边距
                    if not (found_blank_top or found_blank_bottom or found_blank_left or found_blank_right):
                        min_padding = 15
                        original_coords = [top, left, right, bottom]
                        top = max(0, top - min_padding)
                        left = max(0, left - min_padding)
                        right = min(current_width, right + min_padding)
                        bottom = min(current_height, bottom + min_padding)
                        logger.info("未检测到空白区域，强制添加最小边距: %spx, 坐标从 %s 调整为 [%s, %s, %s, %s]",
                                   min_padding, original_coords, top, left, right, bottom)

                    # 确保坐标有效
                    if left >= right or top >= bottom:
                        logger.warning("无效的裁剪坐标: %s，跳过裁剪", adjusted_crop_box)
                        # 不再使用默认坐标！如果坐标无效，就不裁剪
                        return result

                    final_crop_box = [left, top, right, bottom]
                    logger.info("最终裁剪坐标: %s", final_crop_box)

                    # 裁剪图片
                    cropped_image = image.crop(final_crop_box)
                    metadata['geometry_image'] = cropped_image
                    metadata['geometry_crop_box'] = final_crop_box
                    metadata['has_geometry'] = True
                    logger.info(f"几何图形裁剪成功，尺寸: {cropped_image.size}")
                except Exception as e:
                    logger.error(f"几何图形裁剪失败: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())

            # 如果有SVG内容，渲染并保存到metadata
            elif figure_svg and figure_svg.strip() and geometry_strategy == 'svg':
                logger.info(f"检测到 SVG 内容，长度: {len(figure_svg)} 字符")
                metadata['figure_svg'] = figure_svg
                metadata['has_geometry'] = True

                try:
                    import cairosvg
                    svg_bytes = figure_svg.encode('utf-8')
                    png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=800)
                    geometry_image = Image.open(BytesIO(png_bytes))
                    geometry_image.load()
                    metadata['geometry_image'] = geometry_image
                    logger.info("SVG 图形渲染成功")
                except ImportError:
                    logger.warning("cairosvg 未安装，无法渲染 SVG 图形")
                except Exception as exc:
                    logger.error(f"SVG 图形渲染失败: {exc}")

            return result

        figure_svg = metadata.get('figure_svg')
        geometry_crop_box = metadata.get('geometry_crop_box')

        # 处理裁剪策略
        if geometry_crop_box and geometry_strategy == 'crop':
            logger.info(f"使用裁剪策略，裁剪坐标: {geometry_crop_box}")
            try:
                cropped_image = image.crop(geometry_crop_box)
                metadata['geometry_image'] = cropped_image
                metadata['has_geometry'] = True
                logger.info(f"几何图形裁剪成功，尺寸: {cropped_image.size}")
            except Exception as e:
                logger.error(f"几何图形裁剪失败: {e}")

        # 处理SVG策略
        if isinstance(figure_svg, str):
            figure_svg = figure_svg.strip()
        else:
            figure_svg = ''

        # 尝试解析几何JSON
        geometry_elements = parse_geometry_json(content)

        if geometry_elements and geometry_strategy == 'svg':
            logger.info(f"检测到 {len(geometry_elements)} 个几何元素")
            metadata['geometry_elements'] = geometry_elements
            metadata['has_geometry'] = True

            # 如果几何渲染器可用，生成几何图形
            if GEOMETRY_RENDERER_AVAILABLE:
                try:
                    renderer = GeometryRenderer(width=800, height=600, padding=40)
                    geometry_image = renderer.render_to_pil(geometry_elements)
                    metadata['geometry_image'] = geometry_image
                    logger.info("几何图形渲染成功")
                except Exception as e:
                    logger.error(f"几何图形渲染失败: {e}")
            else:
                logger.warning("几何渲染器不可用，无法生成几何图形")
        elif figure_svg and geometry_strategy == 'svg':
            logger.info("检测到 figure_svg 字段，将尝试渲染 SVG 图形")
            metadata['has_geometry'] = True
            if 'figure_svg' not in metadata:
                metadata['figure_svg'] = figure_svg
            if 'geometry_image' not in metadata:
                try:
                    import cairosvg
                    svg_bytes = figure_svg.encode('utf-8')
                    png_bytes = cairosvg.svg2png(bytestring=svg_bytes)
                    geometry_image = Image.open(BytesIO(png_bytes))
                    geometry_image.load()
                    metadata['geometry_image'] = geometry_image
                    logger.info("SVG 图形渲染成功")
                except ImportError:
                    logger.warning("cairosvg 未安装，无法渲染 SVG 图形")
                except Exception as exc:  # noqa: BLE001
                    logger.error(f"SVG 图形渲染失败: {exc}")
        else:
            # 检查是否有几何关键词但没有几何JSON
            geometry_keywords = ['如图', '图所示', '见图', '下图', '几何图', '立体几何']
            if any(keyword in content for keyword in geometry_keywords):
                logger.warning("检测到几何关键词但未找到几何JSON，可能需要重新生成")

        return result

    @staticmethod
    def _content_lacks_transcription(content: str) -> bool:
        """判定内容是否缺少正文（仅包含代码块或JSON）"""
        stripped = content.strip()
        if not stripped:
            return True
        if stripped.startswith('```'):
            try:
                body = stripped.split('```', 2)[1]
            except IndexError:
                body = ''
            if not re.search(r'[A-Za-z0-9\u4e00-\u9fa5]', body):
                return True
            stripped = body.strip()
        if stripped.lower().startswith('\\begin{tikzpicture}'):
            return True
        if LLMClient._extract_svg_json(stripped):
            return False
        if stripped.startswith('{') or stripped.startswith('['):
            try:
                json.loads(stripped)
                return True
            except json.JSONDecodeError:
                return False
        return False

    def _build_provider_chain(self) -> List[str]:
        """构建用于重试的模型提供商顺序"""
        chain: List[str] = []

        def add(provider: Optional[str]):
            if not provider:
                return
            if provider in chain:
                return
            if self._is_provider_available(provider):
                chain.append(provider)

        add(self.primary_provider)
        add(self.fallback_provider)

        for provider in ['openai', 'gemini', 'anthropic', 'qwen']:
            add(provider)

        return chain

    def _is_provider_available(self, provider: str) -> bool:
        if provider == 'openai':
            return bool(self.openai_client and self.openai_api_key)
        if provider == 'anthropic':
            return bool(self.anthropic_client and self.anthropic_api_key)
        if provider == 'gemini':
            return bool(GEMINI_AVAILABLE and self.gemini_api_key)
        if provider == 'qwen':
            return bool(QWEN_AVAILABLE and self.qwen_api_key)
        return False

    def _log_payload(self, provider: str, payload: dict):
        try:
            serialized = json.dumps(payload, ensure_ascii=False, indent=2)
        except TypeError:
            serialized = str(payload)
        logger.info("LLM Request Payload (%s):\n%s", provider, serialized)

    def _generate_geometry_svg(self, image: Image.Image) -> Optional[str]:
        """调用LLM生成SVG Base64 JSON"""
        providers_to_try = [self.primary_provider]
        if self.fallback_provider and self.fallback_provider not in providers_to_try:
            providers_to_try.append(self.fallback_provider)

        for provider in providers_to_try:
            try:
                if provider == 'qwen' and self.qwen_api_key and QWEN_AVAILABLE:
                    svg_json = self._generate_svg_with_qwen(image)
                elif provider == 'openai' and self.openai_api_key and self.openai_client:
                    svg_json = self._generate_svg_with_openai(image)
                elif provider == 'anthropic' and self.anthropic_api_key and self.anthropic_client:
                    svg_json = self._generate_svg_with_anthropic(image)
                elif provider == 'gemini' and self.gemini_api_key and GEMINI_AVAILABLE:
                    svg_json = self._generate_svg_with_gemini(image)
                else:
                    continue

                if svg_json:
                    svg_json = svg_json.strip()
                    if svg_json.startswith('```'):
                        parts = svg_json.split('```')
                        if len(parts) >= 2:
                            svg_json = parts[1].strip()
                    if not svg_json.startswith('【图形】'):
                        svg_json = f'【图形】\n{svg_json}'
                    if self._extract_svg_json(svg_json):
                        return svg_json
                    logger.warning("生成的SVG内容未通过格式校验，丢弃")
            except Exception as exc:  # noqa: BLE001
                logger.warning("生成SVG时提供商 %s 失败: %s", provider, exc)

        return None

    def _get_geometry_prompts(self) -> Dict[str, str]:
        prompts_cfg = self.config.get('prompts', {}) or {}
        system_prompt = prompts_cfg.get('geometry_svg_system', '').strip()
        user_prompt = prompts_cfg.get('geometry_svg_user', '').strip()

        if not system_prompt:
            system_prompt = (
                "You are an expert vector illustrator."
                " Analyze the provided geometry figure and recreate it precisely as an SVG."
                " Respond ONLY with a JSON object: {\"img_b64\": \"<Base64 SVG>\", \"format\": \"svg\"}."
            )

        if not user_prompt:
            user_prompt = (
                "请根据给定图像生成 SVG，返回 JSON：{\"img_b64\": \"<Base64 SVG>\", \"format\": \"svg\"}"
                " 禁止输出其他任何内容。"
            )

        return {'system': system_prompt, 'user': user_prompt}

    @classmethod
    def _extract_svg_json(cls, text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        match = cls.GEOMETRY_SVG_JSON_PATTERN.search(text)
        if match:
            return match.group(0)
        return None

    @staticmethod
    def _extract_json_payload(raw: str) -> Optional[str]:
        """提取可能包含在代码块中的JSON字符串"""
        stripped = raw.strip()
        if not stripped:
            return None

        if stripped.startswith('```'):
            parts = stripped.split('```')
            for part in parts:
                candidate = part.strip()
                if candidate.startswith('{') and candidate.endswith('}'):
                    return candidate
            return None

        return stripped if stripped.startswith('{') and stripped.endswith('}') else None

    @classmethod
    def _parse_text_svg_json(cls, content: str) -> Optional[Dict[str, str]]:
        """尝试解析LLM返回的 {"text": ..., "geometry_crop_box": ...} 或 {"text": ..., "figure_svg": ...} 结构"""
        try:
            json_candidate = cls._extract_json_payload(content)
            if not json_candidate:
                return None
            payload = json.loads(json_candidate)
        except json.JSONDecodeError:
            return None

        if not isinstance(payload, dict):
            return None

        text_value = payload.get('text')
        figure_svg = payload.get('figure_svg', '')
        geometry_crop_box = payload.get('geometry_crop_box', None)

        if not isinstance(text_value, str):
            return None

        if not isinstance(figure_svg, str):
            figure_svg = ''

        if geometry_crop_box is not None and not isinstance(geometry_crop_box, list):
            geometry_crop_box = None

        return {
            'text': text_value,
            'figure_svg': figure_svg,
            'geometry_crop_box': geometry_crop_box,
            'raw_json': content.strip()
        }

    def _normalize_llm_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """如果LLM返回JSON，解析并提取text/figure_svg/geometry_crop_box"""
        if not result:
            return result

        content = result.get('content')
        if not isinstance(content, str):
            return result

        parsed = self._parse_text_svg_json(content)
        if not parsed:
            return result

        text_value = parsed['text']
        figure_svg = parsed.get('figure_svg', '')
        geometry_crop_box = parsed.get('geometry_crop_box', None)

        result['content'] = text_value

        metadata = result.setdefault('metadata', {})
        metadata.setdefault('raw_llm_json', parsed.get('raw_json', content.strip()))
        metadata.setdefault('figure_svg', figure_svg)
        metadata.setdefault('geometry_crop_box', geometry_crop_box)

        if figure_svg.strip():
            metadata.setdefault('has_geometry', True)
        elif geometry_crop_box:
            metadata.setdefault('has_geometry', True)

        return result

    def _generate_svg_with_qwen(self, image: Image.Image) -> Optional[str]:
        import tempfile

        prompts = self._get_geometry_prompts()
        qwen_config = self.config.get('llm', {}).get('qwen', {})
        model_name = os.getenv('QWEN_MODEL', qwen_config.get('model', 'qwen-vl-plus'))

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            temp_path = tmp_file.name
            image.save(temp_path, format='PNG')

        try:
            messages = [
                {
                    'role': 'system',
                    'content': [{'text': prompts['system']}]
                },
                {
                    'role': 'user',
                    'content': [
                        {'image': f'file://{temp_path}'},
                        {'text': prompts['user']}
                    ]
                }
            ]

            # 获取max_tokens配置
            max_tokens = int(os.getenv('QWEN_MAX_TOKENS', qwen_config.get('max_tokens', 4096)))

            call_kwargs = {
                'model': model_name,
                'messages': messages,
                'max_tokens': max_tokens  # 添加max_tokens参数
            }
            if self._qwen_supports_timeout:
                call_kwargs['timeout'] = self.request_timeout

            self._log_payload('qwen-svg', call_kwargs)
            logger.info("调用Qwen生成SVG Base64...")
            response = MultiModalConversation.call(**call_kwargs)

            if response.status_code != 200:
                raise Exception(f"Qwen SVG生成失败: {response.code} - {response.message}")

            svg_json = response.output.choices[0].message.content[0]['text'].strip()
            logger.info("Qwen返回SVG JSON (前100字符): %s...", svg_json[:100])
            return svg_json
        finally:
            import os as os_module
            if os_module.path.exists(temp_path):
                os_module.unlink(temp_path)

    def _generate_svg_with_openai(self, image: Image.Image) -> Optional[str]:
        return None

    def _generate_svg_with_anthropic(self, image: Image.Image) -> Optional[str]:
        return None

    def _generate_svg_with_gemini(self, image: Image.Image) -> Optional[str]:
        return None
    
    def _analyze_with_openai(self, image: Image.Image) -> Dict[str, Any]:
        """
        使用OpenAI GPT-4 Vision分析图像
        
        Args:
            image: PIL Image对象
            
        Returns:
            分析结果
        """
        if not self.openai_api_key:
            raise ValueError("OpenAI API密钥未设置")
        if not self.openai_client:
            raise RuntimeError("OpenAI客户端未正确初始化")
        
        # 转换图像为base64
        base64_image = self.image_processor.image_to_base64(image)
        
        # 获取配置
        openai_config = self.config.get('llm', {}).get('openai', {})
        model = os.getenv('OPENAI_MODEL', openai_config.get('model', 'gpt-4-vision-preview'))
        max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', openai_config.get('max_tokens', 4096)))
        temperature = openai_config.get('temperature', 0.1)
        detail = openai_config.get('detail', 'high')
        
        # 获取提示词
        system_message = self.config.get('prompts', {}).get('system_message', '')
        user_message = self.config.get('prompts', {}).get('user_message', '')

        # 打印提示词到日志
        logger.info("=" * 80)
        logger.info("OpenAI 提示词:")
        logger.info("-" * 80)
        logger.info(f"System Message:\n{system_message}")
        logger.info("-" * 80)
        logger.info(f"User Message:\n{user_message}")
        logger.info("=" * 80)

        # 调用API
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": detail
                            }
                        }
                    ]
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=self.request_timeout
        )

        content = response.choices[0].message.content
        
        logger.info("=" * 80)
        logger.info("OpenAI LLM 完整输出:")
        logger.info("=" * 80)
        logger.info(content)
        logger.info("=" * 80)
        
        return {
            'provider': 'openai',
            'model': model,
            'content': content,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }
    
    def _analyze_with_anthropic(self, image: Image.Image) -> Dict[str, Any]:
        """
        使用Anthropic Claude 3分析图像
        
        Args:
            image: PIL Image对象
            
        Returns:
            分析结果
        """
        if not self.anthropic_api_key:
            raise ValueError("Anthropic API密钥未设置")
        
        # 转换图像为base64
        base64_image = self.image_processor.image_to_base64(image)
        
        # 获取配置
        anthropic_config = self.config.get('llm', {}).get('anthropic', {})
        model = os.getenv('ANTHROPIC_MODEL', anthropic_config.get('model', 'claude-3-opus-20240229'))
        max_tokens = int(os.getenv('ANTHROPIC_MAX_TOKENS', anthropic_config.get('max_tokens', 4096)))
        temperature = anthropic_config.get('temperature', 0.1)
        
        # 获取提示词
        system_message = self.config.get('prompts', {}).get('system_message', '')
        user_message = self.config.get('prompts', {}).get('user_message', '')

        # 打印提示词到日志
        logger.info("=" * 80)
        logger.info("Anthropic 提示词:")
        logger.info("-" * 80)
        logger.info(f"System Message:\n{system_message}")
        logger.info("-" * 80)
        logger.info(f"User Message:\n{user_message}")
        logger.info("=" * 80)

        # 调用API
        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": user_message
                        }
                    ]
                }
            ],
            timeout=self.request_timeout
        )
        
        content = response.content[0].text
        
        logger.info("=" * 80)
        logger.info("Anthropic LLM 完整输出:")
        logger.info("=" * 80)
        logger.info(content)
        logger.info("=" * 80)
        
        return {
            'provider': 'anthropic',
            'model': model,
            'content': content,
            'usage': {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens
            }
        }

    def _analyze_with_gemini(self, image: Image.Image) -> Dict[str, Any]:
        """
        使用Google Gemini分析图像

        Args:
            image: PIL Image对象

        Returns:
            分析结果
        """
        if not self.gemini_api_key:
            raise ValueError("Gemini API密钥未设置，请在环境变量中提供 GEMINI_API_KEY、AISTUDIO_API_KEY 或 GOOGLE_API_KEY")

        if not GEMINI_AVAILABLE:
            raise ValueError("Google Generative AI库未安装，请运行: pip install google-generativeai")

        # 获取配置
        gemini_config = self.config.get('llm', {}).get('gemini', {})
        model_name = os.getenv('GEMINI_MODEL', gemini_config.get('model', 'gemini-1.5-flash'))
        max_tokens = int(os.getenv('GEMINI_MAX_TOKENS', gemini_config.get('max_tokens', 4096)))
        temperature = gemini_config.get('temperature', 0.1)

        # 获取提示词
        system_message = self.config.get('prompts', {}).get('system_message', '')
        user_message = self.config.get('prompts', {}).get('user_message', '')

        # 打印提示词到日志
        logger.info("=" * 80)
        logger.info("Gemini 提示词:")
        logger.info("-" * 80)
        logger.info(f"System Message:\n{system_message}")
        logger.info("-" * 80)
        logger.info(f"User Message:\n{user_message}")
        logger.info("=" * 80)

        # 创建模型
        model = genai.GenerativeModel(model_name)

        # 准备内容
        prompt = f"{system_message}\n\n{user_message}"

        # 调用API
        request_kwargs = {}
        if self._gemini_request_options is not None:
            request_kwargs['request_options'] = self._gemini_request_options
        elif self._gemini_supports_timeout_kwarg:
            request_kwargs['timeout'] = self.request_timeout

        response = model.generate_content(
            [prompt, image],
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            ),
            **request_kwargs
        )

        content = response.text
        
        logger.info("=" * 80)
        logger.info("Gemini LLM 完整输出:")
        logger.info("=" * 80)
        logger.info(content)
        logger.info("=" * 80)

        # 获取使用统计 (如果可用)
        usage = {}
        if hasattr(response, 'usage_metadata'):
            usage = {
                'prompt_tokens': response.usage_metadata.prompt_token_count,
                'completion_tokens': response.usage_metadata.candidates_token_count,
                'total_tokens': response.usage_metadata.total_token_count
            }

        return {
            'provider': 'gemini',
            'model': model_name,
            'content': content,
            'usage': usage
        }

    def _analyze_with_qwen(self, image: Image.Image) -> Dict[str, Any]:
        """
        使用阿里云通义千问Qwen-VL分析图像

        Args:
            image: PIL Image对象

        Returns:
            分析结果
        """
        if not self.qwen_api_key:
            raise ValueError("Qwen API密钥未设置")

        if not QWEN_AVAILABLE:
            raise ValueError("DashScope库未安装，请运行: pip install dashscope")

        # 保存临时图像文件 (Qwen需要文件路径或URL)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            temp_path = tmp_file.name
            image.save(temp_path, format='PNG')

        try:
            # 获取配置
            qwen_config = self.config.get('llm', {}).get('qwen', {})
            model_name = os.getenv('QWEN_MODEL', qwen_config.get('model', 'qwen-vl-plus'))

            # 获取提示词
            system_message = self.config.get('prompts', {}).get('system_message', '')
            user_message = self.config.get('prompts', {}).get('user_message', '')

            # 打印提示词到日志
            logger.info("=" * 80)
            logger.info("Qwen 提示词:")
            logger.info("-" * 80)
            logger.info(f"System Message:\n{system_message}")
            logger.info("-" * 80)
            logger.info(f"User Message:\n{user_message}")
            logger.info("=" * 80)

            # 准备消息
            messages = [
                {
                    'role': 'system',
                    'content': [{'text': system_message}]
                },
                {
                    'role': 'user',
                    'content': [
                        {'image': f'file://{temp_path}'},
                        {'text': user_message}
                    ]
                }
            ]

            # 获取max_tokens配置
            max_tokens = int(os.getenv('QWEN_MAX_TOKENS', qwen_config.get('max_tokens', 4096)))

            # 调用API
            call_kwargs = {
                'model': model_name,
                'messages': messages,
                'max_tokens': max_tokens  # 添加max_tokens参数
            }
            if self._qwen_supports_timeout:
                call_kwargs['timeout'] = self.request_timeout

            self._log_payload('qwen', call_kwargs)
            response = MultiModalConversation.call(**call_kwargs)

            if response.status_code == 200:
                content = response.output.choices[0].message.content[0]['text']
                
                logger.info("=" * 80)
                logger.info("Qwen LLM 完整输出:")
                logger.info("=" * 80)
                logger.info(content)
                logger.info("=" * 80)

                # 获取使用统计
                usage = {}
                if hasattr(response.usage, 'input_tokens'):
                    usage = {
                        'input_tokens': response.usage.input_tokens,
                        'output_tokens': response.usage.output_tokens
                    }

                return {
                    'provider': 'qwen',
                    'model': model_name,
                    'content': content,
                    'usage': usage
                }
            else:
                raise Exception(f"Qwen API调用失败: {response.code} - {response.message}")

        finally:
            # 清理临时文件
            import os as os_module
            if os_module.path.exists(temp_path):
                os_module.unlink(temp_path)

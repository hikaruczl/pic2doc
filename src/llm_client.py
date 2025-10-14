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

    def analyze_images(self, images: List[Image.Image]) -> List[Dict[str, Any]]:
        """并行或串行分析多张图像"""
        if not images:
            return []

        if len(images) == 1 or not self.concurrent_enabled or self.max_parallel_requests <= 1:
            sequential_results: List[Dict[str, Any]] = []
            for idx, img in enumerate(images):
                logger.info("串行处理图像分片 %s/%s", idx + 1, len(images))
                result = self.analyze_image(img)
                result = self._post_process_geometry(result, img)
                result['segment_index'] = idx
                sequential_results.append(result)
            return sequential_results

        max_workers = max(1, min(self.max_parallel_requests, len(images)))
        results: List[Optional[Dict[str, Any]]] = [None] * len(images)

        def _worker(index: int, img: Image.Image) -> Dict[str, Any]:
            logger.info("并行处理图像分片 %s/%s", index + 1, len(images))
            result = self.analyze_image(img)
            result = self._post_process_geometry(result, img)
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

    def _post_process_geometry(self, result: Dict[str, Any], image: Image.Image) -> Dict[str, Any]:
        """检测并修复几何图形的占位符代码块"""
        content = result.get('content')
        if not content or not isinstance(content, str):
            return result

        metadata = result.setdefault('metadata', {})

        match = self.GEOMETRY_PLACEHOLDER_PATTERN.search(content)
        if match:
            logger.info("检测到几何图占位符，尝试生成TikZ代码替换")
            tikz_block = self._generate_geometry_tikz(image)
            if not tikz_block:
                logger.warning("TikZ生成失败，保留原始占位符内容")
                return result

            tikz_block = self._ensure_tikz_block(tikz_block)
            if not tikz_block:
                logger.warning("生成内容无效，保留占位符")
                return result
            new_content = content[:match.start()] + tikz_block + content[match.end():]
            result['content'] = new_content
            metadata['geometry_tikz_generated'] = True
            logger.info("几何图占位符已替换为生成的TikZ代码")
            return result

        content_lower = content.lower()
        if '\\begin{tikzpicture}' in content_lower or metadata.get('geometry_tikz_generated'):
            return result

        geometry_keywords = ['如图', '图所示', '见图', '下图', '几何图', '立体几何']
        if any(keyword in content for keyword in geometry_keywords):
            logger.info("检测到几何描述但无TikZ代码，尝试补充渲染")
            tikz_block = self._generate_geometry_tikz(image)
            if tikz_block:
                tikz_block = self._ensure_tikz_block(tikz_block)
                if tikz_block:
                    result['content'] = tikz_block + '\n\n' + content
                    metadata['geometry_tikz_generated'] = True
                    logger.info("已在内容前插入生成的TikZ代码")
                else:
                    logger.warning("生成的TikZ内容无效，保留原文本")
            else:
                logger.warning("TikZ生成失败，保留原文本")
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

    def _generate_geometry_tikz(self, image: Image.Image) -> Optional[str]:
        """调用LLM生成TikZ代码"""
        providers_to_try = [self.primary_provider]
        if self.fallback_provider and self.fallback_provider not in providers_to_try:
            providers_to_try.append(self.fallback_provider)

        for provider in providers_to_try:
            try:
                if provider == 'qwen' and self.qwen_api_key and QWEN_AVAILABLE:
                    tikz = self._generate_tikz_with_qwen(image)
                elif provider == 'openai' and self.openai_api_key and self.openai_client:
                    tikz = self._generate_tikz_with_openai(image)
                elif provider == 'anthropic' and self.anthropic_api_key and self.anthropic_client:
                    tikz = self._generate_tikz_with_anthropic(image)
                elif provider == 'gemini' and self.gemini_api_key and GEMINI_AVAILABLE:
                    tikz = self._generate_tikz_with_gemini(image)
                else:
                    continue

                if tikz:
                    return tikz
            except Exception as exc:  # noqa: BLE001
                logger.warning("生成TikZ时提供商 %s 失败: %s", provider, exc)

        return None

    def _get_geometry_prompts(self) -> Dict[str, str]:
        prompts_cfg = self.config.get('prompts', {}) or {}
        system_prompt = prompts_cfg.get('geometry_tikz_system', '').strip()
        user_prompt = prompts_cfg.get('geometry_tikz_user', '').strip()

        if not system_prompt:
            system_prompt = (
                "You are an expert LaTeX TikZ illustrator."
                " Analyze the provided geometry figure and recreate it precisely using TikZ commands."
                " Ensure the code compiles without external files and uses standard libraries only."
                " Respond ONLY with the TikZ code wrapped in ```tikz ... ``` with no explanations."
            )

        if not user_prompt:
            user_prompt = (
                "请根据给定图像生成完整的 TikZ 代码，精确还原所有点、线段、角度与标注。"
                " 仅输出 TikZ 代码，并使用 ```tikz ... ``` 包裹，不要添加其他说明。"
            )

        return {'system': system_prompt, 'user': user_prompt}

    def _generate_tikz_with_qwen(self, image: Image.Image) -> Optional[str]:
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

            call_kwargs = {
                'model': model_name,
                'messages': messages
            }
            if self._qwen_supports_timeout:
                call_kwargs['timeout'] = self.request_timeout

            self._log_payload('qwen-tikz', call_kwargs)
            logger.info("调用Qwen生成TikZ代码...")
            response = MultiModalConversation.call(**call_kwargs)

            if response.status_code != 200:
                raise Exception(f"Qwen TikZ生成失败: {response.code} - {response.message}")

            tikz = response.output.choices[0].message.content[0]['text'].strip()
            logger.info("Qwen返回TikZ代码 (前100字符): %s...", tikz[:100])

            if '\\begin{tikzpicture}' not in tikz:
                logger.warning("Qwen返回的内容不包含tikzpicture环境")
            return tikz
        finally:
            import os as os_module
            if os_module.path.exists(temp_path):
                os_module.unlink(temp_path)

    @staticmethod
    def _ensure_tikz_block(tikz: str) -> str:
        tikz = tikz.strip()
        if '\\begin{tikzpicture}' not in tikz:
            logger.warning("生成的内容不包含tikzpicture环境，忽略插入")
            return ''
        if not tikz.startswith('```'):
            tikz = f'```tikz\n{tikz}\n```'
        return tikz

    def _generate_tikz_with_openai(self, image: Image.Image) -> Optional[str]:
        return None

    def _generate_tikz_with_anthropic(self, image: Image.Image) -> Optional[str]:
        return None

    def _generate_tikz_with_gemini(self, image: Image.Image) -> Optional[str]:
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

            # 调用API
            call_kwargs = {
                'model': model_name,
                'messages': messages
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

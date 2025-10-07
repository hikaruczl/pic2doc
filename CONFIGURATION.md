# 配置指南

本文档详细说明Advanced OCR系统的所有配置选项。

## 配置文件

系统使用两个配置文件:

1. **`.env`** - 环境变量和敏感信息 (API密钥等)
2. **`config/config.yaml`** - 系统配置和参数

---

## 环境变量配置 (.env)

### API密钥配置

```env
# OpenAI API配置
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-vision-preview
OPENAI_MAX_TOKENS=4096

# Anthropic Claude API配置
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Google Gemini API配置
GEMINI_API_KEY=your-gemini-key-here
GEMINI_MODEL=gemini-1.5-flash
GEMINI_MAX_TOKENS=4096

# Alibaba Qwen-VL API配置
QWEN_API_KEY=your-qwen-key-here
QWEN_MODEL=qwen-vl-plus
```

**说明:**
- `OPENAI_API_KEY`: OpenAI API密钥 (必需,如果使用OpenAI)
- `OPENAI_MODEL`: 使用的OpenAI模型,默认 `gpt-4-vision-preview`
- `ANTHROPIC_API_KEY`: Anthropic API密钥 (必需,如果使用Claude)
- `ANTHROPIC_MODEL`: 使用的Claude模型,可选:
  - `claude-3-opus-20240229` (最强,最贵)
  - `claude-3-sonnet-20240229` (平衡) ⭐推荐
  - `claude-3-haiku-20240307` (最快,最便宜)
- `GEMINI_API_KEY`: Google Gemini API密钥 (必需,如果使用Gemini)
- `GEMINI_MODEL`: 使用的Gemini模型,可选:
  - `gemini-1.5-pro` (高准确率)
  - `gemini-1.5-flash` (性价比之王) ⭐⭐推荐
- `QWEN_API_KEY`: 阿里云通义千问API密钥 (必需,如果使用Qwen)
- `QWEN_MODEL`: 使用的Qwen模型,可选:
  - `qwen-vl-max` (高准确率)
  - `qwen-vl-plus` (平衡)

### LLM提供商选择

```env
# 主要LLM提供商
PRIMARY_LLM_PROVIDER=gemini

# 备用LLM提供商
FALLBACK_LLM_PROVIDER=qwen
```

**说明:**
- `PRIMARY_LLM_PROVIDER`: 主要使用的提供商 (`openai`, `anthropic`, `gemini`, 或 `qwen`)
- `FALLBACK_LLM_PROVIDER`: 主要提供商失败时的备用选项 (`openai`, `anthropic`, `gemini`, `qwen`, 或 `none`)

**推荐配置:**
- **性价比最高**: `PRIMARY=gemini` (Flash), `FALLBACK=qwen` ⭐⭐推荐
- **平衡方案**: `PRIMARY=anthropic` (Sonnet), `FALLBACK=gemini` ⭐推荐
- **高准确度**: `PRIMARY=anthropic` (Opus), `FALLBACK=openai`
- **国内优化**: `PRIMARY=qwen` (Max), `FALLBACK=gemini`
- **成本最低**: `PRIMARY=gemini` (Flash), `FALLBACK=none`

详见: [MODEL_COMPARISON.md](MODEL_COMPARISON.md)

### API设置

```env
API_TIMEOUT=60
API_MAX_RETRIES=3
API_RETRY_DELAY=2
```

**说明:**
- `API_TIMEOUT`: API调用超时时间 (秒)
- `API_MAX_RETRIES`: 失败后的最大重试次数
- `API_RETRY_DELAY`: 重试之间的延迟 (秒)

### 图像处理设置

```env
MAX_IMAGE_SIZE_MB=10
SUPPORTED_IMAGE_FORMATS=png,jpg,jpeg,pdf
IMAGE_QUALITY=95
```

**说明:**
- `MAX_IMAGE_SIZE_MB`: 允许的最大图像大小 (MB)
- `SUPPORTED_IMAGE_FORMATS`: 支持的图像格式 (逗号分隔)
- `IMAGE_QUALITY`: 保存图像的质量 (1-100)

### 输出设置

```env
OUTPUT_DIR=output
LOG_DIR=logs
LOG_LEVEL=INFO
```

**说明:**
- `OUTPUT_DIR`: 输出文件目录
- `LOG_DIR`: 日志文件目录
- `LOG_LEVEL`: 日志级别 (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)

---

## YAML配置文件 (config/config.yaml)

### LLM配置

```yaml
llm:
  primary_provider: "openai"
  fallback_provider: "anthropic"
  
  openai:
    model: "gpt-4-vision-preview"
    max_tokens: 4096
    temperature: 0.1
    detail: "high"  # low, high, or auto
    
  anthropic:
    model: "claude-3-opus-20240229"
    max_tokens: 4096
    temperature: 0.1
  
  retry:
    max_attempts: 3
    delay_seconds: 2
    backoff_multiplier: 2
```

**参数说明:**

**OpenAI配置:**
- `model`: 模型名称
- `max_tokens`: 最大生成token数
- `temperature`: 温度参数 (0-1),越低越确定
- `detail`: 图像分析详细程度
  - `low`: 低分辨率,更快,更便宜
  - `high`: 高分辨率,更准确,更贵
  - `auto`: 自动选择

**Anthropic配置:**
- `model`: 模型名称
- `max_tokens`: 最大生成token数
- `temperature`: 温度参数

**重试配置:**
- `max_attempts`: 最大重试次数
- `delay_seconds`: 初始延迟时间
- `backoff_multiplier`: 延迟倍增因子 (指数退避)

### 图像处理配置

```yaml
image:
  max_size_mb: 10
  supported_formats:
    - png
    - jpg
    - jpeg
    - pdf
  quality: 95
  preprocessing:
    resize_if_large: true
    max_dimension: 2048
    enhance_contrast: false
    denoise: false
```

**参数说明:**
- `max_size_mb`: 最大文件大小
- `supported_formats`: 支持的格式列表
- `quality`: 图像质量 (1-100)
- `preprocessing.resize_if_large`: 是否调整大图像
- `preprocessing.max_dimension`: 最大尺寸 (像素)
- `preprocessing.enhance_contrast`: 是否增强对比度
- `preprocessing.denoise`: 是否降噪

**性能优化建议:**
- 启用 `resize_if_large` 可减少API费用
- `max_dimension` 设为 2048 通常足够
- 仅在图像质量差时启用 `enhance_contrast` 和 `denoise`

### 公式转换配置

```yaml
formula:
  output_format: "mathml"
  preserve_latex: true
  inline_formulas: true
```

**参数说明:**
- `output_format`: 输出格式 (`mathml` 或 `latex`)
- `preserve_latex`: 是否在文档中保留LaTeX源码
- `inline_formulas`: 是否支持行内公式

### 文档生成配置

```yaml
document:
  default_font: "Arial"
  default_font_size: 11
  heading_font_size: 14
  include_original_image: true
  image_width_inches: 6.0
  page_margins:
    top: 1.0
    bottom: 1.0
    left: 1.0
    right: 1.0
```

**参数说明:**
- `default_font`: 默认字体
- `default_font_size`: 正文字体大小 (磅)
- `heading_font_size`: 标题字体大小
- `include_original_image`: 是否包含原始图像
- `image_width_inches`: 图像宽度 (英寸)
- `page_margins`: 页边距 (英寸)

### 提示词配置

```yaml
prompts:
  system_message: |
    You are an expert at analyzing mathematical content from images.
    Extract all text, mathematical formulas, and diagrams from the image.
    Return formulas in LaTeX format enclosed in $ for inline or $$ for display formulas.
    Preserve the structure and layout of the content.
    
  user_message: |
    Please analyze this image of a math problem and:
    1. Extract all text content
    2. Convert all mathematical formulas to LaTeX format
    3. Describe any diagrams or figures
    4. Preserve the original structure and layout
```

**自定义提示词:**
- 可以根据需要修改提示词以获得更好的结果
- 确保提示词中包含LaTeX格式要求
- 可以添加特定领域的指令

### 日志配置

```yaml
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_rotation: true
  max_bytes: 10485760  # 10MB
  backup_count: 5
  console_output: true
```

**参数说明:**
- `level`: 日志级别
- `format`: 日志格式
- `file_rotation`: 是否启用日志轮转
- `max_bytes`: 单个日志文件最大大小
- `backup_count`: 保留的日志文件数量
- `console_output`: 是否输出到控制台

### 输出配置

```yaml
output:
  directory: "output"
  filename_pattern: "math_problem_{timestamp}.docx"
  save_intermediate: false
```

**参数说明:**
- `directory`: 输出目录
- `filename_pattern`: 文件名模式,支持 `{timestamp}` 占位符
- `save_intermediate`: 是否保存中间文件 (LaTeX等)

---

## 配置示例

### 示例1: 高准确度配置

```yaml
llm:
  primary_provider: "openai"
  openai:
    model: "gpt-4-vision-preview"
    detail: "high"
    temperature: 0.0

image:
  preprocessing:
    resize_if_large: false
    enhance_contrast: true
```

### 示例2: 成本优化配置

```yaml
llm:
  primary_provider: "anthropic"
  anthropic:
    model: "claude-3-haiku-20240307"
  fallback_provider: null

image:
  preprocessing:
    resize_if_large: true
    max_dimension: 1024
```

### 示例3: 批量处理配置

```yaml
llm:
  retry:
    max_attempts: 5
    delay_seconds: 3

performance:
  parallel_processing: true
  cache_api_responses: true
```

---

## 配置优先级

配置的优先级顺序 (从高到低):

1. 环境变量 (`.env`)
2. YAML配置文件 (`config/config.yaml`)
3. 代码中的默认值

**示例:**
```python
# .env 中设置
PRIMARY_LLM_PROVIDER=openai

# config.yaml 中设置
llm:
  primary_provider: "anthropic"

# 实际使用: openai (环境变量优先)
```

---

## 最佳实践

1. **敏感信息**: 始终将API密钥放在 `.env` 文件中,不要提交到版本控制
2. **环境区分**: 为不同环境创建不同的配置文件
   - `config/config.dev.yaml`
   - `config/config.prod.yaml`
3. **备份配置**: 定期备份配置文件
4. **文档化**: 记录自定义配置的原因和效果

---

## 故障排除

### 配置未生效

**检查清单:**
- [ ] 确认配置文件路径正确
- [ ] 检查YAML语法是否正确
- [ ] 验证环境变量是否已加载
- [ ] 重启应用程序

### 性能问题

**优化建议:**
- 启用图像调整: `resize_if_large: true`
- 降低图像质量: `quality: 85`
- 使用更快的模型: `claude-3-haiku`

### API费用过高

**节省建议:**
- 使用 `detail: low` (OpenAI)
- 减小 `max_dimension`
- 使用更便宜的模型
- 启用缓存 (如果可用)

---

更多信息请参考:
- [README.md](README.md)
- [API.md](API.md)
- [example.py](example.py)


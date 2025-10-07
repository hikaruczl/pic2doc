# Advanced OCR - 数学问题图像转Word文档系统

一个强大的OCR系统,可以将数学问题图像转换为可编辑的Word文档,支持公式识别和格式化。

## ✨ 主要特性

- 🖼️ **多格式支持**: 支持PNG, JPG, JPEG, PDF等图像格式
- 🤖 **多模态LLM**: 集成GPT-4 Vision, Claude 3, Gemini, Qwen-VL,支持自动切换和容错
- 📐 **公式识别**: 自动识别并转换数学公式为LaTeX和MathML格式
- 📄 **Word生成**: 生成包含公式、文本和图像的完整Word文档
- 🔄 **批量处理**: 支持批量处理多个图像文件
- 🌐 **Web界面**: 提供Gradio和FastAPI两种Web界面方案
- 🛡️ **错误处理**: 完善的错误处理和重试机制
- 📊 **日志系统**: 详细的日志记录和彩色控制台输出

## 🏗️ 系统架构

```
┌─────────────────┐
│  图像输入       │
│ (PNG/JPG/PDF)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 图像预处理      │
│ - 验证          │
│ - 格式转换      │
│ - 尺寸调整      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM分析         │
│ - GPT-4 Vision  │
│ - Claude 3      │
│ - Gemini        │
│ - Qwen-VL       │
│ - 容错切换      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 公式转换        │
│ - LaTeX解析     │
│ - MathML转换    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Word文档生成    │
│ - 格式化        │
│ - 公式插入      │
│ - 图像嵌入      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Word文档输出   │
└─────────────────┘
```

## 📦 安装

### 1. 克隆仓库

```bash
git clone <repository-url>
cd advanceOCR
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 系统依赖 (可选)

对于PDF处理,需要安装poppler:

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Windows:**
下载并安装 [poppler for Windows](http://blog.alivate.com.au/poppler-windows/)

## ⚙️ 配置

### 1. 创建环境变量文件

```bash
cp .env.example .env
```

### 2. 配置API密钥

编辑 `.env` 文件,添加你的API密钥:

```env
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-vision-preview

# Anthropic Claude API配置
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-opus-20240229

# 主要LLM提供商 (openai 或 anthropic)
PRIMARY_LLM_PROVIDER=openai

# 备用LLM提供商 (openai, anthropic 或 none)
FALLBACK_LLM_PROVIDER=anthropic
```

### 3. 自定义配置 (可选)

编辑 `config/config.yaml` 来自定义系统行为:

- LLM提供商设置
- 图像处理参数
- 公式转换选项
- 文档格式设置
- 日志配置

## 🚀 使用方法

### 🌐 Web界面使用 (推荐)

#### 方式1: Gradio界面 (最简单)

```bash
# 启动Web界面
python web_app.py
```

访问: http://localhost:7860

- ✅ 零配置,开箱即用
- ✅ 美观的现代化界面
- ✅ 支持拖拽上传
- ✅ 实时进度显示

详见: [WEB_GUIDE.md](WEB_GUIDE.md)

#### 方式2: FastAPI后端

```bash
# 启动API服务
python web/backend/app.py
```

API文档: http://localhost:8000/docs

- ✅ RESTful API设计
- ✅ 异步处理
- ✅ 适合集成

### 命令行使用

```bash
# 基本用法
python -m src.main path/to/image.png

# 指定输出文件名
python -m src.main path/to/image.png -o output.docx

# 使用自定义配置
python -m src.main path/to/image.png -c custom_config.yaml
```

### Python API使用

```python
from src.main import AdvancedOCR

# 创建OCR实例
ocr = AdvancedOCR(config_path='config/config.yaml')

# 处理单个图像
result = ocr.process_image('path/to/image.png')

if result['success']:
    print(f"输出文件: {result['output_path']}")
    print(f"公式数量: {result['statistics']['total_formulas']}")
else:
    print(f"错误: {result['error']}")

# 批量处理
image_paths = ['image1.png', 'image2.jpg', 'image3.pdf']
results = ocr.process_batch(image_paths)
```

### 使用示例

运行示例代码:

```bash
python example.py
```

示例包括:
- 基本使用
- 自定义输出
- 批量处理
- 组件单独使用
- 错误处理

## 📚 API文档

### AdvancedOCR 类

主要的OCR系统类。

#### 方法

**`__init__(config_path: str = 'config/config.yaml')`**
- 初始化OCR系统
- 参数: `config_path` - 配置文件路径

**`process_image(image_path: str, output_filename: Optional[str] = None) -> dict`**
- 处理单个图像文件
- 参数:
  - `image_path`: 图像文件路径
  - `output_filename`: 输出文件名(可选)
- 返回: 包含处理结果的字典

**`process_batch(image_paths: List[str]) -> List[dict]`**
- 批量处理多个图像
- 参数: `image_paths` - 图像文件路径列表
- 返回: 处理结果列表

### ImageProcessor 类

图像预处理组件。

#### 方法

**`validate_image(image_path: str) -> Tuple[bool, Optional[str]]`**
- 验证图像文件
- 返回: (是否有效, 错误信息)

**`process_image(image_path: str) -> List[Image.Image]`**
- 处理图像文件
- 返回: PIL Image对象列表

### LLMClient 类

LLM API客户端组件。

#### 方法

**`analyze_image(image: Image.Image) -> Dict[str, Any]`**
- 使用LLM分析图像
- 返回: 包含分析结果的字典

### FormulaConverter 类

公式转换组件。

#### 方法

**`parse_content(content: str) -> List[Dict]`**
- 解析内容,提取文本和公式
- 返回: 结构化元素列表

**`extract_formulas(content: str) -> List[Tuple[str, str]]`**
- 提取所有公式
- 返回: (公式类型, LaTeX) 元组列表

**`convert_latex_to_mathml(latex: str) -> str`**
- 转换LaTeX为MathML
- 返回: MathML字符串

### DocumentGenerator 类

Word文档生成组件。

#### 方法

**`create_document(elements: List[Dict], ...) -> Document`**
- 创建Word文档
- 返回: Document对象

**`save_document(doc: Document, filename: Optional[str] = None) -> str`**
- 保存文档到文件
- 返回: 文件路径

## 🧪 测试

运行单元测试:

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_image_processor.py

# 运行测试并显示覆盖率
pytest --cov=src tests/
```

## 📁 项目结构

```
advanceOCR/
├── config/
│   └── config.yaml          # 配置文件
├── src/
│   ├── __init__.py
│   ├── image_processor.py   # 图像预处理
│   ├── llm_client.py        # LLM API客户端
│   ├── formula_converter.py # 公式格式转换
│   ├── document_generator.py# Word文档生成
│   └── main.py              # 主程序入口
├── tests/
│   ├── test_image_processor.py
│   ├── test_formula_converter.py
│   └── sample_images/       # 测试图片
├── output/                  # 输出目录
├── logs/                    # 日志目录
├── .env.example             # 环境变量模板
├── requirements.txt         # 依赖列表
├── example.py               # 使用示例
└── README.md                # 本文件
```

## 🔧 技术栈

- **Python 3.8+**
- **LLM APIs**: OpenAI GPT-4 Vision, Anthropic Claude 3
- **图像处理**: Pillow, OpenCV, pdf2image
- **文档生成**: python-docx
- **公式转换**: latex2mathml
- **配置管理**: PyYAML, python-dotenv
- **日志**: colorlog
- **测试**: pytest

## ⚠️ 注意事项

1. **API费用**: 使用GPT-4 Vision和Claude 3会产生API调用费用,请注意控制使用量
2. **图像质量**: 图像质量越高,识别准确度越高
3. **公式复杂度**: 极其复杂的公式可能需要手动调整
4. **PDF处理**: PDF文件会被转换为图像,可能影响质量

## 🐛 故障排除

### 问题: API调用失败

**解决方案:**
- 检查API密钥是否正确
- 检查网络连接
- 查看日志文件了解详细错误信息

### 问题: PDF处理失败

**解决方案:**
- 确保已安装poppler
- 检查PDF文件是否损坏

### 问题: 公式转换错误

**解决方案:**
- 检查LaTeX语法是否正确
- 查看日志中的详细错误信息
- 某些复杂公式可能需要手动调整

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request!

## 📧 联系方式

如有问题或建议,请通过Issue联系我们。


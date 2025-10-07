# API 文档

Advanced OCR系统的详细API文档。

## 目录

- [核心类](#核心类)
  - [AdvancedOCR](#advancedocr)
  - [ImageProcessor](#imageprocessor)
  - [LLMClient](#llmclient)
  - [FormulaConverter](#formulaconverter)
  - [DocumentGenerator](#documentgenerator)
- [数据结构](#数据结构)
- [配置选项](#配置选项)
- [错误处理](#错误处理)

---

## 核心类

### AdvancedOCR

主要的OCR系统类,整合所有功能模块。

#### 构造函数

```python
AdvancedOCR(config_path: str = 'config/config.yaml')
```

**参数:**
- `config_path` (str): 配置文件路径,默认为 `'config/config.yaml'`

**示例:**
```python
from src.main import AdvancedOCR

ocr = AdvancedOCR()
# 或使用自定义配置
ocr = AdvancedOCR(config_path='my_config.yaml')
```

#### 方法

##### process_image()

处理单个图像文件。

```python
process_image(image_path: str, output_filename: Optional[str] = None) -> dict
```

**参数:**
- `image_path` (str): 图像文件路径
- `output_filename` (Optional[str]): 输出文件名,默认使用时间戳

**返回:**
```python
{
    'success': bool,           # 是否成功
    'output_path': str,        # 输出文件路径 (成功时)
    'analysis': dict,          # LLM分析结果 (成功时)
    'statistics': dict,        # 公式统计信息 (成功时)
    'elements_count': int,     # 元素数量 (成功时)
    'error': str              # 错误信息 (失败时)
}
```

**示例:**
```python
result = ocr.process_image('math_problem.png')
if result['success']:
    print(f"输出: {result['output_path']}")
else:
    print(f"错误: {result['error']}")
```

##### process_batch()

批量处理多个图像文件。

```python
process_batch(image_paths: List[str]) -> List[dict]
```

**参数:**
- `image_paths` (List[str]): 图像文件路径列表

**返回:**
- List[dict]: 每个图像的处理结果列表

**示例:**
```python
results = ocr.process_batch(['img1.png', 'img2.jpg'])
for result in results:
    if result['success']:
        print(f"✓ {result['output_path']}")
```

---

### ImageProcessor

图像预处理和验证组件。

#### 构造函数

```python
ImageProcessor(config: dict)
```

**参数:**
- `config` (dict): 配置字典

#### 方法

##### validate_image()

验证图像文件是否有效。

```python
validate_image(image_path: str) -> Tuple[bool, Optional[str]]
```

**参数:**
- `image_path` (str): 图像文件路径

**返回:**
- Tuple[bool, Optional[str]]: (是否有效, 错误信息)

**示例:**
```python
is_valid, error = processor.validate_image('test.png')
if not is_valid:
    print(f"验证失败: {error}")
```

##### process_image()

处理图像文件,返回PIL Image对象列表。

```python
process_image(image_path: str) -> List[Image.Image]
```

**参数:**
- `image_path` (str): 图像文件路径

**返回:**
- List[Image.Image]: PIL Image对象列表 (PDF可能有多页)

**示例:**
```python
images = processor.process_image('document.pdf')
print(f"处理了 {len(images)} 页")
```

##### image_to_base64()

将PIL Image转换为base64字符串。

```python
image_to_base64(image: Image.Image) -> str
```

**参数:**
- `image` (Image.Image): PIL Image对象

**返回:**
- str: base64编码的字符串

##### save_image()

保存图像到文件。

```python
save_image(image: Image.Image, output_path: str) -> str
```

**参数:**
- `image` (Image.Image): PIL Image对象
- `output_path` (str): 输出路径

**返回:**
- str: 保存的文件路径

---

### LLMClient

LLM API客户端,支持OpenAI和Anthropic。

#### 构造函数

```python
LLMClient(config: dict, image_processor: ImageProcessor)
```

**参数:**
- `config` (dict): 配置字典
- `image_processor` (ImageProcessor): 图像处理器实例

#### 方法

##### analyze_image()

使用LLM分析图像并提取数学内容。

```python
analyze_image(image: Image.Image) -> Dict[str, Any]
```

**参数:**
- `image` (Image.Image): PIL Image对象

**返回:**
```python
{
    'provider': str,        # 使用的提供商 ('openai' 或 'anthropic')
    'model': str,          # 使用的模型名称
    'content': str,        # 提取的内容
    'usage': dict         # API使用统计
}
```

**示例:**
```python
result = llm_client.analyze_image(image)
print(f"使用模型: {result['model']}")
print(f"内容: {result['content']}")
```

---

### FormulaConverter

公式格式转换组件。

#### 构造函数

```python
FormulaConverter(config: dict)
```

**参数:**
- `config` (dict): 配置字典

#### 方法

##### parse_content()

解析内容,提取文本和公式。

```python
parse_content(content: str) -> List[Dict]
```

**参数:**
- `content` (str): LLM返回的内容

**返回:**
```python
[
    {
        'type': 'text',      # 或 'formula'
        'content': str       # 文本内容 (type='text')
    },
    {
        'type': 'formula',
        'formula_type': str, # 'inline' 或 'display'
        'latex': str,        # LaTeX源码
        'mathml': str       # MathML格式
    }
]
```

##### extract_formulas()

从内容中提取所有公式。

```python
extract_formulas(content: str) -> List[Tuple[str, str]]
```

**参数:**
- `content` (str): 文本内容

**返回:**
- List[Tuple[str, str]]: (公式类型, LaTeX) 元组列表

**示例:**
```python
formulas = converter.extract_formulas(content)
for formula_type, latex in formulas:
    print(f"{formula_type}: {latex}")
```

##### convert_latex_to_mathml()

将LaTeX转换为MathML。

```python
convert_latex_to_mathml(latex: str) -> str
```

**参数:**
- `latex` (str): LaTeX公式

**返回:**
- str: MathML字符串

##### get_formula_statistics()

获取公式统计信息。

```python
get_formula_statistics(content: str) -> Dict
```

**参数:**
- `content` (str): 文本内容

**返回:**
```python
{
    'total_formulas': int,      # 总公式数
    'display_formulas': int,    # 显示公式数
    'inline_formulas': int,     # 行内公式数
    'formulas': List[Tuple]    # 公式列表
}
```

---

### DocumentGenerator

Word文档生成组件。

#### 构造函数

```python
DocumentGenerator(config: dict)
```

**参数:**
- `config` (dict): 配置字典

#### 方法

##### create_document()

创建Word文档。

```python
create_document(
    elements: List[Dict],
    original_image: Optional[Image.Image] = None,
    metadata: Optional[Dict] = None
) -> Document
```

**参数:**
- `elements` (List[Dict]): 格式化的元素列表
- `original_image` (Optional[Image.Image]): 原始图像
- `metadata` (Optional[Dict]): 元数据

**返回:**
- Document: python-docx Document对象

##### save_document()

保存文档到文件。

```python
save_document(doc: Document, filename: Optional[str] = None) -> str
```

**参数:**
- `doc` (Document): Document对象
- `filename` (Optional[str]): 文件名

**返回:**
- str: 保存的文件路径

##### create_from_analysis()

从分析结果创建并保存文档。

```python
create_from_analysis(
    analysis_result: Dict,
    original_image: Image.Image,
    elements: List[Dict]
) -> str
```

**参数:**
- `analysis_result` (Dict): LLM分析结果
- `original_image` (Image.Image): 原始图像
- `elements` (List[Dict]): 格式化的元素列表

**返回:**
- str: 保存的文件路径

---

## 数据结构

### 配置字典结构

```python
{
    'llm': {
        'primary_provider': str,
        'fallback_provider': str,
        'openai': {...},
        'anthropic': {...},
        'retry': {...}
    },
    'image': {
        'max_size_mb': int,
        'quality': int,
        'preprocessing': {...}
    },
    'formula': {
        'output_format': str,
        'preserve_latex': bool
    },
    'document': {
        'default_font': str,
        'default_font_size': int,
        ...
    }
}
```

---

## 配置选项

详细配置选项请参考 `config/config.yaml` 文件。

主要配置项:

- **llm.primary_provider**: 主要LLM提供商 (`'openai'` 或 `'anthropic'`)
- **llm.fallback_provider**: 备用提供商
- **image.max_size_mb**: 最大图像大小 (MB)
- **formula.output_format**: 公式输出格式 (`'mathml'` 或 `'latex'`)
- **document.include_original_image**: 是否包含原始图像

---

## 错误处理

所有方法都包含适当的错误处理。主要异常类型:

- **ValueError**: 参数无效
- **FileNotFoundError**: 文件不存在
- **IOError**: 文件读写错误
- **Exception**: API调用失败或其他错误

**最佳实践:**

```python
try:
    result = ocr.process_image('test.png')
    if result['success']:
        # 处理成功
        pass
    else:
        # 处理失败,查看错误信息
        print(result['error'])
except Exception as e:
    # 处理异常
    print(f"发生异常: {str(e)}")
```

---

## 完整示例

```python
from src.main import AdvancedOCR
from src.image_processor import ImageProcessor
from src.formula_converter import FormulaConverter
import yaml

# 加载配置
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# 方式1: 使用主类 (推荐)
ocr = AdvancedOCR()
result = ocr.process_image('math.png')

# 方式2: 单独使用组件
processor = ImageProcessor(config)
converter = FormulaConverter(config)

# 验证图像
is_valid, error = processor.validate_image('math.png')
if is_valid:
    # 处理图像
    images = processor.process_image('math.png')
    
    # 分析内容 (假设已有content)
    elements = converter.parse_content(content)
    stats = converter.get_formula_statistics(content)
    
    print(f"找到 {stats['total_formulas']} 个公式")
```

---

更多信息请参考:
- [README.md](README.md) - 使用说明
- [example.py](example.py) - 示例代码
- 源代码注释


# 快速开始指南

5分钟快速上手Advanced OCR系统!

## 🚀 快速安装

```bash
# 1. 克隆项目
git clone <repository-url>
cd advanceOCR

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置API密钥
cp .env.example .env
# 编辑.env文件,添加你的API密钥
```

## 🔑 获取API密钥

### 选项1: OpenAI (推荐)

1. 访问 https://platform.openai.com/api-keys
2. 创建API密钥
3. 在 `.env` 中设置:
   ```
   OPENAI_API_KEY=sk-your-key-here
   PRIMARY_LLM_PROVIDER=openai
   ```

### 选项2: Anthropic Claude

1. 访问 https://console.anthropic.com/
2. 创建API密钥
3. 在 `.env` 中设置:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   PRIMARY_LLM_PROVIDER=anthropic
   ```

## 📝 第一个示例

### 1. 准备测试图像

将包含数学问题的图像放到项目目录,例如 `test_math.png`

### 2. 运行处理

```bash
python -m src.main test_math.png
```

### 3. 查看结果

处理完成后,在 `output/` 目录下找到生成的Word文档!

## 💻 Python代码示例

创建 `my_test.py`:

```python
from src.main import AdvancedOCR

# 初始化
ocr = AdvancedOCR()

# 处理图像
result = ocr.process_image('test_math.png')

# 查看结果
if result['success']:
    print(f"✓ 成功!")
    print(f"输出: {result['output_path']}")
    print(f"公式数: {result['statistics']['total_formulas']}")
else:
    print(f"✗ 失败: {result['error']}")
```

运行:
```bash
python my_test.py
```

## 📊 示例输入输出

### 输入图像示例

假设你有一张包含以下内容的图像:

```
问题: 求解方程
x² + 5x + 6 = 0

解答:
使用求根公式: x = (-b ± √(b²-4ac)) / 2a
```

### 输出Word文档

系统会生成包含以下内容的Word文档:

- 原始图像
- 识别的文本
- 格式化的数学公式 (可编辑)
- LaTeX源码 (注释形式)

## 🎯 常用命令

```bash
# 基本使用
python -m src.main image.png

# 指定输出文件名
python -m src.main image.png -o my_output.docx

# 批量处理
python -c "
from src.main import AdvancedOCR
ocr = AdvancedOCR()
ocr.process_batch(['img1.png', 'img2.jpg', 'img3.pdf'])
"

# 运行测试
pytest tests/ -v

# 查看示例
python example.py
```

## ⚙️ 基本配置

编辑 `config/config.yaml` 自定义设置:

```yaml
# 选择主要LLM提供商
llm:
  primary_provider: "openai"  # 或 "anthropic"
  
# 图像设置
image:
  max_size_mb: 10
  quality: 95

# 文档设置
document:
  include_original_image: true
  default_font: "Arial"
```

## 🔍 验证安装

运行以下命令确保一切正常:

```bash
# 测试导入
python -c "from src.main import AdvancedOCR; print('✓ 导入成功')"

# 运行单元测试
pytest tests/test_image_processor.py -v

# 查看配置
python -c "
import yaml
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)
    print('✓ 配置加载成功')
    print(f'主要提供商: {config[\"llm\"][\"primary_provider\"]}')
"
```

## 📁 项目结构速览

```
advanceOCR/
├── src/                    # 源代码
│   ├── main.py            # 主入口
│   ├── image_processor.py # 图像处理
│   ├── llm_client.py      # LLM客户端
│   ├── formula_converter.py # 公式转换
│   └── document_generator.py # 文档生成
├── config/
│   └── config.yaml        # 配置文件
├── tests/                 # 测试文件
├── output/                # 输出目录
├── .env                   # 环境变量 (需创建)
└── example.py             # 使用示例
```

## 🎓 学习路径

1. **新手**: 
   - 运行 `python example.py` 查看所有示例
   - 阅读 `README.md` 了解详细功能

2. **进阶**:
   - 修改 `config/config.yaml` 自定义行为
   - 查看 `src/` 目录了解各模块功能

3. **高级**:
   - 阅读源代码了解实现细节
   - 扩展功能或集成到自己的项目

## ⚠️ 常见问题

### Q: API调用失败?
**A**: 检查 `.env` 文件中的API密钥是否正确,确保有网络连接

### Q: 找不到模块?
**A**: 确保已安装所有依赖: `pip install -r requirements.txt`

### Q: PDF处理失败?
**A**: 需要安装poppler,参见 [INSTALL.md](INSTALL.md)

### Q: 公式识别不准确?
**A**: 
- 确保图像清晰
- 尝试使用不同的LLM提供商
- 调整图像预处理参数

## 💡 提示和技巧

1. **提高识别准确度**:
   - 使用高分辨率图像
   - 确保图像清晰,对比度高
   - 避免图像倾斜或变形

2. **节省API费用**:
   - 使用较小的图像
   - 批量处理时注意控制数量
   - 考虑使用Claude (通常更便宜)

3. **优化性能**:
   - 启用图像预处理中的resize选项
   - 调整max_dimension参数

4. **调试问题**:
   - 查看 `logs/` 目录下的日志文件
   - 设置 `LOG_LEVEL=DEBUG` 获取详细信息

## 📚 下一步

- 📖 阅读完整文档: [README.md](README.md)
- 🔧 详细安装指南: [INSTALL.md](INSTALL.md)
- 💻 查看代码示例: [example.py](example.py)
- 🧪 运行测试: `pytest tests/ -v`

## 🆘 获取帮助

- 查看项目Issues
- 阅读文档
- 提交新Issue (附上详细错误信息)

---

**祝你使用愉快! 🎉**


# 数学符号识别问题修复说明

## 问题描述

从用户提供的对比图片可以看出，OCR系统在识别以下数学符号时存在问题：
1. **求和符号（Σ）**：没有使用正确的 `\sum_{i=1}^{N}` LaTeX格式
2. **平均值符号（上划线）**：没有使用 `\bar{Y}` 或 `\overline{Y}` 格式
3. **分数表示**：没有使用 `\frac{分子}{分母}` 格式

## 解决方案

### 1. 改进提示词（已完成）

修改了 `config/config.yaml` 中的提示词，增加了以下明确指导：

**系统消息中新增：**
```
IMPORTANT: Pay special attention to mathematical notation:
- Summation symbols (Σ): use \sum with proper bounds, e.g., \sum_{i=1}^{N}
- Mean/average bars: use \bar{} or \overline{}, e.g., \bar{Y} or \overline{Y}
- Fractions: use \frac{numerator}{denominator}, e.g., \frac{1}{N}
- Subscripts and superscripts: use _ and ^, e.g., Y_i, x^2
- Products: use \prod with bounds, e.g., \prod_{i=1}^{n}
- Greek letters: use proper LaTeX commands, e.g., \alpha, \beta, \sigma
```

**用户消息中新增：**
```
特别注意数学符号的准确识别：
- 求和符号（Σ）：使用 \sum_{下标}^{上标}，例如 \sum_{i=1}^{N}
- 平均值符号（上划线）：使用 \bar{} 或 \overline{}，例如 \bar{Y}、\overline{x}
- 分数：使用 \frac{分子}{分母}，例如 \frac{1}{N}、\frac{Y_1+Y_2+\cdots+Y_N}{N}
- 下标和上标：使用 _ 和 ^，例如 Y_i、x^2、Y_1、Y_2
- 乘积符号（∏）：使用 \prod_{下标}^{上标}
- 希腊字母：使用LaTeX命令，如 \alpha、\beta、\sigma
```

### 2. 测试脚本（已创建）

创建了 `tests/test_math_symbols.py` 测试脚本，用于验证数学符号识别的准确性。

## 使用方法

### 方法一：使用Web界面（推荐）

1. **重启后端服务以加载新配置：**

```bash
# 如果使用Docker
sudo docker compose restart

# 如果直接运行
# 停止当前运行的后端服务（Ctrl+C），然后重新启动
python web/backend/app.py
```

2. **访问Web界面：**
   - 打开浏览器访问 `http://localhost:5173`
   - 上传用户提供的图片进行测试
   - 检查生成的Word文档中的数学公式是否正确

### 方法二：使用命令行

```bash
# 处理单个图片
python -m src.main path/to/your/image.png -o output.docx

# 查看生成的文档，检查数学符号是否正确
```

### 方法三：运行测试脚本

```bash
# 需要先准备测试图片
python tests/test_math_symbols.py
```

## 验证修复效果

使用用户提供的图片测试，应该能看到：

**修复前：**
- 求和符号可能显示为文本或不正确的格式
- 平均值可能显示为 Y- 或其他错误格式
- 分数可能显示为 (分子)/(分母) 的文本格式

**修复后：**
- 求和符号显示为 `$\sum_{i=1}^{N} Y_i$`
- 平均值显示为 `$\bar{Y}$` 或 `$\overline{Y}$`
- 分数显示为 `$\frac{Y_1+Y_2+\cdots+Y_N}{N}$`

## 注意事项

1. **重启服务**：修改配置文件后必须重启后端服务才能生效
2. **LLM选择**：不同的LLM提供商对数学符号的识别能力可能有差异，建议使用 GPT-4 Vision 或 Claude 3 Opus 以获得最佳效果
3. **图片质量**：确保图片清晰，数学符号完整可见
4. **复杂公式**：对于特别复杂的公式，可能仍需人工检查和调整

## 进一步改进建议

如果仍有问题，可以考虑：

1. **增加示例**：在提示词中加入更多具体的LaTeX示例
2. **后处理**：在 `formula_converter.py` 中增加后处理逻辑，自动修正常见的错误模式
3. **多次验证**：对识别结果进行自动验证，如果不符合LaTeX语法则重新识别
4. **微调模型**：如果使用开源模型，可以用数学公式数据集进行微调

## 相关文件

- `config/config.yaml` - 配置文件（提示词）
- `src/llm_client.py` - LLM客户端
- `src/formula_converter.py` - 公式转换器
- `tests/test_math_symbols.py` - 测试脚本
- `docs/fixes/math_symbol_fix.md` - 本说明文档

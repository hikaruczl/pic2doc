# 格式转换测试指南

## 概述

`test_format_conversion.py` 是一个独立的测试工具，用于测试文本到Word文档的格式转换功能，无需调用LLM API，可以快速验证公式解析和文档生成是否正常工作。

## 功能特点

- ✅ 无需调用LLM API，降低测试成本
- ✅ 支持多种输入方式（文件、命令行、标准输入）
- ✅ 自动解析LaTeX公式（行内公式 `$...$` 和显示公式 `$$...$$`）
- ✅ 生成格式化的Word文档
- ✅ 详细的日志输出，方便调试

## 使用方法

**注意：** 如果项目使用了虚拟环境，请使用 `.venv/bin/python` 代替 `python`

### 1. 从文件读取文本

```bash
# 使用虚拟环境（推荐）
.venv/bin/python test_format_conversion.py -f sample_text.txt

# 或使用系统Python
python3 test_format_conversion.py -f sample_text.txt
```

### 2. 从文件读取并指定输出文件名

```bash
.venv/bin/python test_format_conversion.py -f sample_text.txt -o my_output.docx
```

### 3. 直接输入文本

```bash
.venv/bin/python test_format_conversion.py -t "这是一个测试公式 \$x^2 + y^2 = z^2\$"
```

### 4. 从标准输入读取（支持管道）

```bash
cat sample_text.txt | .venv/bin/python test_format_conversion.py

# 或者
echo "测试公式 \$a^2 + b^2 = c^2\$" | .venv/bin/python test_format_conversion.py
```

### 5. 查看帮助

```bash
.venv/bin/python test_format_conversion.py -h
```

## 输入文本格式

文本中可以包含：

### 行内公式
使用单个 `$` 包裹：
```
这是一个行内公式 $x^2 + y^2 = z^2$，它会出现在文本中。
```

### 显示公式
使用双 `$$` 包裹：
```
这是一个显示公式：

$$\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$

它会单独成行并居中显示。
```

### 普通文本
直接写即可，段落之间用空行分隔：
```
第一段文字。

第二段文字。
```

## 示例文件

项目中包含一个示例文件 `sample_text.txt`，展示了完整的格式：

```bash
.venv/bin/python test_format_conversion.py -f sample_text.txt -o test_output.docx
```

## 日志输出

脚本会输出详细的日志信息，包括：

1. **输入文本** - 显示完整的输入内容
2. **解析结果** - 显示识别出的文本块和公式
3. **格式化结果** - 显示转换后的段落和公式元素
4. **文档保存路径** - 显示生成的Word文档位置

## 输出文件

生成的Word文档会保存在 `output/` 目录下：

- 如果指定了 `-o` 参数，使用指定的文件名
- 否则使用默认格式：`format_test_YYYYMMDD_HHMMSS.docx`

## 典型工作流程

### 测试新的公式格式

1. 创建测试文本文件 `test.txt`：
```
测试复杂公式 $\sum_{i=1}^{n} i^2$ 的渲染效果。

显示公式测试：

$$\int_{0}^{\infty} e^{-x^2} dx = \frac{\sqrt{\pi}}{2}$$
```

2. 运行测试：
```bash
.venv/bin/python test_format_conversion.py -f test.txt -o formula_test.docx
```

3. 打开生成的 `output/formula_test.docx` 检查效果

### 测试LLM输出

1. 从日志中复制LLM的完整输出文本
2. 保存到文件 `llm_output.txt`
3. 运行测试：
```bash
.venv/bin/python test_format_conversion.py -f llm_output.txt -o llm_test.docx
```

4. 对比检查格式转换是否正确

## 故障排查

### 公式不显示

- 检查LaTeX语法是否正确
- 查看日志中的公式解析结果
- 确认 `latex2mathml` 库已安装

### 文档格式不对

- 检查输入文本的段落分隔（使用空行）
- 查看日志中的格式化结果
- 确认配置文件 `config/config.yaml` 设置正确

### 中文显示问题

- 确保输入文件使用UTF-8编码
- 检查Word文档的字体设置

## 相关文件

- `test_format_conversion.py` - 测试脚本
- `sample_text.txt` - 示例输入文本
- `src/formula_converter.py` - 公式转换器
- `src/document_generator.py` - 文档生成器
- `config/config.yaml` - 配置文件

## 配置说明

脚本使用 `config/config.yaml` 中的配置，主要影响：

- `formula.preserve_latex` - 是否在文档中保留LaTeX注释（建议设为false）
- `document.default_font` - 文档字体
- `document.default_font_size` - 文档字号
- `document.image_width_inches` - 图片宽度（本测试不含图片）

## 高级用法

### 批量测试

创建多个测试文件，使用脚本批量转换：

```bash
for file in test_*.txt; do
    echo "Testing $file..."
    .venv/bin/python test_format_conversion.py -f "$file" -o "${file%.txt}.docx"
done
```

### 实时预览

配合文件监控工具，实现修改即转换：

```bash
# 需要安装 entr 工具
echo sample_text.txt | entr .venv/bin/python test_format_conversion.py -f sample_text.txt -o preview.docx
```

## 总结

使用此测试工具可以：

1. **快速验证** - 无需调用API即可测试格式转换
2. **降低成本** - 避免频繁调用付费API
3. **方便调试** - 详细日志帮助定位问题
4. **灵活输入** - 支持多种输入方式
5. **快速迭代** - 修改代码后立即测试效果

# 行内公式位置修复说明

## 问题描述

之前的版本中，所有公式（包括行内公式 `$...$`）都会被提取为单独的元素，导致：
- 行内公式单独占一行
- 破坏了原文的排版和阅读流畅性
- 与原始内容的布局不符

例如，文本 "已知函数 $f(x) = x^2$ 是..." 会被拆分成三个独立段落：
```
已知函数
f(x) = x^2
是...
```

## 解决方案

修改解析和渲染逻辑，实现：
- **显示公式** (`$$...$$`) - 单独成行，居中显示
- **行内公式** (`$...$`) - 保留在原文本位置，与文字在同一行

## 修改内容

### 1. 修改 `src/formula_converter.py`

**方法：** `parse_content()`

**修改前：**
- 提取所有公式（显示公式和行内公式）作为单独元素
- 将文本和公式交替存储

**修改后：**
- 只提取显示公式 (`$$...$$`) 作为单独元素
- 行内公式 (`$...$`) 保留在文本中
- 更新日志输出，显示行内公式数量

**核心逻辑：**
```python
# 只查找显示公式 $$...$$
display_formulas = []
for match in re.finditer(self.DISPLAY_FORMULA_PATTERN, content, re.DOTALL):
    display_formulas.append({...})

# 行内公式保留在文本中
for formula in display_formulas:
    if current_pos < formula['start']:
        text = content[current_pos:formula['start']].strip()
        if text:
            elements.append({'type': 'text', 'content': text})  # 包含行内公式
```

### 2. 修改 `src/document_generator.py`

**方法：** `_add_paragraph()`

**修改前：**
- 直接将文本添加为段落
- 不处理其中的行内公式

**修改后：**
- 解析段落中的行内公式
- 将文本和公式交替添加到同一段落中
- 行内公式转换为MathML并插入

**核心逻辑：**
```python
# 查找行内公式（排除双$$）
inline_formula_pattern = r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)'

for match in re.finditer(inline_formula_pattern, text):
    # 添加公式前的文本
    run = paragraph.add_run(text[last_pos:match.start()])
    
    # 添加行内公式（转换为MathML）
    latex = match.group(1).strip()
    mathml = latex_to_mathml(latex)
    self._insert_mathml(paragraph, mathml)
    
    last_pos = match.end()

# 添加剩余文本
run = paragraph.add_run(text[last_pos:])
```

**正则表达式说明：**
- `(?<!\$)` - 负向后顾，确保前面不是 `$`
- `\$(?!\$)` - 匹配单个 `$`，后面不是 `$`
- `(.+?)` - 非贪婪匹配公式内容
- `(?<!\$)\$(?!\$)` - 匹配结束的单个 `$`

这样可以准确匹配 `$...$` 而排除 `$$...$$`

## 测试结果

### 测试用例1：纯行内公式（log_text）

**输入：** 50个行内公式，0个显示公式

**输出：**
```
解析完成: 1 个元素 (0 个显示公式, 50 个行内公式保留在文本中)
格式化完成，共 12 个段落/公式
```

**结果：** ✅ 所有行内公式保留在原位置

### 测试用例2：混合公式（sample_text.txt）

**输入：** 11个行内公式，4个显示公式

**输出：**
```
解析完成: 8 个元素 (4 个显示公式, 11 个行内公式保留在文本中)
格式化完成，共 13 个段落/公式
```

**结果：** ✅ 行内公式在原位置，显示公式单独成行

## 效果对比

### 修改前

```
已知函数
f(x) = x^2 + 2x + 1
，求解以下问题。

因此，当
x = -1
时，函数取得最小值
f(-1) = 0
。
```

### 修改后

```
已知函数 f(x) = x^2 + 2x + 1，求解以下问题。

因此，当 x = -1 时，函数取得最小值 f(-1) = 0。
```

## 技术细节

### 公式类型识别

| 标记 | 类型 | 处理方式 | 示例 |
|-----|------|---------|------|
| `$...$` | 行内公式 | 保留在文本中，同一段落 | 函数 $f(x)$ 是... |
| `$$...$$` | 显示公式 | 提取为单独元素，居中显示 | $$\int_0^1 x^2 dx$$ |

### 解析流程

```
输入文本
    ↓
parse_content()
    ├─ 查找 $$...$$ → 提取为单独元素
    └─ 保留 $...$ 在文本中
    ↓
format_for_word()
    ├─ 文本元素 → paragraph
    └─ 公式元素 → formula
    ↓
_add_paragraph()
    ├─ 识别段落中的 $...$
    ├─ 转换为 MathML
    └─ 插入到段落中
    ↓
生成 Word 文档
```

### MathML 转换

行内公式和显示公式都使用 `latex2mathml` 库转换为 MathML，然后插入到 Word 文档的 OMML 格式中：

```python
# LaTeX → MathML
mathml = latex_to_mathml(latex)

# MathML → OMML (Word格式)
omml_element = self._convert_mathml_to_omml(mathml)

# 插入到段落
run._element.append(omml_element)
```

## 使用方法

修改后的代码自动处理公式位置，无需特殊操作：

```bash
# 直接使用，自动正确处理
.venv/bin/python test_format_conversion.py -f your_text.txt -o output.docx
```

## 兼容性

- ✅ 纯文本（无公式）
- ✅ 纯行内公式
- ✅ 纯显示公式
- ✅ 混合公式
- ✅ 复杂 LaTeX 公式（分数、根号、积分等）

## 错误处理

如果行内公式的 LaTeX 转换失败，会回退到文本显示：

```python
try:
    mathml = latex_to_mathml(latex)
    self._insert_mathml(paragraph, mathml)
except Exception as e:
    logger.warning(f"插入行内公式失败，使用文本: {str(e)}")
    run = paragraph.add_run(f"${latex}$")  # 回退到文本
```

## 注意事项

1. **正则表达式限制**
   - 行内公式中不能包含换行符
   - 如果需要多行公式，请使用显示公式 `$$...$$`

2. **特殊字符**
   - 如果文本中需要显示字面的 `$` 符号，需要转义
   - 或者避免使用 `$` 作为普通文本

3. **性能**
   - 每个行内公式都需要进行 LaTeX → MathML → OMML 转换
   - 如果文档中有大量行内公式，处理时间会相应增加

## 相关文件

- `src/formula_converter.py` - 公式解析逻辑
- `src/document_generator.py` - 文档生成和公式渲染
- `test_format_conversion.py` - 测试工具
- `log_text` - 测试用例（纯行内公式）
- `sample_text.txt` - 测试用例（混合公式）

## 总结

此修复确保：
1. ✅ 行内公式保持在原文本位置
2. ✅ 显示公式单独成行居中显示
3. ✅ 保持原文的排版和阅读流畅性
4. ✅ 符合数学文档的排版规范
5. ✅ 正确处理各种公式混合场景

修改后的代码更符合用户期望，生成的 Word 文档布局更接近原始内容。

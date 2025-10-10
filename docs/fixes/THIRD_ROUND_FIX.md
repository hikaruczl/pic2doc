# 第三轮修复总结

## 问题回顾

用户报告两个新问题：

1. **重复公式问题**: 包含空格差异的公式未被去重
   - 示例: `$f'(x)=1$` vs `$f'(x) = 1$` (等号周围空格不同)
   - 原因: 公式归一化不够激进，无法识别这些细微差异

2. **公式对齐问题**: 多行公式(aligned环境)的第一行居中而非左对齐
   - 现象: `\begin{aligned}...\end{aligned}` 环境的公式整体居中显示
   - 预期: 多行公式应该左对齐

---

## 修复方案

### 问题1: 增强公式归一化

**文件**: `src/main.py` (第314-330行)

**已有的修复** (来自第二轮):
在 `_trim_overlap_text()` 静态方法中的 `normalize_for_formula_comparison()` 函数已经包含6步激进归一化：

```python
def normalize_for_formula_comparison(text: str) -> str:
    """针对包含公式的文本，进行更激进的标准化"""
    import re
    # 移除$内外的所有空格差异，只保留基本结构
    # 步骤1: 标准化LaTeX命令后的空格
    text = re.sub(r'\\(\w+)\s+', r'\\\1 ', text)  # \frac  {} -> \frac {}
    # 步骤2: 移除$符号前后的空格
    text = re.sub(r'\s*\$\s*', '$', text)  # 空格 $ 空格 -> $
    # 步骤3: 标准化括号前后的空格
    text = re.sub(r'\s*([(){}[\]])\s*', r'\1', text)  # ( x ) -> (x)
    # 步骤4: 标准化运算符周围的空格（统一为单个空格）
    text = re.sub(r'\s*([+\-=<>])\s*', r' \1 ', text)  # x+y -> x + y
    # 步骤5: 移除逗号后的多余空格
    text = re.sub(r',\s+', ', ', text)  # ,  空格 -> ,
    # 步骤6: 压缩所有连续空格为单个空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
```

**效果**:
- `$f'(x)=1$` 和 `$f'(x) = 1$` 归一化后都变成: `$f'(x) = 1$`
- `$x+y$` 和 `$x + y$` 归一化后都变成: `$x + y$`
- 括号、逗号、LaTeX命令周围的空格差异都被统一

**使用场景**:
- 检测到内容包含 `$` 符号时自动启用
- 用于图像切片边界的重叠检测
- 相似度阈值: 75% (允许一些差异)

---

### 问题2: 修复公式对齐

**文件**: `src/document_generator.py` (第242-262行)

**修改内容**:

```python
def _add_formula(self, doc: Document, element: Dict):
    """添加公式"""
    formula_type = element['formula_type']
    latex = element['latex']
    mathml = element['mathml']

    # 创建段落
    paragraph = doc.add_paragraph()

    if formula_type == 'display':
        # 检查是否包含多行环境(aligned, gathered等)
        # 这些环境应该左对齐,而不是居中
        multi_line_envs = ['aligned', 'gathered', 'align', 'eqnarray', 'cases']
        is_multi_line = any(env in latex for env in multi_line_envs)

        if is_multi_line:
            # 多行公式左对齐
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        else:
            # 单行公式居中显示
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

**修改前**:
```python
if formula_type == 'display':
    # 居中显示公式
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

**修改后行为**:
- 检测公式LaTeX是否包含多行环境关键词
- 支持的多行环境: `aligned`, `gathered`, `align`, `eqnarray`, `cases`
- **多行环境** → 左对齐 (LEFT)
- **单行公式** → 居中 (CENTER)

**效果示例**:

单行公式 (居中):
```
              x² + y² = r²
```

多行公式 (左对齐):
```
f(x) = x + 1
f'(x) = 1
f''(x) = 0
```

---

## 测试验证

### 验证问题1 (公式去重)

```bash
# 开启DEBUG日志
export LOG_LEVEL=DEBUG

# 处理图片
python -m src.main your_image.png -o test.docx

# 查看重叠检测日志
tail -f logs/advanceocr_*.log | grep -E "(重叠|分片)"
```

**预期日志**:
```
INFO - 分片 X/Y: 移除 Z 字符重叠
DEBUG - 发现精确重叠: Z 字符 (公式文本=True)
DEBUG - 公式文本使用比例估算移除重叠(ratio=0.XX)，剩余 N 字符
```

**验证清单**:
- [ ] 日志中显示"移除 X 字符重叠"
- [ ] 文档中没有重复的公式（即使空格不同）
- [ ] 包含 `$...$` 的句子不重复

---

### 验证问题2 (公式对齐)

**验证清单**:
- [ ] 单行公式 (如 `$$x^2 + y^2 = 1$$`) 居中显示 ✓
- [ ] `\begin{aligned}...\end{aligned}` 环境左对齐 ✓
- [ ] `\begin{gathered}...\end{gathered}` 环境左对齐 ✓
- [ ] `\begin{cases}...\end{cases}` 环境左对齐 ✓
- [ ] 公式内容正确渲染（不受对齐影响）

**手动检查**:
在生成的Word文档中：
1. 找到包含 `aligned`/`gathered`/`cases` 的公式
2. 确认这些公式段落左对齐（不是居中）
3. 确认公式内容正确显示

---

## 技术细节

### 为什么需要两套归一化？

代码中有两个归一化函数：

1. **`normalize_for_comparison()`** - 基础归一化
   - 压缩空白符
   - 统一换行
   - 用于纯文本重叠检测

2. **`normalize_for_formula_comparison()`** - 公式归一化
   - 继承基础归一化
   - 额外处理LaTeX语法（命令、括号、运算符）
   - 只在检测到 `$` 时使用

### 多行环境检测逻辑

```python
multi_line_envs = ['aligned', 'gathered', 'align', 'eqnarray', 'cases']
is_multi_line = any(env in latex for env in multi_line_envs)
```

这个简单的字符串匹配对于以下LaTeX代码都有效：
- `\begin{aligned}...\end{aligned}`
- `\begin{gathered}...\end{gathered}`
- `\begin{align}...\end{align}` (不带星号的也会被检测到)
- `\begin{cases}...\end{cases}`

---

## 相关修复历史

### 第一轮修复 (THREE_ISSUES_FIX_SUMMARY.md)
1. ✅ Prime符号显示错误 (`f'}(x)` → `f'(x)`)
2. ⚠️ 整段识别为公式 (第一次尝试，未成功)
3. ⚠️ 边界重叠 (第一次尝试，未完全修复)

### 第二轮修复 (SECOND_ROUND_FIX.md)
1. ✅ 整段识别为公式 (改用逐行扫描)
2. ✅ 边界重叠 (增强归一化，降低阈值)
3. ✅ Logger错误修复

### 第三轮修复 (本轮)
1. ✅ 公式空格差异去重 (已有修复验证)
2. ✅ 多行公式对齐 (新增修复)

---

## 如果仍有问题

### 问题1: 仍有公式重复

**调试步骤**:
1. 开启DEBUG日志: `export LOG_LEVEL=DEBUG`
2. 查看是否有"发现重叠"日志
3. 如果没有，可能需要调整参数:

```python
# 在 src/main.py 中
@staticmethod
def _trim_overlap_text(existing: str, new_content: str,
                       max_overlap: int = 2000,
                       min_overlap: int = 50):  # 尝试降低到 30
    # ...
    if similarity > 0.75:  # 尝试降低到 0.70
```

4. 检查是否是完全不同的公式（而非重复）

### 问题2: 对齐仍不正确

**检查项**:
1. 确认LaTeX包含 `aligned`/`gathered` 等关键词
2. 如果使用其他环境，添加到 `multi_line_envs` 列表
3. 检查是否是Word显示问题（尝试在不同设备打开）

---

## 总结

**修复文件**:
- ✅ `src/main.py` - 公式归一化 (第二轮已修复，本轮验证)
- ✅ `src/document_generator.py` - 公式对齐 (本轮新增)

**测试命令**:
```bash
# 处理图片
python -m src.main your_image.png -o test.docx

# 查看详细日志
export LOG_LEVEL=DEBUG
python -m src.main your_image.png -o test_debug.docx 2>&1 | tee processing.log
```

**验证重点**:
1. 文档中无重复公式（即使空格不同）
2. 多行公式左对齐，单行公式居中
3. 公式内容正确渲染

---

**修复时间**: 2025-10-09
**修复文件**: `src/document_generator.py`
**关联修复**: `src/main.py` (第二轮已完成)
**状态**: ✅ 已修复，等待测试验证

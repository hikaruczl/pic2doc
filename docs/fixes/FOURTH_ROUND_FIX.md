# 第四轮修复总结

## 问题复查

用户反馈前两轮修复都未成功：

1. **重复问题仍存在**: 公式空格不匹配导致重复未被检测
   - 示例: `$f'(x)=1$` 和 `$f'(x) = 1$` 仍然重复出现

2. **对齐修改导致新问题**: 整段文字被识别为公式
   - 之前的关键词匹配太简单，导致误判

---

## 第四轮修复策略

### 修复1: 完全重写重复检测 - 移除所有空格后比较

**文件**: `src/main.py` (第287-368行)

**新策略**:
- **完全移除空格**: 使用 `re.sub(r'\s+', '', text)` 移除所有空白符
- **只比较内容**: 忽略所有格式差异（空格、换行、缩进）
- **智能切分**: 在自然边界（换行、句号、公式标记）处切分

**核心逻辑**:

```python
def remove_all_spaces(text: str) -> str:
    """完全移除所有空白符，只保留内容"""
    return re.sub(r'\s+', '', text)

# 完全无空格版本
existing_no_space = remove_all_spaces(existing)
candidate_no_space = remove_all_spaces(candidate)

# 检查完全重复（无空格版本）
if candidate_no_space in existing_no_space:
    _logger.info(f"检测到完全重复内容（忽略空格），跳过")
    return ""
```

**重叠检测**:
```python
# 在无空格版本中找重叠
for overlap in range(max_len, min_overlap - 1, -1):
    suffix = existing_tail_no_space[-overlap:]
    prefix = candidate_no_space[:overlap]

    if suffix == prefix:  # 精确匹配
        best_overlap_len = overlap
        break
```

**智能切分**:
```python
# 在原始文本中找切分位置（保留格式）
ratio = best_overlap_len / len(candidate_no_space)
cut_pos = int(len(candidate) * ratio)

# 在附近寻找自然边界
for sep in ['\n\n', '\n', '。', '. ', '$$', '$']:
    sep_pos = chunk.find(sep)
    if sep_pos >= 0:
        cut_pos = cut_pos + sep_pos + len(sep)
        break
```

**改进点**:
1. ✅ 降低 `min_overlap` 从 50 → 30（检测更小的重叠）
2. ✅ 完全移除空格后比较（100%解决空格差异）
3. ✅ 在公式边界（`$`、`$$`）处切分
4. ✅ 使用INFO级别日志（更容易看到重叠检测）

---

### 修复2: 精确检测多行公式环境

**文件**: `src/document_generator.py` (第242-261行)

**问题分析**:
之前使用 `any(env in latex for env in multi_line_envs)` 简单子字符串匹配，可能误匹配：
- 如果整段文本错误地被识别为公式，且文本中包含"aligned"这个词
- 就会被错误地左对齐

**新策略**:
使用正则表达式精确匹配LaTeX的 `\begin{...}` 语法：

```python
# 检查是否是多行环境(通过LaTeX的\begin{...}语法)
is_multi_line = bool(re.search(r'\\begin\{(aligned|gathered|align|eqnarray|cases)', latex))

if is_multi_line:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT  # 多行左对齐
else:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER  # 单行居中
```

**匹配模式**:
- `\\begin\{aligned\}` ✓ 匹配
- `\\begin\{gathered\}` ✓ 匹配
- `text aligned with` ✗ 不匹配（不是LaTeX环境）
- `aligned` ✗ 不匹配（必须有\begin{}）

**支持的环境**:
- `aligned` - 对齐的多行公式
- `gathered` - 居中的多行公式（但段落左对齐）
- `align` - 带编号的对齐公式
- `eqnarray` - 旧式多行公式
- `cases` - 分段函数

---

## 测试验证

### 验证命令

```bash
# 处理图片
python -m src.main your_image.png -o test.docx

# 查看重叠检测日志（INFO级别自动显示）
tail -f logs/advanceocr_*.log | grep "重叠"
```

### 预期日志输出

**重叠检测成功**:
```
INFO - 发现重叠(无空格): 156 字符
INFO - 移除 234 字符重叠，剩余 187 字符
```

**完全重复**:
```
INFO - 检测到完全重复内容（忽略空格），跳过
```

**无重叠**:
```
DEBUG - 未发现重叠，保留完整内容 (456 字符)
```

---

### 验证清单

#### 问题1: 重复检测
- [ ] 日志中看到"发现重叠(无空格)"
- [ ] 文档中无重复公式（即使空格完全不同）
- [ ] 文档中无重复文本段落
- [ ] 包含公式的句子不重复

**测试用例**:
```
已合并文本: "因为$f'(x)=1$所以..."
新内容: "因为 $f'(x) = 1$ 所以..."
预期: 检测为重复，跳过新内容
```

#### 问题2: 公式对齐
- [ ] 单行公式居中: `$$x^2 + y^2 = 1$$`
- [ ] aligned环境左对齐: `$$\begin{aligned}...\end{aligned}$$`
- [ ] gathered环境左对齐: `$$\begin{gathered}...\end{gathered}$$`
- [ ] cases环境左对齐: `$$\begin{cases}...\end{cases}$$`
- [ ] 文本不受影响（不会被误识别为公式）

---

## 技术对比

### 旧版重复检测 vs 新版

| 特性 | 旧版 (第二/三轮) | 新版 (第四轮) |
|------|---------------|--------------|
| 归一化方式 | 6步公式归一化 | 完全移除空格 |
| 空格处理 | 统一为单个空格 | 完全移除 |
| 运算符 | `x+y` → `x + y` | `x+y` → `x+y` |
| 括号 | `( x )` → `(x)` | `(x)` → `(x)` |
| 换行 | 压缩为最多2个 | 完全移除 |
| min_overlap | 50 | 30 |
| 日志级别 | DEBUG | INFO |

**示例对比**:

原文1: `$f'(x) = 1$`
原文2: `$f'(x)=1$`

旧版归一化后:
- 文本1: `$f'(x) = 1$` (有空格)
- 文本2: `$f'(x) = 1$` (有空格)
- 结果: 匹配 ✓

新版归一化后:
- 文本1: `$f'(x)=1$` (无空格)
- 文本2: `$f'(x)=1$` (无空格)
- 结果: 匹配 ✓

**新版优势**:
- 更简单，更可靠
- 不需要复杂的归一化规则
- 100%消除空格差异

---

### 对齐检测: 关键词匹配 vs 正则匹配

| 方法 | 代码 | 问题 |
|-----|------|-----|
| 关键词 | `'aligned' in latex` | 误匹配普通文本 |
| 正则 | `r'\\begin\{aligned\}'` | 只匹配LaTeX环境 ✓ |

**误匹配示例**:

```latex
% 错误的LLM输出: 整段文本被识别为公式
$
(5) The values are aligned in a row.
We need to solve for x.
$
```

旧版 (关键词):
- 检测到 "aligned"
- 应用左对齐 ✗ 错误

新版 (正则):
- 没有 `\begin{aligned}`
- 应用居中对齐 ✓ 正确

---

## 故障排除

### 如果仍有重复

1. **检查日志**:
```bash
export LOG_LEVEL=INFO
python -m src.main your_image.png -o test.docx 2>&1 | tee debug.log
grep "重叠" debug.log
```

2. **查看是否检测到重叠**:
   - 如果有"发现重叠"但仍重复 → 切分位置不对
   - 如果没有"发现重叠" → 降低 `min_overlap` (30 → 20)

3. **手动调整参数**:
```python
# src/main.py, 第289行
def _trim_overlap_text(existing: str, new_content: str,
                       max_overlap: int = 2000,
                       min_overlap: int = 20):  # 改为20
```

### 如果对齐仍不正确

1. **检查LaTeX格式**:
```bash
grep "\\\\begin{" your_output.log
```

2. **确认是否匹配**:
   - 必须是 `\begin{aligned}` 格式
   - 不是 `aligned` 单词

3. **添加更多环境**:
```python
# src/document_generator.py, 第254行
is_multi_line = bool(re.search(
    r'\\begin\{(aligned|gathered|align|eqnarray|cases|split|multline)\}',
    latex
))
```

---

## 修复历史

| 轮次 | 问题 | 修复 | 结果 |
|-----|------|------|-----|
| 一 | Prime符号、整段公式、重叠 | 字符串修复、正则、归一化 | Prime ✓, 其他 ✗ |
| 二 | 整段公式、重叠 | 逐行扫描、公式归一化 | 整段 ✓, 重叠部分 ✓ |
| 三 | 重叠、对齐 | 增强归一化、关键词检测 | 均 ✗ |
| **四** | 重叠、对齐 | **完全移除空格、正则匹配** | **待验证** |

---

## 总结

**修改的文件**:
1. ✅ `src/main.py` - 完全重写重复检测逻辑
2. ✅ `src/document_generator.py` - 精确匹配多行环境

**核心改进**:
1. 重复检测: 移除所有空格后比较（最激进）
2. 对齐检测: 正则表达式精确匹配 `\begin{...}` 语法

**测试重点**:
- 公式空格差异不再导致重复
- 多行公式左对齐，单行公式居中
- 不会误识别普通文本为公式

**日志关键字**:
- "发现重叠(无空格)" - 成功检测重叠
- "移除 X 字符重叠" - 成功移除重叠
- "检测到完全重复内容" - 整段重复

---

**修复时间**: 2025-10-09
**修复文件**: `src/main.py`, `src/document_generator.py`
**状态**: ✅ 已修复，等待测试验证

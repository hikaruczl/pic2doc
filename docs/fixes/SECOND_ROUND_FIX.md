# 第二轮修复总结

## 问题复查

用户报告问题1(Prime符号)已修复 ✓，但问题2和3仍存在：

1. **✓ 已修复**: f'(x) 多出 } - 第一轮修复成功
2. **⚠️ 仍存在**: 整段内容被识别为公式
3. **⚠️ 仍存在**: 边界重叠内容

## 第二轮修复

### 问题2修复: 整段识别为公式

**问题现象**:
```
$
\begin{aligned}
& (5)\ f(x)=...
\end{aligned}
$
```
整个aligned环境被单个`$`包裹，而不是`$$`。

**第一轮修复问题**: 使用了复杂的正则表达式，但在实际LLM输出中失效。

**第二轮修复** (`src/formula_converter.py`):

改用逐行扫描的方式：

```python
def _preprocess_llm_output(self, content: str) -> str:
    # 按行分割
    lines = content.split('\n')

    # 查找模式: 单独一行的 $
    #            包含 \begin{aligned}
    #            包含 \end{aligned}
    #            单独一行的 $

    # 如果找到，替换首尾的 $ 为 $$
```

**优势**:
- 不依赖复杂正则
- 处理多行内容更可靠
- 易于调试和理解

---

### 问题3修复: 边界重叠

**问题现象**:
- 纯文字重叠被检测（但没出现在文档中，说明有效）
- **包含公式的行重叠仍会出现在文档中** ← 关键问题
- 日志中没有"发现重叠"的字眼

**分析**:
包含公式的文本，如：
```
因为 $x \in(0,+\infty)$ 时，$f''(x)=e^{x}-1>0$
```
LaTeX语法的细微差异（空格、命令格式）导致字符串不匹配。

**第二轮修复** (`src/main.py`):

1. **公式特殊处理**:
```python
# 检测是否包含公式
has_formula = '$' in existing or '$' in candidate

if has_formula:
    # 使用更激进的标准化
    # 移除LaTeX命令后的空格
    # 标准化所有空白符
```

2. **降低相似度要求**:
- 从80% → 75% (更宽松，容忍公式差异)

3. **改进切分策略**:
```python
if has_formula:
    # 使用比例估算
    # 在附近寻找段落边界(换行、句号)
    # 在自然位置切分
```

4. **增强日志**:
```python
logger.info(f"分片 {idx+1}/{len(segments)}: 移除 {removed} 字符重叠")
logger.debug(f"发现精确重叠: {overlap} 字符 (公式文本={has_formula})")
```

---

## 测试验证

### 查看详细日志

```bash
# 设置DEBUG级别
export LOG_LEVEL=DEBUG

# 处理图片
python -m src.main your_image.png -o test.docx

# 查看日志
tail -f logs/advanceocr_*.log | grep -E "(重叠|分片|preprocess)"
```

### 预期日志输出

**问题2修复后**:
```
DEBUG - 预处理LLM输出: 检测到单$包裹的aligned环境
INFO - 解析完成: X 个元素 (Y 个显示公式...)
```

**问题3修复后**:
```
DEBUG - 发现精确重叠: 127 字符 (公式文本=True)
INFO - 分片 7/27: 移除 127 字符重叠
DEBUG - 公式文本使用比例估算移除重叠(ratio=0.35)，剩余 234 字符
```

---

## 检查清单

在Word文档中验证:

### 问题2:
- [ ] 题号(5)、(6)是普通文本，不在公式框中
- [ ] aligned环境的公式正确渲染
- [ ] "解:"等文字是普通文本

### 问题3:
- [ ] 没有重复的句子
- [ ] 包含公式的行不重复
- [ ] 内容连贯，没有突然断开

### 在日志中验证:
- [ ] 看到"移除 X 字符重叠"的INFO日志
- [ ] DEBUG日志显示"发现重叠"(如果设置了DEBUG)
- [ ] 没有大量"未发现重叠"的DEBUG日志（说明检测有效）

---

## 如果仍有问题

### 问题2还存在

1. 查看日志中的LLM原始输出
2. 检查是否真的是单`$`开头结尾
3. 如果格式更复杂，可能需要进一步调整预处理逻辑

### 问题3还存在

1. 开启DEBUG日志，查看重叠检测详情
2. 检查日志中是否显示"发现重叠"
3. 如果显示"发现重叠"但文档中仍有重复，可能是切分位置不对
4. 如果不显示"发现重叠"，可能需要:
   - 进一步降低相似度阈值（75% → 70%）
   - 减小min_overlap（50 → 30）

可以在 `src/main.py` 中调整参数：
```python
@staticmethod
def _trim_overlap_text(existing: str, new_content: str,
                       max_overlap: int = 2000,
                       min_overlap: int = 30):  # 改为30
    ...
    if similarity > 0.70:  # 改为70%
```

---

## 配置优化

如果问题持续，可以调整图片切片参数：

```yaml
# config/config.yaml
image:
  slicing:
    overlap: 120  # 减少物理重叠（从160降到120）
    min_overlap: 30  # 降低检测阈值
```

---

## 技术细节

### 为什么公式文本需要特殊处理

同样的数学表达式，LLM可能返回：
- `$f'(x)=x$` （无空格）
- `$f'(x) = x$` （有空格）
- `$f^{\prime}(x)=x$` （prime格式）

这些在视觉上相同，但字符串不完全匹配。

### normalize_for_formula_comparison

这个函数做了：
1. 移除LaTeX命令后的空格：`\frac {}` → `\frac{}`
2. 标准化所有空白符：多个空格 → 单个空格
3. 使得相似但不同的公式表示能够匹配

---

**修复时间**: 2025-01-08
**修复文件**:
- `src/formula_converter.py` (问题2)
- `src/main.py` (问题3)
**状态**: ✅ 已修复，等待测试验证

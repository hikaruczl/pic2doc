# 问题修复总结

## 修复日期
2025-10-12

## 问题清单

### 1. 数学公式解析失败

**问题描述**：
一段包含多个数学公式的文本整体解析失败，主要原因是OCR识别错误：
- `\bar{x}_1` 被识别成 `ar{x}1`
- `y_0^2` 被识别成 `y_0 2`
- 上标符号 `^` 经常丢失

**解决方案**：
在 `src/formula_converter.py` 的 `fix_common_latex_patterns` 方法中添加OCR错误修复规则：

1. **修复 `ar{` → `\bar{`**
   ```python
   # OCR经常把 \bar 识别成 ar
   content = re.sub(r'(?<!\\)ar\{', r'\\bar{', content)
   ```

2. **修复下标+空格+数字**
   ```python
   # y_0 2 → y_0^2
   subscript_space_number = r'([A-Za-z]_[A-Za-z0-9]+)\s+(\d+)'
   content = re.sub(subscript_space_number, r'\1^\2', content)
   ```

3. **修复缺失的下标符号**
   ```python
   # \bar{x}1 → \bar{x}_1
   bar_missing_subscript = r'\\bar\{([A-Za-z])\}(\d+)'
   content = re.sub(bar_missing_subscript, r'\\bar{\1}_\2', content)
   ```

**测试方法**：
使用包含这些模式的LaTeX公式进行测试。

---

### 2. 矩阵符号显示小中括号

**问题描述**：
所有矩阵（pmatrix, bmatrix, vmatrix等）在Word中都显示为小括号，而不是各自正确的括号类型：
- `bmatrix` 应该显示方括号 `[]`
- `vmatrix` 应该显示竖线 `||`

**问题根因**：
`latex2mathml` 库将矩阵转换为如下MathML结构：
```xml
<mrow>
  <mo>[</mo>
  <mtable>...</mtable>
  <mo>]</mo>
</mrow>
```

我们的OMML转换器在处理 `mrow` 时，将 `mo`（括号）和 `mtable`（矩阵）分开处理了，导致它们没有正确组合。

**解决方案**：
修改 `src/document_generator.py` 中的 `_convert_mathml_element_to_omml` 方法，在处理 `mrow` 时检测矩阵模式：

```python
elif tag == 'mrow':
    # 检测矩阵模式: <mo>开括号</mo> <mtable>...</mtable> <mo>闭括号</mo>
    children = list(mathml_elem)

    # 如果符合 mo + mtable + mo 模式
    if (first_tag == 'mo' and last_tag == 'mo' and has_mtable):
        # 创建带括号的矩阵结构（使用d包裹m）
        d = etree.SubElement(omml_parent, '{%s}d' % MATH_NS)
        # 设置正确的括号字符
        begChr.set('{%s}val' % MATH_NS, open_bracket)
        endChr.set('{%s}val' % MATH_NS, close_bracket)
        # 创建矩阵结构
        m = etree.SubElement(d, '{%s}m' % MATH_NS)
        # 处理矩阵内容...
```

**测试方法**：
- 创建包含 `bmatrix`、`pmatrix`、`vmatrix` 的测试用例
- 验证生成的Word文档中括号显示正确

**修改文件**：
- `src/document_generator.py` (行 395-454)

---

### 3. 立体几何图形无法显示

**问题描述**：
OCR无法识别立体几何图形，导致生成的文档中缺少图形。

**解决方案**：
实现TikZ图形渲染功能，分三个阶段：

#### 第一阶段：TikZ基础支持（已完成）

**实现内容**：
1. 创建 `src/tikz_renderer.py` - TikZ代码渲染器
   - 识别 `\begin{tikzpicture}...\end{tikzpicture}` 代码块
   - 编译LaTeX生成PDF
   - 转换PDF为PNG图片
   - 返回PIL Image对象

2. 依赖检查：
   - `pdflatex` - LaTeX编译器 ✅
   - `pdftoppm` 或 `convert` - PDF转PNG ✅

3. 测试验证：
   - 测试立方体渲染 ✅
   - 测试圆锥渲染 ✅
   - 测试代码块提取 ✅

**配置扩展**：
```yaml
graphics:
  enabled: true
  backend: "tikz"

  tikz:
    latex_command: "pdflatex"
    convert_dpi: 300
```

**生成的测试图片**：
- `output/test_cube.png` (2.0KB)
- `output/test_cone.png` (9.2KB)

#### 第二阶段：集成到主流程（待实现）

**需要做的事情**：
1. 修改LLM提示词，指导生成TikZ代码
2. 在 `document_generator.py` 中集成TikZ渲染
3. 添加图形缓存机制
4. 更新配置文件模板

#### 第三阶段：增强功能（未来）

**计划功能**：
1. 支持Asymptote（更专业的3D图形）
2. 支持Matplotlib代码执行
3. 支持SVG代码
4. 提供常见立体几何模板
5. 智能判断是否需要生成图形

**参考文档**：
- `docs/improvements/3d_geometry_solution.md` - 详细设计方案

---

## 文件修改清单

### 修改的文件
1. `src/formula_converter.py`
   - 添加OCR错误修复规则（行 144-162）

2. `src/document_generator.py`
   - 修复矩阵括号处理逻辑（行 395-454）

### 新增的文件
1. `src/tikz_renderer.py` - TikZ渲染器
2. `tests/test_tikz_renderer.py` - TikZ渲染器测试
3. `tests/test_matrix_brackets.py` - 矩阵括号测试
4. `tests/test_matrix_structure.py` - MathML结构测试
5. `docs/improvements/3d_geometry_solution.md` - 立体几何方案设计
6. `docs/improvements/fix_summary.md` - 本文档

---

## 测试验证

### OCR错误修复测试
```python
# 测试用例
test_cases = [
    ('ar{x}1', r'\bar{x}_1'),
    ('y_0 2', 'y_0^2'),
    ('x_0 2 + y_0 2', 'x_0^2 + y_0^2'),
]
```

### 矩阵括号测试
```latex
% pmatrix - 小括号
\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}

% bmatrix - 方括号
\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}

% vmatrix - 竖线
\begin{vmatrix} 1 & 2 \\ 3 & 4 \end{vmatrix}
```

### TikZ渲染测试
```bash
cd /mnt/vdb/dev/advanceOCR
source .venv/bin/activate
python tests/test_tikz_renderer.py
```

---

## 注意事项

### 1. OCR错误修复的局限性
- 只能修复已知的常见模式
- 对于复杂的OCR错误可能无效
- 需要持续添加新的修复规则

### 2. 矩阵括号修复的边界条件
- 只处理 `mo + mtable + mo` 模式
- 对于嵌套矩阵可能需要额外处理
- 需要测试各种矩阵类型

### 3. TikZ渲染的依赖
- 需要完整的LaTeX安装（texlive-full）
- 需要PDF转换工具（pdftoppm或ImageMagick）
- 渲染可能较慢（每个图形约1-3秒）

---

## 后续工作

### 优先级1（重要且紧急）
- [ ] 将TikZ渲染集成到主流程
- [ ] 更新LLM提示词以生成TikZ代码
- [ ] 添加配置文件示例

### 优先级2（重要但不紧急）
- [ ] 添加更多OCR错误修复规则
- [ ] 测试更多矩阵类型和边界情况
- [ ] 实现图形缓存机制

### 优先级3（可以延后）
- [ ] 支持Asymptote
- [ ] 支持Matplotlib
- [ ] 添加常见立体几何模板
- [ ] 实现智能图形检测

---

## 联系方式
如有问题，请查看以下文档：
- API文档: `API.md`
- 配置指南: `CONFIGURATION_GUIDE.md`
- 快速开始: `QUICKSTART.md`

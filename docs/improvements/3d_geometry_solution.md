# 立体几何图形解决方案设计

## 问题描述
OCR无法直接识别立体几何图形，需要通过代码生成的方式来重建这些图形。

## 解决方案

### 方案1：TikZ/PGF渲染（推荐）
**优点**：
- LaTeX原生支持，质量高
- 与数学公式配合好
- 语法简洁

**实现步骤**：
1. 在LLM提示词中添加TikZ代码生成指导
2. 识别TikZ代码块（`\begin{tikzpicture}...\end{tikzpicture}`）
3. 使用`latex`+`dvipng`或`pdflatex`+`convert`渲染为图片
4. 插入到Word文档中

**所需依赖**：
- texlive-full（包含TikZ）
- dvipng 或 imagemagick

**代码结构**：
```python
class TikZRenderer:
    def render_tikz_to_image(self, tikz_code: str) -> Image:
        # 1. 创建临时LaTeX文件
        # 2. 编译LaTeX生成PDF
        # 3. 转换PDF为PNG
        # 4. 返回PIL Image对象
        pass
```

### 方案2：Matplotlib 3D渲染
**优点**：
- Python原生，易于集成
- 可以动态生成各种图形
- 不需要额外的LaTeX依赖

**实现步骤**：
1. 让LLM生成Python matplotlib代码
2. 识别代码块（```python...```）
3. 在沙箱环境中执行代码
4. 保存图片并插入文档

**代码结构**：
```python
class PythonGraphRenderer:
    def execute_and_render(self, python_code: str) -> Image:
        # 1. 验证代码安全性
        # 2. 在受限环境中执行
        # 3. 保存图片
        # 4. 返回PIL Image对象
        pass
```

### 方案3：SVG代码生成（最灵活）
**优点**：
- 矢量图形，质量好
- 可以直接嵌入Word
- LLM可以直接生成SVG代码

**实现步骤**：
1. 让LLM生成SVG代码
2. 识别SVG代码块
3. 验证并清理SVG
4. 转换为图片或直接嵌入

## 推荐实现路径

### 第一阶段：TikZ基础支持
1. 修改LLM提示词，指导生成TikZ代码
2. 实现TikZ代码识别
3. 实现TikZ渲染器
4. 集成到文档生成流程

### 第二阶段：增强功能
1. 添加常见立体几何模板
2. 支持Asymptote（更专业的3D图形）
3. 添加缓存机制避免重复渲染

### 第三阶段：智能识别
1. 让LLM自动判断是否需要图形
2. 根据描述自动生成合适的代码
3. 支持多种渲染后端切换

## 配置文件扩展

```yaml
graphics:
  enabled: true
  backend: "tikz"  # tikz | matplotlib | svg

  tikz:
    latex_command: "pdflatex"
    convert_dpi: 300

  matplotlib:
    figure_size: [8, 6]
    dpi: 300

  svg:
    validate: true
    convert_to_png: true
```

## 提示词扩展

在system prompt中添加：
```
当遇到立体几何图形时，请生成TikZ代码来绘制图形：

示例：
对于一个正方体，生成：
```tikz
\\begin{tikzpicture}
  % 正方体代码
\\end{tikzpicture}
```

对于锥体、柱体等，使用TikZ的3D库。
```

## 测试用例

1. 正方体
2. 长方体
3. 圆锥
4. 圆柱
5. 球体
6. 复合立体图形

## 风险和限制

1. **依赖问题**：需要安装LaTeX完整版
2. **性能问题**：渲染可能较慢
3. **安全问题**：执行用户代码需要沙箱
4. **质量问题**：LLM生成的代码可能不完美

## 后续优化

1. 使用GPU加速渲染
2. 预渲染常见图形
3. 提供图形编辑界面
4. 支持用户自定义模板

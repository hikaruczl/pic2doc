# TikZ 立体几何图形支持

本系统现已支持自动识别和渲染立体几何图形！

## 快速开始

### 1. 确保依赖已安装

```bash
# 检查LaTeX
pdflatex --version

# 检查PDF转换工具
pdftoppm -v
```

如果缺少依赖：
```bash
# Ubuntu/Debian
sudo apt-get install texlive-full poppler-utils

# 或者只安装必要的包
sudo apt-get install texlive-latex-base texlive-latex-extra texlive-pictures poppler-utils
```

### 2. 启用TikZ渲染

在 `config/config.yaml` 中确认：
```yaml
graphics:
  enabled: true
  backend: "tikz"
```

### 3. 使用方法

系统会自动识别LLM输出中的TikZ代码块：

````markdown
如图所示为一个正方体：

```tikz
\begin{tikzpicture}[scale=2]
  \draw[fill=gray!20] (0,0) -- (1,0) -- (1,1) -- (0,1) -- cycle;
  \draw[fill=gray!40] (0.3,0.3) -- (1.3,0.3) -- (1.3,1.3) -- (0.3,1.3) -- cycle;
  \draw (0,0) -- (0.3,0.3);
  \draw (1,0) -- (1.3,0.3);
  \draw (1,1) -- (1.3,1.3);
  \draw (0,1) -- (0.3,1.3);
\end{tikzpicture}
```

正方体的体积为 $V = a^3$。
````

系统会：
1. 自动检测 ````tikz...``` 代码块
2. 使用LaTeX编译生成图形
3. 将图形插入Word文档
4. 保留前后的文本和公式

## 示例

### 正方体
```tikz
\begin{tikzpicture}[scale=2]
  \draw[fill=gray!20] (0,0) -- (1,0) -- (1,1) -- (0,1) -- cycle;
  \draw[fill=gray!40] (0.3,0.3) -- (1.3,0.3) -- (1.3,1.3) -- (0.3,1.3) -- cycle;
  \draw (0,0) -- (0.3,0.3);
  \draw (1,0) -- (1.3,0.3);
  \draw (1,1) -- (1.3,1.3);
  \draw (0,1) -- (0.3,1.3);
\end{tikzpicture}
```

### 圆锥
```tikz
\begin{tikzpicture}[scale=2]
  \draw[fill=gray!20] (0,0) ellipse (1 and 0.3);
  \draw[fill=gray!40] (-1,0) -- (0,2) -- (1,0);
  \draw[dashed] (-1,0) arc (180:360:1 and 0.3);
\end{tikzpicture}
```

### 圆柱
```tikz
\begin{tikzpicture}[scale=2]
  \draw[fill=gray!20] (0,0) ellipse (1 and 0.3);
  \draw[fill=gray!40] (-1,0) -- (-1,2) arc (180:360:1 and 0.3) -- (1,0);
  \draw[dashed] (-1,0) arc (180:0:1 and 0.3);
  \draw (1,0) -- (1,2);
  \draw (-1,0) -- (-1,2);
  \draw (0,2) ellipse (1 and 0.3);
\end{tikzpicture}
```

## 测试

运行测试验证功能：
```bash
cd /path/to/advanceOCR
source .venv/bin/activate
python tests/test_tikz_integration.py
```

## 注意事项

1. **中文注释问题**：TikZ代码中的注释请使用英文
   ```latex
   % Good: This is a comment
   % Bad: 这是注释
   ```

2. **性能**：每个图形需要1-3秒渲染时间

3. **错误处理**：如果渲染失败，文档中会显示占位符

## 故障排除

### 问题：TikZ图形未显示
**检查**：
1. 运行 `pdflatex --version` 确认LaTeX已安装
2. 运行 `pdftoppm -v` 确认PDF转换工具已安装
3. 检查 `config/config.yaml` 中 `graphics.enabled: true`

### 问题：LaTeX编译失败
**检查**：
1. TikZ代码语法是否正确
2. 是否使用了中文注释（需移除）
3. 查看日志文件了解详细错误

### 问题：依赖缺失
**安装**：
```bash
# 完整安装（推荐）
sudo apt-get install texlive-full poppler-utils

# 最小安装
sudo apt-get install texlive-latex-base texlive-latex-extra \
                     texlive-pictures poppler-utils
```

## 更多信息

- **详细文档**：`docs/improvements/tikz_integration_summary.md`
- **设计方案**：`docs/improvements/3d_geometry_solution.md`
- **测试文件**：`tests/test_tikz_*.py`

## 配置选项

```yaml
graphics:
  enabled: true              # 启用/禁用图形渲染
  backend: "tikz"           # 渲染后端（目前支持tikz）

  tikz:
    latex_command: "pdflatex"    # LaTeX编译命令
    convert_dpi: 300             # 输出图片DPI
    timeout_seconds: 30          # 编译超时时间
```

---

**版本**: v1.0
**更新日期**: 2025-10-12
**状态**: ✅ 生产就绪

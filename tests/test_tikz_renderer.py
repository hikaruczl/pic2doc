#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试TikZ渲染器
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tikz_renderer import TikZRenderer

# 测试配置
config = {
    'graphics': {
        'enabled': True,
        'tikz': {
            'latex_command': 'pdflatex',
            'convert_dpi': 300
        }
    }
}

# 创建渲染器
renderer = TikZRenderer(config)

# 测试用例1：简单的立方体
tikz_cube = r"""
\begin{tikzpicture}[scale=2]
  % 后面的面
  \draw[fill=gray!20] (0,0) -- (1,0) -- (1,1) -- (0,1) -- cycle;
  % 前面的面
  \draw[fill=gray!40] (0.3,0.3) -- (1.3,0.3) -- (1.3,1.3) -- (0.3,1.3) -- cycle;
  % 连接线
  \draw (0,0) -- (0.3,0.3);
  \draw (1,0) -- (1.3,0.3);
  \draw (1,1) -- (1.3,1.3);
  \draw (0,1) -- (0.3,1.3);
\end{tikzpicture}
"""

# 测试用例2：圆锥
tikz_cone = r"""
\begin{tikzpicture}[scale=2]
  % 底面
  \draw[fill=gray!20] (0,0) ellipse (1 and 0.3);
  % 侧面
  \draw[fill=gray!40] (-1,0) -- (0,2) -- (1,0);
  % 虚线表示底面的后半部分
  \draw[dashed] (-1,0) arc (180:360:1 and 0.3);
\end{tikzpicture}
"""

print("=" * 80)
print("Testing TikZ Renderer")
print("=" * 80)

if not renderer.enabled:
    print("TikZ rendering is disabled. Please install LaTeX and ImageMagick.")
    sys.exit(1)

print("\nTest 1: Rendering a cube...")
image1 = renderer.render_tikz_to_image(tikz_cube, 'output/test_cube.png')
if image1:
    print(f"  Success! Image size: {image1.size}")
else:
    print("  Failed!")

print("\nTest 2: Rendering a cone...")
image2 = renderer.render_tikz_to_image(tikz_cone, 'output/test_cone.png')
if image2:
    print(f"  Success! Image size: {image2.size}")
else:
    print("  Failed!")

print("\nTest 3: Extracting TikZ blocks from text...")
test_content = """
这是一些文本内容。

下面是一个立方体图形：
""" + tikz_cube + """

还有更多文本。

下面是一个圆锥图形：
""" + tikz_cone + """

结束。
"""

blocks = renderer.extract_tikz_blocks(test_content)
print(f"  Found {len(blocks)} TikZ blocks")
for i, block in enumerate(blocks, 1):
    print(f"  Block {i}: position {block['start']}-{block['end']}")

print("\n" + "=" * 80)

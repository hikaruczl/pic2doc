#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试TikZ渲染器的LaTeX编译，显示详细错误"""

import sys
import os
import logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tikz_renderer import TikZRenderer

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

# 配置
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

# 简单的TikZ代码
tikz_code = r"""
\begin{tikzpicture}[scale=2]
  \draw[fill=gray!20] (0,0) -- (1,0) -- (1,1) -- (0,1) -- cycle;
  \draw[fill=gray!40] (0.3,0.3) -- (1.3,0.3) -- (1.3,1.3) -- (0.3,1.3) -- cycle;
  \draw (0,0) -- (0.3,0.3);
  \draw (1,0) -- (1.3,0.3);
  \draw (1,1) -- (1.3,1.3);
  \draw (0,1) -- (0.3,1.3);
\end{tikzpicture}
"""

print("Testing TikZ rendering with detailed error output...")
print("=" * 80)

image = renderer.render_tikz_to_image(tikz_code, 'output/test_debug.png')

if image:
    print("SUCCESS: Image rendered")
    print(f"Image size: {image.size}")
else:
    print("FAILED: Image not rendered")
    print("Check the log output above for LaTeX errors")

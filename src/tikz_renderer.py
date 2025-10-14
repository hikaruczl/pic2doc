#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikZ图形渲染器
将TikZ代码渲染为图片
"""

import os
import re
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)


class TikZRenderer:
    """TikZ代码渲染器"""

    # TikZ代码块匹配模式
    TIKZ_PATTERN = r'\\begin\{tikzpicture\}(.*?)\\end\{tikzpicture\}'

    def __init__(self, config: dict):
        """
        初始化TikZ渲染器

        Args:
            config: 配置字典
        """
        self.config = config
        self.graphics_config = config.get('graphics', {})
        self.enabled = self.graphics_config.get('enabled', False)

        # 渲染配置
        tikz_config = self.graphics_config.get('tikz', {})
        self.latex_command = tikz_config.get('latex_command', 'pdflatex')
        self.convert_dpi = tikz_config.get('convert_dpi', 300)

        # 检查依赖
        self._check_dependencies()

        logger.info("TikZRenderer initialized (enabled=%s)", self.enabled)

    def _check_dependencies(self):
        """检查必要的依赖是否安装"""
        if not self.enabled:
            return

        # 检查pdflatex
        try:
            subprocess.run([self.latex_command, '--version'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          timeout=5)
            logger.info("LaTeX command '%s' is available", self.latex_command)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("LaTeX command '%s' not found, TikZ rendering disabled",
                          self.latex_command)
            self.enabled = False
            return

        # 检查convert (ImageMagick)
        try:
            subprocess.run(['convert', '--version'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          timeout=5)
            logger.info("ImageMagick 'convert' is available")
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("ImageMagick 'convert' not found, will try dvipng")

    def extract_tikz_blocks(self, content: str) -> list:
        """
        从内容中提取TikZ代码块

        Args:
            content: 文本内容

        Returns:
            TikZ代码块列表
        """
        if not self.enabled:
            return []

        blocks = []
        for match in re.finditer(self.TIKZ_PATTERN, content, re.DOTALL):
            tikz_code = match.group(0)
            blocks.append({
                'code': tikz_code,
                'start': match.start(),
                'end': match.end()
            })

        return blocks

    def render_tikz_to_image(self, tikz_code: str, output_path: Optional[str] = None) -> Optional[Image.Image]:
        """
        将TikZ代码渲染为图片

        Args:
            tikz_code: TikZ代码
            output_path: 输出路径（可选）

        Returns:
            PIL Image对象，如果失败返回None
        """
        if not self.enabled:
            logger.warning("TikZ rendering is disabled")
            return None

        if '\\begin{tikzpicture}' not in tikz_code or '\\end{tikzpicture}' not in tikz_code:
            logger.error("TikZ code missing begin/end environment; skipping render")
            return None

        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # 创建完整的LaTeX文档
            latex_doc = self._create_latex_document(tikz_code)

            # 写入LaTeX文件
            tex_file = tmpdir_path / "tikz_figure.tex"
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_doc)

            # 编译LaTeX
            try:
                logger.info("Compiling LaTeX document...")
                result = subprocess.run(
                    [self.latex_command, '-interaction=nonstopmode', 'tikz_figure.tex'],
                    cwd=tmpdir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30
                )

                if result.returncode != 0:
                    logger.error("LaTeX compilation failed (return code: %d)", result.returncode)

                    # 输出详细的错误信息
                    stdout_text = result.stdout.decode('utf-8', errors='ignore')
                    stderr_text = result.stderr.decode('utf-8', errors='ignore')

                    # 从stdout中提取关键错误信息
                    error_lines = []
                    for line in stdout_text.split('\n'):
                        if '!' in line or 'Error' in line or 'error' in line:
                            error_lines.append(line)

                    if error_lines:
                        logger.error("LaTeX errors found:")
                        for line in error_lines[:10]:  # 只显示前10个错误
                            logger.error("  %s", line.strip())

                    logger.debug("Full stdout (first 1000 chars): %s", stdout_text[:1000])
                    logger.debug("Full stderr: %s", stderr_text)
                    return None

                # 转换PDF为PNG
                pdf_file = tmpdir_path / "tikz_figure.pdf"
                if not pdf_file.exists():
                    logger.error("PDF file not generated")
                    return None

                png_file = tmpdir_path / "tikz_figure.png"
                self._convert_pdf_to_png(pdf_file, png_file)

                if not png_file.exists():
                    logger.error("PNG file not generated")
                    return None

                # 读取图片
                image = Image.open(png_file)

                # 如果指定了输出路径，保存图片
                if output_path:
                    image.save(output_path)
                    logger.info("TikZ image saved to %s", output_path)

                return image

            except subprocess.TimeoutExpired:
                logger.error("LaTeX compilation timeout")
                return None
            except Exception as e:
                logger.error("TikZ rendering failed: %s", str(e))
                import traceback
                logger.debug(traceback.format_exc())
                return None

    def _create_latex_document(self, tikz_code: str) -> str:
        """
        创建完整的LaTeX文档

        Args:
            tikz_code: TikZ代码

        Returns:
            完整的LaTeX文档
        """
        return r"""
\documentclass[tikz,border=10pt]{standalone}
\usepackage{tikz}
\usetikzlibrary{3d,arrows,calc,decorations.markings,decorations.pathreplacing,angles,quotes}

\begin{document}
""" + tikz_code + r"""
\end{document}
"""

    def _convert_pdf_to_png(self, pdf_file: Path, png_file: Path):
        """
        将PDF转换为PNG

        Args:
            pdf_file: PDF文件路径
            png_file: PNG文件路径
        """
        # 尝试使用convert (ImageMagick)
        try:
            subprocess.run(
                ['convert', '-density', str(self.convert_dpi),
                 str(pdf_file), str(png_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=True
            )
            logger.debug("PDF converted to PNG using ImageMagick")
            return
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.debug("ImageMagick convert failed, trying pdftoppm")

        # 尝试使用pdftoppm
        try:
            subprocess.run(
                ['pdftoppm', '-png', '-r', str(self.convert_dpi),
                 str(pdf_file), str(png_file.with_suffix(''))],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=True
            )
            # pdftoppm会生成带后缀的文件
            generated_file = png_file.with_name(png_file.stem + '-1.png')
            if generated_file.exists():
                generated_file.rename(png_file)
            logger.debug("PDF converted to PNG using pdftoppm")
            return
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("Failed to convert PDF to PNG")

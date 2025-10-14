#!/usr/bin/env python3
"""Command line helper for generating a Word document from LaTeX formulas."""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))


try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - yaml is optional at runtime
    yaml = None


from src.formula_converter import FormulaConverter
from src.document_generator import DocumentGenerator


def load_config(config_path: Path) -> dict:
    """Load YAML config if available and provide sensible defaults."""
    config: dict = {}

    if yaml is not None and config_path.exists():
        try:
            with config_path.open('r', encoding='utf-8') as handle:
                loaded = yaml.safe_load(handle)
                if isinstance(loaded, dict):
                    config = loaded
        except Exception as exc:  # pragma: no cover - defensive logging
            logging.warning("加载配置文件失败，将使用默认配置: %s", exc)

    output_cfg = config.setdefault('output', {})
    output_cfg.setdefault('directory', 'output')

    document_cfg = config.setdefault('document', {})
    document_cfg.setdefault('default_font', 'Arial')
    document_cfg.setdefault('default_font_size', 11)

    graphics_cfg = config.setdefault('graphics', {})
    graphics_cfg.setdefault('enabled', False)

    formula_cfg = config.setdefault('formula', {})
    formula_cfg.setdefault('output_format', 'mathml')
    formula_cfg.setdefault('preserve_latex', True)

    return config


def build_elements(content: str, converter: FormulaConverter, single_formula: bool) -> list:
    """Create Word-ready elements from the provided LaTeX content."""
    content = content.strip()
    if not content:
        raise ValueError('输入内容为空，无法生成公式文档。')

    if single_formula:
        mathml = converter.convert_latex_to_mathml(content)
        return [{
            'type': 'formula',
            'formula_type': 'display',
            'latex': content,
            'mathml': mathml,
        }]

    elements = converter.parse_content(content)
    formatted = converter.format_for_word(elements)

    has_formula = any(item.get('type') == 'formula' for item in formatted)
    if not has_formula:
        mathml = converter.convert_latex_to_mathml(content)
        return [{
            'type': 'formula',
            'formula_type': 'display',
            'latex': content,
            'mathml': mathml,
        }]

    return formatted


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='根据 LaTeX 内容快速生成 Word 文档（用于矩阵等公式预览）'
    )
    parser.add_argument('--latex', help='直接提供的 LaTeX 字符串')
    parser.add_argument('--file', help='包含 LaTeX 内容的文本文件路径')
    parser.add_argument('--output', help='输出文件名，默认遵循配置文件设置')
    parser.add_argument('--single-formula', action='store_true',
                        help='将输入整体视为单个显示公式进行转换')
    parser.add_argument('--config', default='config/config.yaml',
                        help='可选的配置文件路径，默认使用项目配置')
    parser.add_argument('--debug', action='store_true', help='输出调试日志')
    return parser.parse_args()


def read_input_text(args: argparse.Namespace) -> str:
    if args.latex:
        return args.latex

    if args.file:
        path = Path(args.file)
        if not path.exists():
            raise FileNotFoundError(f'找不到指定的文件: {path}')
        return path.read_text(encoding='utf-8')

    if not sys.stdin.isatty():
        return sys.stdin.read()

    raise ValueError('请通过 --latex、--file 或标准输入提供 LaTeX 内容。')


def main() -> None:
    args = parse_arguments()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format='[%(levelname)s] %(message)s')

    config_path = Path(args.config)
    config = load_config(config_path)

    output_dir = Path(config['output']['directory'])
    output_dir.mkdir(parents=True, exist_ok=True)

    converter = FormulaConverter(config)
    generator = DocumentGenerator(config)

    latex_content = read_input_text(args)
    elements = build_elements(latex_content, converter, args.single_formula)

    doc = generator.create_document(elements, metadata=None, minimal_layout=True)
    output_path = generator.save_document(doc, args.output)

    print(f'文档已生成: {output_path}')


if __name__ == '__main__':
    main()

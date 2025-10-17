#!/usr/bin/env python3
"""测试新的几何图形方案"""

import sys
import logging

# 直接导入模块
sys.path.insert(0, '/mnt/vdb/dev/advanceOCR')
from src.geometry_renderer import GeometryRenderer, parse_geometry_json

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 测试内容（模拟LLM输出）
test_content = """【题目】
1. （0分）（2016高二上·重庆期中）如图所示，平面四边形 $ ADEF $ 与梯形 $ ABCD $ 所在的平面互相垂直，$ AD \\perp CD $，$ AD \\perp ED $，$ AF \\parallel DE $，$ AB \\parallel CD $，$ CD = 2AB = 2AD = 2ED = xAF $。

（Ⅰ）若四点 $ F $、$ B $、$ C $、$ E $ 共面，$ AB = a $，求 $ x $ 的值；

【图形】
[
  {"type": "point", "pos": [100, 100], "label": "A"},
  {"type": "point", "pos": [200, 100], "label": "B"},
  {"type": "point", "pos": [250, 200], "label": "C"},
  {"type": "point", "pos": [100, 200], "label": "D"},
  {"type": "point", "pos": [100, 50], "label": "E"},
  {"type": "point", "pos": [150, 50], "label": "F"},
  {"type": "line", "start": [100, 100], "end": [200, 100], "style": "solid"},
  {"type": "line", "start": [200, 100], "end": [250, 200], "style": "solid"},
  {"type": "line", "start": [250, 200], "end": [100, 200], "style": "solid"},
  {"type": "line", "start": [100, 200], "end": [100, 100], "style": "solid"},
  {"type": "line", "start": [100, 100], "end": [100, 50], "style": "solid"},
  {"type": "line", "start": [100, 50], "end": [150, 50], "style": "solid"},
  {"type": "line", "start": [150, 50], "end": [100, 100], "style": "dashed"},
  {"type": "line", "start": [100, 200], "end": [100, 50], "style": "dashed"}
]
"""

def test_parse():
    """测试解析"""
    logger.info("=" * 80)
    logger.info("测试1: 解析几何JSON")
    logger.info("=" * 80)

    elements = parse_geometry_json(test_content)
    if elements:
        logger.info(f"成功解析 {len(elements)} 个几何元素")
        for i, elem in enumerate(elements):
            logger.info(f"  元素 {i+1}: {elem['type']}")
    else:
        logger.error("解析失败")

    return elements

def test_render(elements):
    """测试渲染"""
    if not elements:
        logger.error("没有元素可渲染")
        return

    logger.info("\n" + "=" * 80)
    logger.info("测试2: 渲染几何图形")
    logger.info("=" * 80)

    try:
        renderer = GeometryRenderer(width=800, height=600, padding=40)
        image = renderer.render_to_pil(elements)
        logger.info(f"渲染成功: {image.size}")

        # 保存测试图片
        output_path = "output/geometry_test.png"
        image.save(output_path)
        logger.info(f"测试图片已保存: {output_path}")

    except Exception as e:
        logger.error(f"渲染失败: {e}", exc_info=True)

if __name__ == "__main__":
    # 执行测试
    elements = test_parse()
    if elements:
        test_render(elements)

    logger.info("\n" + "=" * 80)
    logger.info("测试完成")
    logger.info("=" * 80)

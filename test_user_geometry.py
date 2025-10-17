#!/usr/bin/env python3
import json
import logging
import sys
import importlib.util

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入geometry_renderer模块
spec = importlib.util.spec_from_file_location('geometry_renderer', '/mnt/vdb/dev/advanceOCR/src/geometry_renderer.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

GeometryRenderer = module.GeometryRenderer
parse_geometry_json = module.parse_geometry_json

# 用户提供的完整内容
test_content = '''【图形】
[
  {"type": "point", "pos": [50, 280], "label": "A"},
  {"type": "point", "pos": [140, 280], "label": "B"},
  {"type": "point", "pos": [230, 200], "label": "C"},
  {"type": "point", "pos": [140, 200], "label": "D"},
  {"type": "point", "pos": [100, 120], "label": "E"},
  {"type": "point", "pos": [50, 170], "label": "F"},
  {"type": "line", "start": [50, 280], "end": [140, 280], "style": "solid"},
  {"type": "line", "start": [140, 280], "end": [230, 200], "style": "solid"},
  {"type": "line", "start": [230, 200], "end": [140, 200], "style": "solid"},
  {"type": "line", "start": [140, 200], "end": [50, 280], "style": "dashed"},
  {"type": "line", "start": [50, 280], "end": [100, 120], "style": "solid"},
  {"type": "line", "start": [140, 280], "end": [100, 120], "style": "solid"},
  {"type": "line", "start": [230, 200], "end": [100, 120], "style": "solid"},
  {"type": "line", "start": [140, 200], "end": [100, 120], "style": "solid"},
  {"type": "line", "start": [50, 170], "end": [100, 120], "style": "solid"},
  {"type": "line", "start": [50, 170], "end": [50, 280], "style": "solid"}
]
'''

logger.info('=' * 80)
logger.info('测试用户提供的几何JSON')
logger.info('=' * 80)

# 解析
elements = parse_geometry_json(test_content)
if elements:
    logger.info(f'✓ 成功解析 {len(elements)} 个几何元素')
    for i, elem in enumerate(elements[:5]):
        logger.info(f'  元素 {i+1}: {elem}')
    if len(elements) > 5:
        logger.info(f'  ... 还有 {len(elements)-5} 个元素')
else:
    logger.error('✗ 解析失败')
    sys.exit(1)

# 渲染
try:
    logger.info('\n渲染几何图形...')
    renderer = GeometryRenderer(width=800, height=600, padding=50)
    image = renderer.render_to_pil(elements)
    logger.info(f'✓ 渲染成功: {image.size[0]}x{image.size[1]}')

    # 保存
    output_path = 'output/user_geometry.png'
    image.save(output_path)
    logger.info(f'✓ 已保存到: {output_path}')

    logger.info('\n' + '=' * 80)
    logger.info('测试完成！')
    logger.info('=' * 80)
except Exception as e:
    logger.error(f'✗ 渲染失败: {e}', exc_info=True)
    sys.exit(1)

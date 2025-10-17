"""
几何图形渲染模块
使用Cairo渲染几何元素JSON为PNG/EMF图像
"""

import io
import json
import math
import logging
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image

try:
    import cairo
    CAIRO_AVAILABLE = True
except ImportError:
    CAIRO_AVAILABLE = False

logger = logging.getLogger(__name__)


class GeometryRenderer:
    """几何图形渲染器"""

    def __init__(self, width: int = 800, height: int = 600, padding: int = 40):
        """
        初始化渲染器

        Args:
            width: 画布宽度
            height: 画布高度
            padding: 边距
        """
        if not CAIRO_AVAILABLE:
            raise ImportError("Cairo库未安装，请运行: pip install pycairo")

        self.width = width
        self.height = height
        self.padding = padding
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

    def render_to_png(self, geometry_elements: List[Dict[str, Any]]) -> bytes:
        """
        渲染几何元素为PNG图像

        Args:
            geometry_elements: 几何元素列表

        Returns:
            PNG图像字节流
        """
        # 创建Cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        ctx = cairo.Context(surface)

        # 白色背景
        ctx.set_source_rgb(1, 1, 1)
        ctx.paint()

        # 计算坐标变换（自动缩放和居中）
        self._calculate_transform(geometry_elements)

        # 渲染所有元素
        for element in geometry_elements:
            self._render_element(ctx, element)

        # 保存为PNG
        png_io = io.BytesIO()
        surface.write_to_png(png_io)
        png_io.seek(0)

        return png_io.getvalue()

    def render_to_pil(self, geometry_elements: List[Dict[str, Any]]) -> Image.Image:
        """
        渲染几何元素为PIL Image

        Args:
            geometry_elements: 几何元素列表

        Returns:
            PIL Image对象
        """
        png_bytes = self.render_to_png(geometry_elements)
        return Image.open(io.BytesIO(png_bytes))

    def _calculate_transform(self, elements: List[Dict[str, Any]]):
        """计算坐标变换参数（缩放和偏移）"""
        if not elements:
            return

        # 收集所有坐标点
        all_coords = []
        for elem in elements:
            elem_type = elem.get('type', '')

            if elem_type == 'point':
                all_coords.append(elem['pos'])
            elif elem_type == 'line':
                all_coords.extend([elem['start'], elem['end']])
            elif elem_type == 'circle':
                center = elem['center']
                radius = elem['radius']
                all_coords.extend([
                    [center[0] - radius, center[1] - radius],
                    [center[0] + radius, center[1] + radius]
                ])
            elif elem_type == 'polygon':
                all_coords.extend(elem['points'])
            elif elem_type == 'arrow':
                all_coords.extend([elem['start'], elem['end']])
            elif elem_type == 'label':
                all_coords.append(elem['pos'])

        if not all_coords:
            return

        # 计算边界框
        xs = [c[0] for c in all_coords]
        ys = [c[1] for c in all_coords]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # 计算缩放比例
        content_width = max_x - min_x
        content_height = max_y - min_y

        if content_width == 0 or content_height == 0:
            self.scale = 1.0
            self.offset_x = self.width / 2
            self.offset_y = self.height / 2
            return

        available_width = self.width - 2 * self.padding
        available_height = self.height - 2 * self.padding

        scale_x = available_width / content_width if content_width > 0 else 1
        scale_y = available_height / content_height if content_height > 0 else 1

        self.scale = min(scale_x, scale_y)

        # 计算偏移量（居中）
        scaled_width = content_width * self.scale
        scaled_height = content_height * self.scale

        self.offset_x = self.padding + (available_width - scaled_width) / 2 - min_x * self.scale
        self.offset_y = self.padding + (available_height - scaled_height) / 2 - min_y * self.scale

        logger.info(f"坐标变换: scale={self.scale:.2f}, offset=({self.offset_x:.2f}, {self.offset_y:.2f})")

    def _transform_point(self, point: List[float]) -> Tuple[float, float]:
        """应用坐标变换"""
        x = point[0] * self.scale + self.offset_x
        y = point[1] * self.scale + self.offset_y
        return x, y

    def _render_element(self, ctx, element: Dict[str, Any]):
        """渲染单个几何元素"""
        elem_type = element.get('type', '')

        try:
            if elem_type == 'point':
                self._render_point(ctx, element)
            elif elem_type == 'line':
                self._render_line(ctx, element)
            elif elem_type == 'circle':
                self._render_circle(ctx, element)
            elif elem_type == 'arc':
                self._render_arc(ctx, element)
            elif elem_type == 'polygon':
                self._render_polygon(ctx, element)
            elif elem_type == 'arrow':
                self._render_arrow(ctx, element)
            elif elem_type == 'label':
                self._render_label(ctx, element)
            else:
                logger.warning(f"未知的几何元素类型: {elem_type}")
        except Exception as e:
            logger.error(f"渲染元素失败 {elem_type}: {e}")

    def _render_point(self, ctx, element: Dict[str, Any]):
        """渲染点"""
        x, y = self._transform_point(element['pos'])
        label = element.get('label', '')

        # 绘制点
        ctx.set_source_rgb(0, 0, 0)
        ctx.arc(x, y, 3, 0, 2 * math.pi)
        ctx.fill()

        # 绘制标签
        if label:
            ctx.set_font_size(14)
            ctx.move_to(x + 6, y - 6)
            ctx.show_text(label)

    def _render_line(self, ctx, element: Dict[str, Any]):
        """渲染线段"""
        x1, y1 = self._transform_point(element['start'])
        x2, y2 = self._transform_point(element['end'])
        style = element.get('style', 'solid')

        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(2)

        if style == 'dashed':
            ctx.set_dash([10, 5])
        elif style == 'dotted':
            ctx.set_dash([2, 3])
        else:
            ctx.set_dash([])

        ctx.move_to(x1, y1)
        ctx.line_to(x2, y2)
        ctx.stroke()

        ctx.set_dash([])  # 重置

    def _render_circle(self, ctx, element: Dict[str, Any]):
        """渲染圆"""
        cx, cy = self._transform_point(element['center'])
        radius = element['radius'] * self.scale
        style = element.get('style', 'solid')

        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(2)

        if style == 'dashed':
            ctx.set_dash([10, 5])
        elif style == 'dotted':
            ctx.set_dash([2, 3])
        else:
            ctx.set_dash([])

        ctx.arc(cx, cy, radius, 0, 2 * math.pi)
        ctx.stroke()

        ctx.set_dash([])

    def _render_arc(self, ctx, element: Dict[str, Any]):
        """渲染圆弧"""
        cx, cy = self._transform_point(element['center'])
        radius = element['radius'] * self.scale
        start_angle = math.radians(element.get('start_angle', 0))
        end_angle = math.radians(element.get('end_angle', 90))

        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(2)
        ctx.arc(cx, cy, radius, start_angle, end_angle)
        ctx.stroke()

    def _render_polygon(self, ctx, element: Dict[str, Any]):
        """渲染多边形"""
        points = element['points']
        if len(points) < 2:
            return

        style = element.get('style', 'solid')
        filled = element.get('filled', False)

        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(2)

        if style == 'dashed':
            ctx.set_dash([10, 5])
        elif style == 'dotted':
            ctx.set_dash([2, 3])
        else:
            ctx.set_dash([])

        # 移动到第一个点
        x, y = self._transform_point(points[0])
        ctx.move_to(x, y)

        # 连接其他点
        for point in points[1:]:
            x, y = self._transform_point(point)
            ctx.line_to(x, y)

        # 闭合路径
        ctx.close_path()

        if filled:
            ctx.fill_preserve()
        ctx.stroke()

        ctx.set_dash([])

    def _render_arrow(self, ctx, element: Dict[str, Any]):
        """渲染箭头"""
        x1, y1 = self._transform_point(element['start'])
        x2, y2 = self._transform_point(element['end'])

        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(2)

        # 绘制线段
        ctx.move_to(x1, y1)
        ctx.line_to(x2, y2)
        ctx.stroke()

        # 绘制箭头头部
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_size = 12

        ctx.move_to(x2, y2)
        ctx.line_to(
            x2 - arrow_size * math.cos(angle - math.pi / 6),
            y2 - arrow_size * math.sin(angle - math.pi / 6)
        )
        ctx.move_to(x2, y2)
        ctx.line_to(
            x2 - arrow_size * math.cos(angle + math.pi / 6),
            y2 - arrow_size * math.sin(angle + math.pi / 6)
        )
        ctx.stroke()

    def _render_label(self, ctx, element: Dict[str, Any]):
        """渲染文字标签"""
        x, y = self._transform_point(element['pos'])
        text = element.get('text', '')

        if not text:
            return

        ctx.set_source_rgb(0, 0, 0)
        ctx.set_font_size(14)
        ctx.move_to(x, y)
        ctx.show_text(text)


def parse_geometry_json(content: str) -> Optional[List[Dict[str, Any]]]:
    """
    从LLM输出中解析几何JSON

    Args:
        content: LLM输出内容

    Returns:
        几何元素列表，如果没有找到则返回None
    """
    # 查找【图形】标记
    if '【图形】' not in content:
        return None

    # 提取【图形】之后的内容
    parts = content.split('【图形】', 1)
    if len(parts) < 2:
        return None

    geometry_section = parts[1].strip()

    # 尝试解析JSON
    try:
        # 找到JSON数组的开始和结束
        start_idx = geometry_section.find('[')
        if start_idx == -1:
            logger.warning("未找到JSON数组开始标记")
            return None

        # 找到对应的结束括号
        bracket_count = 0
        end_idx = -1
        for i in range(start_idx, len(geometry_section)):
            if geometry_section[i] == '[':
                bracket_count += 1
            elif geometry_section[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = i + 1
                    break

        if end_idx == -1:
            logger.warning("未找到JSON数组结束标记")
            return None

        json_str = geometry_section[start_idx:end_idx]
        elements = json.loads(json_str)

        if not isinstance(elements, list):
            logger.warning("几何JSON不是数组格式")
            return None

        logger.info(f"成功解析 {len(elements)} 个几何元素")
        return elements

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        return None
    except Exception as e:
        logger.error(f"解析几何JSON时出错: {e}")
        return None

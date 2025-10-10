"""
使用示例
演示如何使用Advanced OCR系统
"""

import os
from pathlib import Path
from src.main import AdvancedOCR


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("示例 1: 基本使用")
    print("=" * 60)
    
    # 创建OCR实例
    ocr = AdvancedOCR(config_path='config/config.yaml')
    
    # 处理单个图像
    image_path = 'tests/sample_images/math_problem_1.png'
    
    if not os.path.exists(image_path):
        print(f"⚠ 示例图像不存在: {image_path}")
        print("请先准备测试图像")
        return
    
    result = ocr.process_image(image_path)
    
    if result['success']:
        print(f"✓ 处理成功!")
        print(f"  输出文件: {result['output_path']}")
        print(f"  公式数量: {result['statistics']['total_formulas']}")
        print(f"  - 显示公式: {result['statistics']['display_formulas']}")
        print(f"  - 行内公式: {result['statistics']['inline_formulas']}")
        print(f"  元素数量: {result['elements_count']}")
    else:
        print(f"✗ 处理失败: {result['error']}")


def example_custom_output():
    """自定义输出文件名示例"""
    print("\n" + "=" * 60)
    print("示例 2: 自定义输出文件名")
    print("=" * 60)
    
    ocr = AdvancedOCR()
    
    image_path = 'tests/sample_images/math_problem_1.png'
    
    if not os.path.exists(image_path):
        print(f"⚠ 示例图像不存在: {image_path}")
        return
    
    # 指定输出文件名
    result = ocr.process_image(image_path, output_filename='my_math_problem.docx')
    
    if result['success']:
        print(f"✓ 文档已保存到: {result['output_path']}")


def example_batch_processing():
    """批量处理示例"""
    print("\n" + "=" * 60)
    print("示例 3: 批量处理多个图像")
    print("=" * 60)
    
    ocr = AdvancedOCR()
    
    # 准备图像列表
    image_dir = Path('tests/sample_images')
    
    if not image_dir.exists():
        print(f"⚠ 示例图像目录不存在: {image_dir}")
        return
    
    # 获取所有图像文件
    image_paths = []
    for ext in ['.png', '.jpg', '.jpeg', '.pdf']:
        image_paths.extend(image_dir.glob(f'*{ext}'))
    
    if not image_paths:
        print("⚠ 未找到图像文件")
        return
    
    print(f"找到 {len(image_paths)} 个图像文件")
    
    # 批量处理
    results = ocr.process_batch([str(p) for p in image_paths])
    
    # 统计结果
    success_count = sum(1 for r in results if r['success'])
    print(f"\n批量处理完成:")
    print(f"  成功: {success_count}/{len(results)}")
    print(f"  失败: {len(results) - success_count}/{len(results)}")
    
    # 显示详细结果
    for idx, result in enumerate(results, 1):
        if result['success']:
            print(f"  [{idx}] ✓ {result['output_path']}")
        else:
            print(f"  [{idx}] ✗ {result['error']}")


def example_component_usage():
    """单独使用各个组件的示例"""
    print("\n" + "=" * 60)
    print("示例 4: 单独使用各个组件")
    print("=" * 60)
    
    import yaml
    from dotenv import load_dotenv
    from src.image_processor import ImageProcessor
    from src.llm_client import LLMClient
    from src.formula_converter import FormulaConverter
    from src.document_generator import DocumentGenerator
    
    # 加载配置
    load_dotenv()
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 1. 使用图像处理器
    print("\n1. 图像处理器")
    image_processor = ImageProcessor(config)
    
    image_path = 'tests/sample_images/math_problem_1.png'
    if os.path.exists(image_path):
        is_valid, error = image_processor.validate_image(image_path)
        print(f"   图像验证: {'✓ 有效' if is_valid else f'✗ 无效 - {error}'}")
        
        if is_valid:
            processed_images, original_image = image_processor.process_image(image_path)
            print(f"   处理完成: {len(processed_images)} 张图像分片，原图尺寸: {original_image.size}")
    
    # 2. 使用公式转换器
    print("\n2. 公式转换器")
    formula_converter = FormulaConverter(config)
    
    sample_text = """
    这是一个示例文本,包含公式:
    
    行内公式: $E = mc^2$
    
    显示公式:
    $$\\int_{0}^{\\infty} e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$
    """
    
    stats = formula_converter.get_formula_statistics(sample_text)
    print(f"   找到 {stats['total_formulas']} 个公式")
    
    elements = formula_converter.parse_content(sample_text)
    print(f"   解析出 {len(elements)} 个元素")
    
    # 3. 使用文档生成器
    print("\n3. 文档生成器")
    doc_generator = DocumentGenerator(config)
    
    formatted_elements = formula_converter.format_for_word(elements)
    doc = doc_generator.create_document(formatted_elements)
    print(f"   文档创建完成,包含 {len(formatted_elements)} 个元素")


def example_error_handling():
    """错误处理示例"""
    print("\n" + "=" * 60)
    print("示例 5: 错误处理")
    print("=" * 60)
    
    ocr = AdvancedOCR()
    
    # 测试不存在的文件
    print("\n测试 1: 不存在的文件")
    result = ocr.process_image('nonexistent.png')
    print(f"  结果: {'✓ 成功' if result['success'] else f'✗ 失败 - {result[\"error\"]}'}")
    
    # 测试不支持的格式
    print("\n测试 2: 不支持的格式")
    # 创建临时文件
    temp_file = 'temp_test.txt'
    with open(temp_file, 'w') as f:
        f.write('test')
    
    result = ocr.process_image(temp_file)
    print(f"  结果: {'✓ 成功' if result['success'] else f'✗ 失败 - {result[\"error\"]}'}")
    
    # 清理
    if os.path.exists(temp_file):
        os.remove(temp_file)


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("Advanced OCR 使用示例")
    print("=" * 60)
    
    # 检查环境变量
    if not os.getenv('OPENAI_API_KEY') and not os.getenv('ANTHROPIC_API_KEY'):
        print("\n⚠ 警告: 未设置API密钥!")
        print("请在.env文件中设置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY")
        print("参考 .env.example 文件")
        return
    
    # 运行示例
    try:
        example_basic_usage()
        example_custom_output()
        example_batch_processing()
        example_component_usage()
        example_error_handling()
        
        print("\n" + "=" * 60)
        print("所有示例运行完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 运行示例时出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

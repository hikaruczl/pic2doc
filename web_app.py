"""
Advanced OCR Web界面 - 基于Gradio
提供友好的图形界面用于数学问题图像转Word文档
"""

import os
import gradio as gr
from pathlib import Path
from datetime import datetime
import yaml
from dotenv import load_dotenv

from src.main import AdvancedOCR
from src.formula_converter import FormulaConverter

# 加载环境变量
load_dotenv()

# 加载配置
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 初始化OCR系统
ocr = AdvancedOCR()
formula_converter = FormulaConverter(config)


def process_image(image_file, llm_provider, include_image, image_quality):
    """
    处理上传的图像
    
    Args:
        image_file: 上传的图像文件
        llm_provider: 选择的LLM提供商
        include_image: 是否在Word中包含原始图像
        image_quality: 图像质量
        
    Returns:
        (输出文件路径, 处理结果信息, 公式统计)
    """
    try:
        if image_file is None:
            return None, "❌ 请上传图像文件", ""
        
        # 更新配置
        ocr.config['llm']['primary_provider'] = llm_provider.lower()
        ocr.config['document']['include_original_image'] = include_image
        ocr.config['image']['quality'] = image_quality
        
        # 重新初始化LLM客户端
        from src.llm_client import LLMClient
        from src.image_processor import ImageProcessor
        ocr.llm_client = LLMClient(ocr.config, ocr.image_processor)
        
        # 处理图像
        result = ocr.process_image(image_file.name)
        
        if result['success']:
            # 准备结果信息
            stats = result['statistics']
            info = f"""
✅ **处理成功!**

📊 **统计信息:**
- 总公式数: {stats['total_formulas']}
- 显示公式: {stats['display_formulas']}
- 行内公式: {stats['inline_formulas']}
- 元素数量: {result['elements_count']}

🤖 **使用模型:**
- 提供商: {result['analysis']['provider']}
- 模型: {result['analysis']['model']}

📄 **输出文件:** {result['output_path']}
"""
            
            # 准备公式列表
            formulas_text = "**识别的公式:**\n\n"
            for idx, (formula_type, latex) in enumerate(stats['formulas'][:10], 1):
                formulas_text += f"{idx}. [{formula_type}] `{latex}`\n"
            
            if len(stats['formulas']) > 10:
                formulas_text += f"\n... 还有 {len(stats['formulas']) - 10} 个公式"
            
            return result['output_path'], info, formulas_text
        else:
            return None, f"❌ 处理失败: {result['error']}", ""
            
    except Exception as e:
        return None, f"❌ 发生错误: {str(e)}", ""


def batch_process(files, llm_provider):
    """
    批量处理多个图像
    
    Args:
        files: 上传的文件列表
        llm_provider: 选择的LLM提供商
        
    Returns:
        处理结果摘要
    """
    try:
        if not files:
            return "❌ 请上传至少一个文件"
        
        # 更新配置
        ocr.config['llm']['primary_provider'] = llm_provider.lower()
        
        # 重新初始化LLM客户端
        from src.llm_client import LLMClient
        ocr.llm_client = LLMClient(ocr.config, ocr.image_processor)
        
        # 批量处理
        file_paths = [f.name for f in files]
        results = ocr.process_batch(file_paths)
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        total_formulas = sum(r.get('statistics', {}).get('total_formulas', 0) 
                           for r in results if r['success'])
        
        # 准备结果信息
        summary = f"""
✅ **批量处理完成!**

📊 **处理统计:**
- 总文件数: {len(results)}
- 成功: {success_count}
- 失败: {len(results) - success_count}
- 总公式数: {total_formulas}

📄 **处理结果:**
"""
        
        for idx, result in enumerate(results, 1):
            if result['success']:
                summary += f"\n{idx}. ✅ {Path(file_paths[idx-1]).name} - {result['statistics']['total_formulas']} 个公式"
            else:
                summary += f"\n{idx}. ❌ {Path(file_paths[idx-1]).name} - {result['error']}"
        
        return summary
        
    except Exception as e:
        return f"❌ 批量处理失败: {str(e)}"


def get_model_info(provider):
    """获取模型信息"""
    model_info = {
        "OpenAI": {
            "模型": "GPT-4 Vision",
            "准确率": "95%",
            "成本": "$10-50/1K图",
            "速度": "10-20秒",
            "推荐": "高精度场景"
        },
        "Anthropic": {
            "模型": "Claude 3 Sonnet",
            "准确率": "90%",
            "成本": "$3-8/1K图",
            "速度": "5-12秒",
            "推荐": "平衡性价比 ⭐推荐"
        },
        "Gemini": {
            "模型": "Gemini 1.5 Flash",
            "准确率": "88%",
            "成本": "$0.35-1.05/1K图",
            "速度": "4-10秒",
            "推荐": "性价比之王 ⭐⭐推荐"
        },
        "Qwen": {
            "模型": "Qwen-VL-Plus",
            "准确率": "89%",
            "成本": "$1.4-2.8/1K图",
            "速度": "6-12秒",
            "推荐": "国内用户优选"
        }
    }
    
    info = model_info.get(provider, {})
    if info:
        return f"""
**{provider} 模型信息:**

- 模型: {info['模型']}
- 准确率: {info['准确率']}
- 成本: {info['成本']}
- 响应速度: {info['速度']}
- 推荐场景: {info['推荐']}
"""
    return "请选择LLM提供商"


# 创建Gradio界面
with gr.Blocks(title="Advanced OCR - 数学问题图像转Word", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎓 Advanced OCR - 数学问题图像转Word文档
    
    将包含数学公式的图像转换为可编辑的Word文档，支持多种多模态LLM。
    """)
    
    with gr.Tabs():
        # 单图像处理标签页
        with gr.TabItem("📄 单图像处理"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 上传图像")
                    image_input = gr.File(
                        label="选择图像文件",
                        file_types=[".png", ".jpg", ".jpeg", ".pdf"],
                        type="filepath"
                    )
                    
                    gr.Markdown("### 配置选项")
                    llm_provider = gr.Dropdown(
                        choices=["OpenAI", "Anthropic", "Gemini", "Qwen"],
                        value="Gemini",
                        label="LLM提供商",
                        info="选择用于图像分析的AI模型"
                    )
                    
                    include_image = gr.Checkbox(
                        value=True,
                        label="在Word中包含原始图像"
                    )
                    
                    image_quality = gr.Slider(
                        minimum=70,
                        maximum=100,
                        value=95,
                        step=5,
                        label="图像质量",
                        info="影响输出文件大小"
                    )
                    
                    process_btn = gr.Button("🚀 开始处理", variant="primary", size="lg")
                
                with gr.Column(scale=1):
                    gr.Markdown("### 模型信息")
                    model_info_display = gr.Markdown(get_model_info("Gemini"))
                    
                    gr.Markdown("### 处理结果")
                    result_info = gr.Markdown()
                    
                    gr.Markdown("### 识别的公式")
                    formulas_display = gr.Markdown()
                    
                    output_file = gr.File(label="下载Word文档")
            
            # 更新模型信息
            llm_provider.change(
                fn=get_model_info,
                inputs=[llm_provider],
                outputs=[model_info_display]
            )
            
            # 处理按钮点击
            process_btn.click(
                fn=process_image,
                inputs=[image_input, llm_provider, include_image, image_quality],
                outputs=[output_file, result_info, formulas_display]
            )
        
        # 批量处理标签页
        with gr.TabItem("📚 批量处理"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 上传多个图像")
                    batch_files = gr.File(
                        label="选择多个图像文件",
                        file_count="multiple",
                        file_types=[".png", ".jpg", ".jpeg", ".pdf"]
                    )
                    
                    batch_llm_provider = gr.Dropdown(
                        choices=["OpenAI", "Anthropic", "Gemini", "Qwen"],
                        value="Gemini",
                        label="LLM提供商"
                    )
                    
                    batch_process_btn = gr.Button("🚀 批量处理", variant="primary", size="lg")
                
                with gr.Column():
                    gr.Markdown("### 批量处理结果")
                    batch_result = gr.Markdown()
            
            batch_process_btn.click(
                fn=batch_process,
                inputs=[batch_files, batch_llm_provider],
                outputs=[batch_result]
            )
        
        # 帮助标签页
        with gr.TabItem("❓ 帮助"):
            gr.Markdown("""
            ## 使用说明
            
            ### 1. 准备工作
            - 确保已配置API密钥 (在 `.env` 文件中)
            - 准备包含数学问题的图像文件
            
            ### 2. 单图像处理
            1. 上传图像文件 (支持 PNG, JPG, PDF)
            2. 选择LLM提供商
            3. 配置选项 (可选)
            4. 点击"开始处理"
            5. 等待处理完成
            6. 下载生成的Word文档
            
            ### 3. 批量处理
            1. 上传多个图像文件
            2. 选择LLM提供商
            3. 点击"批量处理"
            4. 查看处理结果
            5. 在 `output/` 目录查找生成的文档
            
            ### 4. LLM提供商选择
            - **Gemini**: 性价比最高,推荐日常使用
            - **Anthropic**: 平衡准确率和成本
            - **OpenAI**: 最高准确率,适合高要求场景
            - **Qwen**: 国内用户优选,中文支持好
            
            ### 5. 注意事项
            - 图像质量越高,识别准确率越高
            - 复杂公式可能需要手动调整
            - API调用会产生费用,请注意控制使用量
            
            ### 6. 获取帮助
            - 查看 [README.md](README.md) 了解详细信息
            - 查看 [MODEL_COMPARISON.md](MODEL_COMPARISON.md) 了解模型对比
            - 遇到问题请查看日志文件: `logs/`
            """)
    
    gr.Markdown("""
    ---
    💡 **提示**: 首次使用请确保已在 `.env` 文件中配置相应的API密钥
    
    📚 **文档**: [README](README.md) | [快速开始](QUICKSTART.md) | [模型对比](MODEL_COMPARISON.md)
    """)


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


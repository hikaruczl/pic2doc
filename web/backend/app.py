"""
Advanced OCR FastAPI后端
提供RESTful API接口
"""

import os
import sys
import uuid
import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yaml
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.main import AdvancedOCR

# 加载环境变量
load_dotenv()

# 创建FastAPI应用
app = FastAPI(
    title="Advanced OCR API",
    description="数学问题图像转Word文档API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化OCR系统
ocr = AdvancedOCR()

# 任务存储 (生产环境应使用数据库)
tasks = {}


class ProcessRequest(BaseModel):
    """处理请求模型"""
    llm_provider: str = "gemini"
    include_original_image: bool = True
    image_quality: int = 95


class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int
    message: str
    result: Optional[dict] = None
    created_at: str
    updated_at: str


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Advanced OCR API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "process": "/api/process",
            "batch": "/api/batch",
            "task": "/api/task/{task_id}",
            "download": "/api/download/{filename}",
            "models": "/api/models"
        }
    }


@app.get("/api/models")
async def get_models():
    """获取支持的模型列表"""
    return {
        "models": [
            {
                "id": "openai",
                "name": "OpenAI GPT-4 Vision",
                "accuracy": "95%",
                "cost": "$10-50/1K",
                "speed": "10-20s",
                "recommended": False
            },
            {
                "id": "anthropic",
                "name": "Claude 3 Sonnet",
                "accuracy": "90%",
                "cost": "$3-8/1K",
                "speed": "5-12s",
                "recommended": True
            },
            {
                "id": "gemini",
                "name": "Gemini 1.5 Flash",
                "accuracy": "88%",
                "cost": "$0.35-1.05/1K",
                "speed": "4-10s",
                "recommended": True
            },
            {
                "id": "qwen",
                "name": "Qwen-VL-Plus",
                "accuracy": "89%",
                "cost": "$1.4-2.8/1K",
                "speed": "6-12s",
                "recommended": False
            }
        ]
    }


@app.post("/api/process")
async def process_image(
    file: UploadFile = File(...),
    llm_provider: str = "gemini",
    include_original_image: bool = True,
    image_quality: int = 95,
    background_tasks: BackgroundTasks = None
):
    """
    处理单个图像
    
    Args:
        file: 上传的图像文件
        llm_provider: LLM提供商
        include_original_image: 是否包含原始图像
        image_quality: 图像质量
        
    Returns:
        任务ID和状态
    """
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 保存上传的文件
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / f"{task_id}_{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 创建任务
        task = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0,
            "message": "任务已创建",
            "result": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "file_path": str(file_path),
            "config": {
                "llm_provider": llm_provider,
                "include_original_image": include_original_image,
                "image_quality": image_quality
            }
        }
        
        tasks[task_id] = task
        
        # 在后台处理
        if background_tasks:
            background_tasks.add_task(process_task, task_id)
        else:
            # 同步处理 (用于测试)
            await process_task(task_id)
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "任务已提交,正在处理中"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def process_task(task_id: str):
    """
    后台处理任务
    
    Args:
        task_id: 任务ID
    """
    task = tasks.get(task_id)
    if not task:
        return
    
    try:
        # 更新状态
        task["status"] = "processing"
        task["progress"] = 10
        task["message"] = "正在处理图像..."
        task["updated_at"] = datetime.now().isoformat()
        
        # 更新OCR配置
        config = task["config"]
        ocr.config['llm']['primary_provider'] = config['llm_provider']
        ocr.config['document']['include_original_image'] = config['include_original_image']
        ocr.config['image']['quality'] = config['image_quality']
        
        # 重新初始化LLM客户端
        from src.llm_client import LLMClient
        ocr.llm_client = LLMClient(ocr.config, ocr.image_processor)
        
        task["progress"] = 30
        task["message"] = "正在调用LLM分析..."
        
        # 处理图像
        result = ocr.process_image(task["file_path"])
        
        if result['success']:
            task["status"] = "completed"
            task["progress"] = 100
            task["message"] = "处理完成"
            task["result"] = {
                "output_path": result['output_path'],
                "statistics": result['statistics'],
                "provider": result['analysis']['provider'],
                "model": result['analysis']['model']
            }
        else:
            task["status"] = "failed"
            task["progress"] = 0
            task["message"] = f"处理失败: {result['error']}"
        
        task["updated_at"] = datetime.now().isoformat()
        
    except Exception as e:
        task["status"] = "failed"
        task["progress"] = 0
        task["message"] = f"处理出错: {str(e)}"
        task["updated_at"] = datetime.now().isoformat()


@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态信息
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "task_id": task["task_id"],
        "status": task["status"],
        "progress": task["progress"],
        "message": task["message"],
        "result": task.get("result"),
        "created_at": task["created_at"],
        "updated_at": task["updated_at"]
    }


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """
    下载生成的文件
    
    Args:
        filename: 文件名
        
    Returns:
        文件下载响应
    """
    file_path = Path("output") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@app.post("/api/batch")
async def batch_process(
    files: List[UploadFile] = File(...),
    llm_provider: str = "gemini"
):
    """
    批量处理多个图像
    
    Args:
        files: 上传的文件列表
        llm_provider: LLM提供商
        
    Returns:
        批处理任务ID
    """
    try:
        # 生成批处理任务ID
        batch_id = str(uuid.uuid4())
        
        # 保存所有文件并创建子任务
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        sub_task_ids = []
        
        for file in files:
            task_id = str(uuid.uuid4())
            file_path = upload_dir / f"{task_id}_{file.filename}"
            
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # 创建子任务
            task = {
                "task_id": task_id,
                "status": "pending",
                "progress": 0,
                "message": "等待处理",
                "result": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "file_path": str(file_path),
                "config": {
                    "llm_provider": llm_provider,
                    "include_original_image": True,
                    "image_quality": 95
                }
            }
            
            tasks[task_id] = task
            sub_task_ids.append(task_id)
        
        # 创建批处理任务
        batch_task = {
            "batch_id": batch_id,
            "sub_tasks": sub_task_ids,
            "total": len(sub_task_ids),
            "completed": 0,
            "failed": 0,
            "created_at": datetime.now().isoformat()
        }
        
        tasks[f"batch_{batch_id}"] = batch_task
        
        # 异步处理所有子任务
        for task_id in sub_task_ids:
            asyncio.create_task(process_task(task_id))
        
        return {
            "batch_id": batch_id,
            "total_tasks": len(sub_task_ids),
            "message": "批处理任务已提交"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """
    获取批处理状态
    
    Args:
        batch_id: 批处理ID
        
    Returns:
        批处理状态信息
    """
    batch_task = tasks.get(f"batch_{batch_id}")
    if not batch_task:
        raise HTTPException(status_code=404, detail="批处理任务不存在")
    
    # 统计子任务状态
    completed = 0
    failed = 0
    processing = 0
    
    for task_id in batch_task["sub_tasks"]:
        task = tasks.get(task_id)
        if task:
            if task["status"] == "completed":
                completed += 1
            elif task["status"] == "failed":
                failed += 1
            elif task["status"] == "processing":
                processing += 1
    
    return {
        "batch_id": batch_id,
        "total": batch_task["total"],
        "completed": completed,
        "failed": failed,
        "processing": processing,
        "pending": batch_task["total"] - completed - failed - processing,
        "created_at": batch_task["created_at"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)


"""
Advanced OCR FastAPI后端
提供RESTful API接口
"""

import os
import sys
import uuid
import asyncio
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Response,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.main import AdvancedOCR
from web.backend.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    compute_expires_in,
    create_access_token,
    decode_access_token,
    get_user,
    get_user_by_phone_number,
    normalize_phone_number,
    register_user_with_phone,
    reset_password_with_phone,
    send_phone_verification_code,
    should_refresh_token,
    validate_phone_number,
    verify_phone_code,
    PHONE_PURPOSE_REGISTER,
    PHONE_PURPOSE_RESET,
)
from web.backend.database import init_db_pool, close_db_pool
from web.backend.redis_client import init_redis_client, close_redis_client

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

DEBUG_PHONE_CODE = os.getenv("AUTH_DEBUG_PHONE_CODE", "false").lower() in {"1", "true", "yes"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Initializing database connection pool...")
    init_db_pool()

    logger.info("Initializing Redis client...")
    init_redis_client()

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Closing database connection pool...")
    close_db_pool()

    logger.info("Closing Redis client...")
    close_redis_client()

    logger.info("Application shutdown complete")


# 创建FastAPI应用
app = FastAPI(
    title="图像转Word API",
    description="智能识别数学公式，生成Word文档",
    version="1.0.0",
    lifespan=lifespan,
)

security = HTTPBearer(auto_error=False)

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


class LoginRequest(BaseModel):
    """登录请求模型"""

    username: str
    password: str


class TokenResponse(BaseModel):
    """访问令牌响应模型"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfile(BaseModel):
    """已登录用户信息"""

    username: str
    full_name: Optional[str] = None


class PhoneCodeRequest(BaseModel):
    """手机验证码请求模型"""

    phone: str
    purpose: str = PHONE_PURPOSE_REGISTER


class PhoneCodeResponse(BaseModel):
    """验证码发送响应"""

    message: str
    ttl: int
    debug_code: Optional[str] = None


class PhoneRegisterRequest(BaseModel):
    """手机号注册请求模型"""

    phone: str
    code: str
    password: str
    username: Optional[str] = None
    full_name: Optional[str] = None


class PhoneResetRequest(BaseModel):
    """手机号找回密码请求"""

    phone: str
    code: str
    new_password: str


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


async def get_current_user(
    response: Response,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """从Bearer Token中解析当前用户。"""

    if credentials is None:
        raise HTTPException(status_code=401, detail="未提供认证凭证")

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="不支持的认证方式")

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="访问令牌无效或已过期")

    username = payload.get("sub")

    user_record = get_user(username)
    if not user_record or user_record.get("disabled"):
        raise HTTPException(status_code=401, detail="用户不可用")

    if should_refresh_token(payload.get("exp")):
        new_token, expires_at = create_access_token(username)
        response.headers["X-Access-Token"] = new_token
        response.headers["X-Token-Expires-In"] = str(compute_expires_in(expires_at))

    return username


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "图像转Word API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "login": "/api/login",
            "me": "/api/me",
            "process": "/api/process",
            "batch": "/api/batch",
            "task": "/api/task/{task_id}",
            "download": "/api/download/{filename}",
        }
    }


@app.post("/api/auth/phone/send-code", response_model=PhoneCodeResponse)
async def request_phone_code(request: PhoneCodeRequest):
    """发送手机验证码"""

    purpose = request.purpose.lower()
    if purpose not in {PHONE_PURPOSE_REGISTER, PHONE_PURPOSE_RESET}:
        raise HTTPException(status_code=400, detail="不支持的验证码用途")

    normalized_phone = normalize_phone_number(request.phone)
    if not validate_phone_number(normalized_phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")

    if purpose == PHONE_PURPOSE_REGISTER:
        if get_user_by_phone_number(normalized_phone):
            raise HTTPException(status_code=400, detail="手机号已注册")
    else:
        if not get_user_by_phone_number(normalized_phone):
            raise HTTPException(status_code=404, detail="手机号未注册")

    try:
        code, ttl = send_phone_verification_code(normalized_phone, purpose)
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    payload = {"message": "验证码已发送，如未收到请稍后重试", "ttl": ttl}
    if DEBUG_PHONE_CODE:
        payload["debug_code"] = code
    return PhoneCodeResponse(**payload)


@app.post("/api/auth/phone/register", response_model=TokenResponse)
async def register_with_phone(request: PhoneRegisterRequest):
    """使用手机号注册账号"""

    normalized_phone = normalize_phone_number(request.phone)
    if not validate_phone_number(normalized_phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")

    if get_user_by_phone_number(normalized_phone):
        raise HTTPException(status_code=400, detail="手机号已注册")

    username = request.username.strip() if request.username else normalized_phone
    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")

    if get_user(username):
        raise HTTPException(status_code=400, detail="用户名已存在")

    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度必须不少于6位")

    if not verify_phone_code(normalized_phone, PHONE_PURPOSE_REGISTER, request.code):
        raise HTTPException(status_code=400, detail="验证码无效或已过期")

    created = register_user_with_phone(
        username=username,
        password=request.password,
        phone=normalized_phone,
        full_name=request.full_name,
    )

    if not created:
        raise HTTPException(status_code=400, detail="注册失败，请稍后重试")

    access_token, expires_at = create_access_token(subject=username)
    return TokenResponse(
        access_token=access_token,
        expires_in=compute_expires_in(expires_at),
    )


@app.post("/api/auth/phone/reset-password")
async def reset_password_with_phone_endpoint(request: PhoneResetRequest):
    """通过手机验证码重置密码"""

    normalized_phone = normalize_phone_number(request.phone)
    if not validate_phone_number(normalized_phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")

    user = get_user_by_phone_number(normalized_phone)
    if not user:
        raise HTTPException(status_code=404, detail="手机号未注册")

    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度必须不少于6位")

    if not verify_phone_code(normalized_phone, PHONE_PURPOSE_RESET, request.code):
        raise HTTPException(status_code=400, detail="验证码无效或已过期")

    if not reset_password_with_phone(normalized_phone, request.new_password):
        raise HTTPException(status_code=500, detail="重置密码失败，请稍后重试")

    return {"message": "密码已重置，请使用新密码登录"}


@app.post("/api/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """用户登录并获取访问令牌"""

    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token, expires_at = create_access_token(subject=user["username"])
    return TokenResponse(
        access_token=access_token,
        expires_in=compute_expires_in(expires_at),
    )


@app.get("/api/me", response_model=UserProfile)
async def read_current_user(current_user: str = Depends(get_current_user)):
    """获取当前登录用户信息"""

    record = get_user(current_user) or {}
    return UserProfile(username=current_user, full_name=record.get("full_name"))


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
    background_tasks: BackgroundTasks = None,
    current_user: str = Depends(get_current_user),
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
            },
            "user": current_user,
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
async def get_task_status(task_id: str, current_user: str = Depends(get_current_user)):
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

    if task.get("user") != current_user:
        raise HTTPException(status_code=403, detail="无权访问该任务")

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
async def download_file(filename: str, current_user: str = Depends(get_current_user)):
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

    # Ensure the requested file belongs to the current user
    allowed = False
    for task in tasks.values():
        if isinstance(task, dict) and task.get("user") == current_user:
            result = task.get("result")
            if result:
                output_path = result.get("output_path")
                if output_path and Path(output_path).name == filename:
                    allowed = True
                    break

    if not allowed:
        raise HTTPException(status_code=403, detail="无权下载该文件")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@app.post("/api/batch")
async def batch_process(
    files: List[UploadFile] = File(...),
    llm_provider: str = "gemini",
    current_user: str = Depends(get_current_user),
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
                },
                "user": current_user,
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
            "created_at": datetime.now().isoformat(),
            "user": current_user,
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
async def get_batch_status(batch_id: str, current_user: str = Depends(get_current_user)):
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

    if batch_task.get("user") != current_user:
        raise HTTPException(status_code=403, detail="无权访问该批处理任务")
    
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

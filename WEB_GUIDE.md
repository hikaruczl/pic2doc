# Web界面使用指南

Advanced OCR提供两种Web界面方案:
1. **Gradio界面** - 快速简单,适合个人使用
2. **FastAPI + 前端** - 完整方案,适合生产部署

---

## 🚀 方案1: Gradio Web界面 (推荐快速开始)

### 特点
- ✅ 零配置,开箱即用
- ✅ 美观的现代化界面
- ✅ 支持单图像和批量处理
- ✅ 实时进度显示
- ✅ 内置帮助文档

### 安装

```bash
# 安装依赖
pip install gradio

# 或使用完整requirements
pip install -r requirements.txt
```

### 启动

```bash
# 启动Web界面
python web_app.py
```

访问: http://localhost:7860

### 使用步骤

1. **配置API密钥**
   - 确保 `.env` 文件中已配置API密钥
   - 至少配置一个LLM提供商的密钥

2. **单图像处理**
   - 点击"单图像处理"标签页
   - 上传图像文件
   - 选择LLM提供商
   - 配置选项 (可选)
   - 点击"开始处理"
   - 等待处理完成
   - 下载Word文档

3. **批量处理**
   - 点击"批量处理"标签页
   - 上传多个图像文件
   - 选择LLM提供商
   - 点击"批量处理"
   - 查看处理结果
   - 在 `output/` 目录查找生成的文档

### 配置选项

#### LLM提供商
- **Gemini** (推荐): 性价比最高
- **Anthropic**: 平衡准确率和成本
- **OpenAI**: 最高准确率
- **Qwen**: 国内用户优选

#### 其他选项
- **包含原始图像**: 是否在Word中嵌入原始图像
- **图像质量**: 70-100,影响文件大小

### 高级配置

编辑 `web_app.py` 自定义:

```python
# 修改端口
demo.launch(
    server_port=8080,  # 自定义端口
    share=True,        # 生成公网链接
    auth=("user", "pass")  # 添加认证
)
```

### 公网访问

```bash
# 生成临时公网链接
python web_app.py --share
```

---

## 🏗️ 方案2: FastAPI后端 + 前端

### 特点
- ✅ RESTful API设计
- ✅ 异步处理
- ✅ 任务队列管理
- ✅ 适合生产环境
- ✅ 易于集成

### 架构

```
┌─────────────┐      HTTP      ┌──────────────┐
│   前端      │ ◄──────────────► │  FastAPI     │
│  (可选)     │                  │   后端       │
└─────────────┘                  └──────┬───────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │  OCR Engine  │
                                 └──────────────┘
```

### 安装

```bash
cd web/backend
pip install -r requirements.txt
```

### 启动后端

```bash
# 开发模式
python app.py

# 或使用uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

API文档: http://localhost:8000/docs

### API端点

#### 1. 获取模型列表

```bash
GET /api/models
```

响应:
```json
{
  "models": [
    {
      "id": "gemini",
      "name": "Gemini 1.5 Flash",
      "accuracy": "88%",
      "cost": "$0.35-1.05/1K",
      "speed": "4-10s",
      "recommended": true
    }
  ]
}
```

#### 2. 处理单个图像

```bash
POST /api/process
Content-Type: multipart/form-data

file: <image_file>
llm_provider: gemini
include_original_image: true
image_quality: 95
```

响应:
```json
{
  "task_id": "uuid-here",
  "status": "pending",
  "message": "任务已提交"
}
```

#### 3. 查询任务状态

```bash
GET /api/task/{task_id}
```

响应:
```json
{
  "task_id": "uuid-here",
  "status": "completed",
  "progress": 100,
  "message": "处理完成",
  "result": {
    "output_path": "output/file.docx",
    "statistics": {
      "total_formulas": 10
    }
  }
}
```

#### 4. 下载文件

```bash
GET /api/download/{filename}
```

#### 5. 批量处理

```bash
POST /api/batch
Content-Type: multipart/form-data

files: [<file1>, <file2>, ...]
llm_provider: gemini
```

#### 6. 查询批处理状态

```bash
GET /api/batch/{batch_id}
```

### 使用示例

#### Python客户端

```python
import requests

# 上传图像
files = {'file': open('math.png', 'rb')}
data = {'llm_provider': 'gemini'}

response = requests.post(
    'http://localhost:8000/api/process',
    files=files,
    data=data
)

task_id = response.json()['task_id']

# 查询状态
import time
while True:
    status = requests.get(f'http://localhost:8000/api/task/{task_id}')
    result = status.json()
    
    if result['status'] == 'completed':
        print(f"完成! 文件: {result['result']['output_path']}")
        break
    elif result['status'] == 'failed':
        print(f"失败: {result['message']}")
        break
    
    time.sleep(2)

# 下载文件
filename = result['result']['output_path'].split('/')[-1]
file_response = requests.get(f'http://localhost:8000/api/download/{filename}')
with open('output.docx', 'wb') as f:
    f.write(file_response.content)
```

#### JavaScript客户端

```javascript
// 上传图像
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('llm_provider', 'gemini');

const response = await fetch('http://localhost:8000/api/process', {
    method: 'POST',
    body: formData
});

const { task_id } = await response.json();

// 轮询状态
const checkStatus = async () => {
    const statusResponse = await fetch(`http://localhost:8000/api/task/${task_id}`);
    const status = await statusResponse.json();
    
    if (status.status === 'completed') {
        console.log('完成!', status.result);
        // 下载文件
        window.location.href = `http://localhost:8000/api/download/${status.result.output_path.split('/').pop()}`;
    } else if (status.status === 'failed') {
        console.error('失败:', status.message);
    } else {
        setTimeout(checkStatus, 2000);
    }
};

checkStatus();
```

---

## 🐳 Docker部署

### Dockerfile

```dockerfile
FROM python:3.8-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p output logs uploads

# 暴露端口
EXPOSE 7860 8000

# 启动命令 (可选择Gradio或FastAPI)
CMD ["python", "web_app.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  gradio:
    build: .
    ports:
      - "7860:7860"
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
      - ./.env:/app/.env
    environment:
      - LOG_LEVEL=INFO
    command: python web_app.py
  
  fastapi:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
      - ./uploads:/app/uploads
      - ./.env:/app/.env
    environment:
      - LOG_LEVEL=INFO
    command: python web/backend/app.py
```

### 构建和运行

```bash
# 构建镜像
docker build -t advanceocr .

# 运行Gradio界面
docker run -p 7860:7860 -v $(pwd)/.env:/app/.env advanceocr

# 或使用docker-compose
docker-compose up gradio

# 运行FastAPI后端
docker-compose up fastapi
```

---

## 🚀 生产部署

### Nginx配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Gradio
    location / {
        proxy_pass http://localhost:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
    
    # FastAPI
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Systemd服务

创建 `/etc/systemd/system/advanceocr.service`:

```ini
[Unit]
Description=Advanced OCR Web Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/advanceOCR
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python web_app.py

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl enable advanceocr
sudo systemctl start advanceocr
sudo systemctl status advanceocr
```

---

## 🔒 安全建议

1. **API密钥保护**
   - 不要在前端暴露API密钥
   - 使用环境变量
   - 定期轮换密钥

2. **访问控制**
   - 添加用户认证
   - 限制上传文件大小
   - 实施速率限制

3. **HTTPS**
   - 生产环境必须使用HTTPS
   - 使用Let's Encrypt免费证书

4. **文件安全**
   - 验证上传文件类型
   - 定期清理临时文件
   - 限制文件访问权限

---

## 📊 监控和日志

### 日志查看

```bash
# Gradio日志
tail -f logs/advanceocr_*.log

# FastAPI日志
tail -f logs/fastapi.log
```

### 性能监控

使用Prometheus + Grafana监控:

```python
# 在FastAPI中添加metrics端点
from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')
```

---

## ❓ 常见问题

### Q: Gradio界面无法访问?
**A**: 检查防火墙设置,确保7860端口开放

### Q: FastAPI返回500错误?
**A**: 查看日志文件,检查API密钥配置

### Q: 处理速度慢?
**A**: 
- 使用更快的模型 (Gemini Flash, Claude Haiku)
- 启用图像压缩
- 考虑使用GPU加速

### Q: 如何添加认证?
**A**: 
```python
# Gradio
demo.launch(auth=("username", "password"))

# FastAPI
from fastapi.security import HTTPBasic
```

---

## 📚 更多资源

- [Gradio文档](https://gradio.app/docs/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [项目README](README.md)
- [API文档](API.md)

---

**更新日期:** 2024-01-XX


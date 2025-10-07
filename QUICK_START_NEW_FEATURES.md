# 新功能快速开始指南

本指南帮助你快速上手Advanced OCR的新功能。

---

## 🆕 新功能概览

### 1. 新增4个多模态LLM模型
- ✅ Google Gemini 1.5 Pro/Flash
- ✅ 阿里云通义千问 Qwen-VL Max/Plus

### 2. Web界面
- ✅ Gradio可视化界面
- ✅ FastAPI RESTful后端

---

## 🚀 5分钟快速开始

### 步骤1: 安装新依赖

```bash
# 更新依赖
pip install -r requirements.txt

# 或单独安装新依赖
pip install google-generativeai dashscope gradio fastapi uvicorn
```

### 步骤2: 配置API密钥

编辑 `.env` 文件,添加至少一个新模型的API密钥:

```env
# 推荐: Google Gemini (性价比最高)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# 或: 阿里云通义千问 (国内用户)
QWEN_API_KEY=your_qwen_api_key_here
QWEN_MODEL=qwen-vl-plus

# 设置主要提供商
PRIMARY_LLM_PROVIDER=gemini
FALLBACK_LLM_PROVIDER=qwen
```

### 步骤3: 启动Web界面

```bash
# 启动Gradio界面 (推荐)
python web_app.py
```

访问: http://localhost:7860

### 步骤4: 使用Web界面

1. 上传包含数学问题的图像
2. 选择LLM模型 (推荐Gemini)
3. 点击"开始处理"
4. 等待处理完成
5. 下载Word文档

**完成! 🎉**

---

## 💰 成本对比

### 处理1000张图像的成本

| 模型 | 成本 | 相比GPT-4节省 |
|------|------|--------------|
| GPT-4 Vision | $10-50 | - |
| Claude 3 Sonnet | $3-8 | 70-84% |
| **Gemini 1.5 Flash** | **$0.35-1.05** | **96-98%** ⭐ |
| Qwen-VL-Plus | $1.4-2.8 | 86-94% |

**推荐使用Gemini 1.5 Flash,成本最低!**

---

## 🎯 使用场景推荐

### 场景1: 日常个人使用
```env
PRIMARY_LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-flash
```
- 成本: 极低
- 准确率: 88%
- 速度: 快

### 场景2: 高质量要求
```env
PRIMARY_LLM_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-3-sonnet-20240229
FALLBACK_LLM_PROVIDER=gemini
```
- 成本: 适中
- 准确率: 90%
- 可靠性: 高

### 场景3: 国内用户
```env
PRIMARY_LLM_PROVIDER=qwen
QWEN_MODEL=qwen-vl-max
FALLBACK_LLM_PROVIDER=gemini
```
- 成本: 适中
- 准确率: 93%
- 速度: 国内快

---

## 🌐 Web界面功能

### Gradio界面特点

**单图像处理:**
- 📤 拖拽上传
- 🎛️ 模型选择
- ⚙️ 配置选项
- 📊 实时统计
- 💾 一键下载

**批量处理:**
- 📚 多文件上传
- 🔄 并行处理
- 📈 进度跟踪
- 📋 结果汇总

**帮助文档:**
- 📖 使用说明
- 💡 模型建议
- ⚠️ 注意事项

### FastAPI后端

**API端点:**
```bash
# 处理图像
POST /api/process

# 查询状态
GET /api/task/{task_id}

# 下载文件
GET /api/download/{filename}

# 批量处理
POST /api/batch
```

**使用示例:**
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
print(f"任务ID: {task_id}")
```

---

## 🔑 获取API密钥

### Google Gemini
1. 访问: https://ai.google.dev/
2. 点击 "Get API Key"
3. 创建新项目
4. 生成API密钥
5. 复制密钥到 `.env`

**免费额度:** 每分钟60次请求

### 阿里云通义千问
1. 访问: https://bailian.console.aliyun.com/
2. 开通DashScope服务
3. 创建API密钥
4. 复制密钥到 `.env`

**免费额度:** 新用户有免费额度

---

## 📊 模型选择指南

### 按成本选择

**最便宜:**
1. Gemini 1.5 Flash ($0.35/1K)
2. Claude 3 Haiku ($0.4/1K)
3. Qwen-VL-Plus ($1.4/1K)

### 按准确率选择

**最准确:**
1. GPT-4 Vision (95%)
2. Claude 3 Opus (94%)
3. Qwen-VL-Max (93%)

### 按速度选择

**最快:**
1. Claude 3 Haiku (3-8s)
2. Gemini 1.5 Flash (4-10s)
3. Claude 3 Sonnet (5-12s)

### 综合推荐

**⭐⭐⭐ 最推荐:**
- **Gemini 1.5 Flash** - 性价比之王
- **Claude 3 Sonnet** - 平衡之选

**⭐⭐ 推荐:**
- **Qwen-VL-Plus** - 国内用户
- **Gemini 1.5 Pro** - 高准确率

---

## 🐳 Docker快速部署

### 使用Docker Compose

```bash
# 启动Gradio界面
docker-compose up gradio

# 或启动FastAPI后端
docker-compose up fastapi
```

### 单独使用Docker

```bash
# 构建镜像
docker build -t advanceocr .

# 运行Gradio
docker run -p 7860:7860 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/output:/app/output \
  advanceocr

# 运行FastAPI
docker run -p 8000:8000 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/output:/app/output \
  advanceocr python web/backend/app.py
```

---

## 🔧 命令行使用 (仍然支持)

```bash
# 使用新模型
python -m src.main image.png

# 配置会自动使用 .env 中设置的模型
```

---

## ❓ 常见问题

### Q: 如何切换模型?
**A:** 在Web界面的下拉菜单选择,或修改 `.env` 中的 `PRIMARY_LLM_PROVIDER`

### Q: Gemini API密钥在哪获取?
**A:** 访问 https://ai.google.dev/ 免费获取

### Q: 哪个模型最便宜?
**A:** Gemini 1.5 Flash,成本仅为GPT-4的2%

### Q: 国内用户推荐哪个?
**A:** Qwen-VL系列,访问速度快,中文支持好

### Q: Web界面如何添加认证?
**A:** 编辑 `web_app.py`,添加:
```python
demo.launch(auth=("username", "password"))
```

### Q: 如何批量处理?
**A:** 使用Web界面的"批量处理"标签页,或使用FastAPI的 `/api/batch` 端点

---

## 📚 详细文档

- **模型对比:** [MODEL_COMPARISON.md](MODEL_COMPARISON.md)
- **Web指南:** [WEB_GUIDE.md](WEB_GUIDE.md)
- **配置说明:** [CONFIGURATION.md](CONFIGURATION.md)
- **完整文档:** [README.md](README.md)

---

## 🎉 开始使用

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置API密钥
cp .env.example .env
# 编辑 .env,添加 GEMINI_API_KEY

# 3. 启动Web界面
python web_app.py

# 4. 访问浏览器
# http://localhost:7860

# 5. 上传图像,开始处理!
```

---

**祝你使用愉快! 🚀**

有问题请查看详细文档或提交Issue。


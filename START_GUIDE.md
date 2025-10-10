# 服务启动指南

## 问题修复

原启动脚本使用了 `python -m pip`,但 uv 创建的虚拟环境默认不包含 pip。

**修复方案**: 将 `scripts/start_uv.sh` 中的 pip 命令替换为 `uv pip install`

## 快速启动

### 方式一:前台运行(带日志)
```bash
# 启动后端 (终端1)
./scripts/start_uv.sh backend

# 启动前端 (终端2)
npm --prefix web/frontend run dev -- --host 0.0.0.0 --port 5173
```
按 `Ctrl+C` 停止对应服务

### 方式二:后台运行(推荐)
```bash
# 启动所有服务
./start_services.sh

# 查看日志
tail -f logs/backend.log  # Backend API日志
tail -f logs/web.log      # Web UI日志

# 停止服务
./stop_services.sh
```

## 服务地址

- **Web UI (React)**: http://localhost:5173
- **Backend API (FastAPI)**: http://localhost:8005
- **API文档**: http://localhost:8005/docs

## 启动流程

1. **检查环境**:
   - uv 已安装
   - Python 3.11+ 可用
   - `.env` 文件已配置

2. **自动安装依赖**:
   - 脚本会自动使用 uv 安装 requirements.txt 中的所有包
   - 首次启动需要几分钟安装依赖

3. **启动服务**:
   - Backend API (FastAPI + Uvicorn)
   - Web UI (React + Vite)

## 环境变量

在 `.env` 文件中配置:

```bash
# LLM API Keys
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GEMINI_API_KEY=your_key
QWEN_API_KEY=your_key

# 主要和备用LLM提供商
PRIMARY_LLM_PROVIDER=gemini
FALLBACK_LLM_PROVIDER=qwen

# UV设置(可选)
export UV_LINK_MODE=copy  # 避免硬链接警告

# 手机验证码配置
PHONE_CODE_LENGTH=6
PHONE_CODE_TTL_SECONDS=300
PHONE_CODE_RESEND_SECONDS=60
AUTH_DEBUG_PHONE_CODE=false
```

## 常见问题

### 1. 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 查找并停止占用端口的进程
lsof -ti:5173 | xargs kill -9
lsof -ti:8005 | xargs kill -9
```

### 2. 依赖安装失败

**解决**:
```bash
# 删除虚拟环境重新创建
rm -rf .venv
./scripts/start_uv.sh backend
```

### 3. 硬链接警告

**警告**: `Failed to hardlink files; falling back to full copy`

**解决**:
```bash
export UV_LINK_MODE=copy
```

### 4. LLM API超时

**错误**: `Timeout of 60.0s exceeded`

**原因**: 网络问题或API不可达

**解决**:
- 检查网络连接
- 切换到备用LLM提供商
- 检查API密钥是否正确

## 日志位置

- **应用日志**: `logs/advanceocr_*.log`
- **Backend日志**: `logs/backend.log` (后台运行时)
- **Web日志**: `logs/web.log` (后台运行时)

## 监控服务状态

```bash
# 查看服务进程
ps aux | grep "web/backend/app.py"

# 测试API是否可用
curl http://localhost:8005/health  # Backend
curl -I http://localhost:5173      # React Web UI (开发模式)

# 实时查看日志
tail -f logs/advanceocr_*.log
```

## 开发模式

如果需要修改代码并实时重载:

```bash
# 只启动后端(带热重载)
uvicorn web.backend.app:app --reload --host 0.0.0.0 --port 8005

# 只启动Web界面
npm --prefix web/frontend run dev -- --host 0.0.0.0 --port 5173
```

## 生产部署

建议使用进程管理工具:

### 使用 systemd

创建 `/etc/systemd/system/advanceocr-backend.service`:
```ini
[Unit]
Description=AdvanceOCR Backend API
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/advanceOCR
Environment="PATH=/path/to/advanceOCR/.venv/bin"
ExecStart=/path/to/advanceOCR/scripts/start_uv.sh backend
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable advanceocr-backend
sudo systemctl start advanceocr-backend
```

### 使用 supervisord

配置文件 `/etc/supervisor/conf.d/advanceocr.conf`:
```ini
[program:advanceocr-backend]
command=/path/to/advanceOCR/scripts/start_uv.sh backend
directory=/path/to/advanceOCR
user=your_user
autostart=true
autorestart=true
stderr_logfile=/var/log/advanceocr-backend.err.log
stdout_logfile=/var/log/advanceocr-backend.out.log

[program:advanceocr-web]
command=/path/to/advanceOCR/scripts/start_uv.sh web
directory=/path/to/advanceOCR
user=your_user
autostart=true
autorestart=true
stderr_logfile=/var/log/advanceocr-web.err.log
stdout_logfile=/var/log/advanceocr-web.out.log
```

## 更新代码后

```bash
# 停止服务
./stop_services.sh

# 拉取最新代码
git pull

# 重新启动(会自动安装新依赖)
./start_services.sh
```

## 清理

```bash
# 停止所有服务
./stop_services.sh

# 删除虚拟环境
rm -rf .venv

# 清理日志
rm -f logs/*.log

# 清理输出文件
rm -f output/*.docx
```

# Web界面使用指南（React + FastAPI）

本指南介绍如何使用 Advanced OCR 的现代 Web 方案：**React 前端 + FastAPI 后端**。旧版 Gradio 界面已在代码库中移除，如需历史说明，请参考 `WEB_DEPRECATION_SUMMARY.md`。

---

## 🧱 架构概览

- **前端**：`web/frontend/`（React + Vite），负责上传文件、展示进度与结果
- **后端**：`web/backend/app.py`（FastAPI），提供认证、任务调度与文件下载
- **鉴权**：默认使用 `config/users.yaml` 中配置的账号密码（JWT）
- **静态资源**：处理结果保存在 `output/` 目录，日志保存在 `logs/`

---

## 🚀 快速开始

### 1. 准备依赖

```bash
# Python 依赖
pip install -r requirements.txt

# Node 依赖（首次）
npm --prefix web/frontend install
```

### 2. 启动服务

#### 一键启动
```bash
./start_services.sh
# Backend: http://localhost:8005
# Frontend: http://localhost:5173
```

#### 手动启动（可选）
```bash
# 终端 1：FastAPI 后端
uvicorn web.backend.app:app --host 0.0.0.0 --port 8005

# 终端 2：React 前端（开发模式）
npm --prefix web/frontend run dev -- --host 0.0.0.0 --port 5173
```

首选账号位于 `config/users.yaml`，默认示例：`admin / admin123`。

---

## 🖥️ 使用前端界面

1. 浏览器访问 `http://localhost:5173`
2. 可使用配置文件中的账号直接登录，或点击「手机号注册」「忘记密码」完成验证码校验后登录
3. 在「单图像」或「批量处理」模块拖拽或选择待处理图片
4. 选择 LLM 提供商与模型（遵循 `.env` 与 `config/config.yaml`）
5. 点击开始处理，实时查看进度与日志片段
6. 完成后下载生成的 Word 文档或查看历史记录

> 提示：批量任务会在后台序列化执行，可通过界面查看状态与失败原因。

---

## 🔌 API 快速参考

FastAPI 提供完整 REST API 与自动文档：`http://localhost:8005/docs`

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/auth/login` | 登录获取 JWT |
| `POST` | `/api/auth/phone/send-code` | 发送手机号验证码 (`register`/`reset`) |
| `POST` | `/api/auth/phone/register` | 使用手机号注册并自动登录 |
| `POST` | `/api/auth/phone/reset-password` | 通过手机号重置账号密码 |
| `POST` | `/api/process` | 上传单张图片并开始处理 |
| `GET` | `/api/task/{task_id}` | 查询任务状态 |
| `GET` | `/api/download/{filename}` | 下载结果文件 |
| `POST` | `/api/batch` | 批量任务创建 |
| `GET` | `/api/batch/{batch_id}` | 查看批量任务进度 |

示例：
```bash
# 登录获取 token
curl -X POST http://localhost:8005/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 提交处理（使用上一步返回的 token）
curl -X POST http://localhost:8005/api/process \
  -H "Authorization: Bearer <token>" \
  -F "file=@tests/sample_images/math.png" \
  -F "llm_provider=gemini"
```

---

## 📦 部署建议

### Docker Compose
```bash
docker-compose up fastapi
# 前端建议使用 Vercel/Netlify 或在服务器上运行 `npm run build && npm run preview`
```

### Systemd（后端示例）
```ini
[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/advanceOCR
Environment="PATH=/opt/advanceOCR/.venv/bin"
ExecStart=/opt/advanceOCR/.venv/bin/uvicorn web.backend.app:app --host 0.0.0.0 --port 8005
Restart=on-failure
```

### 生产构建前端
```bash
npm --prefix web/frontend run build
npm --prefix web/frontend run preview -- --host 0.0.0.0 --port 4173
```
> 将 `dist/` 目录部署到任意静态站点（Nginx、Cloudflare Pages 等）。

---

## 🛠️ 常见问题排查

| 问题 | 排查步骤 |
|------|-----------|
| 登录失败 | 确认 `config/users.yaml` 与服务器时间同步；查看 `logs/backend.log` |
| 上传超时 | 检查前端网络/反向代理超时时间，确保后端可访问所需 API |
| 文档空白 | 查看 `logs/advanceocr_*.log` 中的 LLM 响应与公式转换日志 |
| 批量任务阻塞 | 查看 `/api/batch/{batch_id}` 状态，核对任务队列是否卡住 |

---

## 🗂️ 目录速览

```
web/
├── backend/
│   ├── app.py            # FastAPI 主程序
│   ├── auth.py           # 认证逻辑
│   ├── database.py       # 数据库连接（可选）
│   └── redis_client.py   # Redis 客户端封装
└── frontend/
    ├── src/              # React 源代码
    ├── package.json      # 前端依赖定义
    └── vite.config.ts    # 构建配置
```

---

## 📝 备注

- `.env` 文件仍用于配置默认 LLM、日志级别等参数
- 运行 `./stop_services.sh` 可快速停止后台守护的前后端服务
- 测试脚本已整理至 `tests/regression/` 目录
- Bug 修复说明移动到 `docs/fixes/`

> 如果需要回顾旧的 Gradio 工作流，请查阅 `WEB_DEPRECATION_SUMMARY.md` 与 `WEB_MIGRATION_GUIDE.md`。

# 前端 API 配置说明

## 工作原理

前端通过以下方式自动适配不同环境：

### 开发环境
```bash
npm run dev
```
- 使用 `.env.development` 配置
- API_BASE = `http://localhost:8005`
- 直接访问本地后端

### 生产环境（Docker 部署）
```bash
npm run build
```
- 使用 `.env.production` 配置
- API_BASE = `''` (空字符串，使用相对路径)
- 通过 Nginx 反向代理访问后端

## 部署架构

```
用户浏览器
    ↓
http://your-server.com:5173/
    ↓
Nginx (前端容器)
    ├─→ /            → React 静态文件
    └─→ /api/*       → 反向代理到 backend:8000
```

**关键点：**
- 前端使用相对路径 `/api/*`
- Nginx 自动转发到后端容器
- 无需配置后端地址，自动适配！

## 配置说明

### 默认配置（推荐）

**无需任何配置！** 系统会自动：
- 开发：连接 `localhost:8005`
- 生产：使用 Nginx 代理（相对路径）

### 自定义配置

如果需要连接不同的后端服务器：

#### 方式1: 环境变量（部署时）
```bash
# 在 docker-compose 中设置
environment:
  - VITE_API_BASE=http://api.example.com
```

#### 方式2: 本地覆盖（开发时）
```bash
# 创建 .env.local
echo "VITE_API_BASE=http://192.168.1.100:8005" > web/frontend/.env.local
```

## 验证配置

### 检查前端调用的 API 地址

打开浏览器开发者工具（F12）→ Network 标签，查看请求：

**正确的生产环境：**
```
Request URL: http://your-server.com:5173/api/login
```

**错误（仍在用 localhost）：**
```
Request URL: http://localhost:8005/api/login
```

### 测试 API 连接

```bash
# 在服务器上测试
curl http://localhost:5173/api/health

# 应该返回后端健康检查信息
```

## 常见问题

### Q: 部署后前端还在调用 localhost？

**A:** 需要重新构建前端镜像：
```bash
cd docker
docker compose down frontend
docker compose build --no-cache frontend
docker compose up -d frontend
```

### Q: 如何修改后端地址？

**A:**
1. **不同域名部署**：设置环境变量 `VITE_API_BASE`
2. **同域名部署**（推荐）：使用默认配置即可

### Q: 开发时如何连接远程后端？

**A:** 创建 `.env.local`：
```bash
cd web/frontend
echo "VITE_API_BASE=http://remote-server.com:8005" > .env.local
npm run dev
```

## 端口说明

| 服务 | 容器内端口 | 宿主机端口 | 说明 |
|------|----------|----------|------|
| Frontend (Nginx) | 80 | 5173 | 前端界面 + API 代理 |
| Backend (FastAPI) | 8000 | 8005 | 后端 API |

**重要：**
- 前端访问：`http://server:5173`
- 前端会将 `/api/*` 请求转发到后端
- 无需直接访问 `:8005` 端口

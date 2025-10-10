# 一键部署指南

## 快速开始

### 前提条件
- Docker 和 Docker Compose 已安装
- 至少 2GB 可用内存
- 至少 5GB 可用磁盘空间

### 部署步骤

1. **克隆仓库**
```bash
git clone <your-repo-url>
cd advanceOCR
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置以下内容：
# - DB_PASSWORD: 数据库密码
# - AUTH_SECRET_KEY: JWT 密钥（使用随机字符串）
# - LLM API密钥（OPENAI_API_KEY, ANTHROPIC_API_KEY 等）
```

3. **一键部署**
```bash
./deploy.sh
```

如果遇到 Docker 权限问题，运行：
```bash
./fix_docker_permission.sh
```

### 访问服务

部署成功后，访问：
- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:8005
- **API 文档**: http://localhost:8005/docs

### 默认账号

- 用户名: `sys_lzm`
- 密码: `9e2d54df5cf51936bf8e76ee023373a4`（MD5）

⚠️ **重要**: 首次登录后请立即修改密码！

## 高级配置

### 分离部署（仅启动应用服务）

如果您已有独立的 PostgreSQL 和 Redis：

```bash
# 1. 配置 .env 中的数据库连接
DB_HOST=your-postgres-host
DB_PORT=5432
REDIS_HOST=your-redis-host
REDIS_PORT=6379

# 2. 仅启动应用服务
./start_app.sh
```

### 用户管理

```bash
# 创建新用户
python scripts/manage_users.py create <username> <password>

# 修改密码
python scripts/manage_users.py update-password <username> <new-password>

# 删除用户
python scripts/manage_users.py delete <username>
```

## 服务管理

### 查看日志
```bash
cd docker
docker compose logs -f
```

### 停止服务
```bash
cd docker
docker compose down
```

### 重启服务
```bash
cd docker
docker compose restart
```

### 完全清理（包括数据）
```bash
cd docker
docker compose down -v
```

## 故障排查

### 端口被占用
如需修改端口，编辑 `docker/docker-compose.components.yml`:
```yaml
services:
  frontend:
    ports:
      - "8080:80"  # 修改为其他端口
  backend:
    ports:
      - "8006:8000"  # 修改为其他端口
```

### 数据库连接失败
检查 `.env` 文件中的数据库配置，确保密码正确。

### 前端无法访问后端
检查后端服务是否正常运行：
```bash
curl http://localhost:8005/health
```

## 生产环境部署建议

1. **修改默认密码和密钥**
   - 修改 `AUTH_SECRET_KEY` 为随机强密码
   - 修改数据库密码
   - 删除或禁用默认用户

2. **配置 HTTPS**
   - 使用 Nginx 反向代理
   - 配置 SSL 证书

3. **数据备份**
   - 定期备份 PostgreSQL 数据
   - 备份 uploads 目录

4. **监控和日志**
   - 配置日志收集
   - 设置服务监控告警

## 目录结构

```
advanceOCR/
├── docker/                 # Docker 配置
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── Dockerfile.frontend
│   └── init.sql
├── web/
│   ├── backend/           # FastAPI 后端
│   └── frontend/          # React 前端
├── src/                   # OCR 核心代码
├── deploy.sh              # 一键部署脚本
├── fix_docker_permission.sh
└── .env.example           # 环境变量示例
```

## 技术支持

遇到问题请查看：
- [API 文档](./API.md)
- [配置指南](./CONFIGURATION.md)
- [启动指南](./START_GUIDE.md)

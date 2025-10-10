# 环境配置说明

## 快速配置

使用配置助手自动生成适合你环境的配置：

```bash
./setup_env.sh
```

然后根据提示选择部署场景。

## 手动配置

### 场景1: 服务器 Docker 部署（推荐）

适用于：全新服务器，使用 Docker 一键部署

```bash
# 1. 使用服务器配置模板
cp .env.server.example .env

# 2. 编辑配置（只需修改密码和 API 密钥）
vi .env
```

**关键配置：**
```bash
# 数据库配置（使用 Docker 容器）
DB_HOST=postgres          # ← 保持不变
DB_PASSWORD=修改为强密码

# Redis 配置（使用 Docker 容器）
REDIS_HOST=redis         # ← 保持不变

# 安全配置
AUTH_SECRET_KEY=生成一个随机字符串

# API 配置
AISTUDIO_API_KEY=你的API密钥
```

### 场景2: 本地开发（连接已有数据库）

适用于：本地开发，已有 PostgreSQL 和 Redis

```bash
# 1. 使用本地开发配置模板
cp .env.local.example .env

# 2. 编辑配置
vi .env
```

**关键配置：**
```bash
# 数据库配置（连接外部数据库）
DB_HOST=10.10.4.144      # ← 修改为你的数据库地址
DB_PORT=5432
DB_USER=myuser           # ← 修改为你的数据库用户
DB_PASSWORD=你的数据库密码

# Redis 配置（连接外部 Redis）
REDIS_HOST=localhost     # ← 修改为你的 Redis 地址
REDIS_PORT=6379
```

## 配置文件说明

| 文件 | 用途 | 是否提交 |
|------|------|---------|
| `.env.example` | 通用配置模板 | ✅ 提交 |
| `.env.server.example` | 服务器部署模板 | ✅ 提交 |
| `.env.local.example` | 本地开发模板 | ✅ 提交 |
| `.env` | 实际使用的配置 | ❌ 不提交 |
| `.env.local` | 本地开发配置 | ❌ 不提交 |
| `docker/.env` | Docker 专用配置 | ❌ 不提交 |

## 关键配置项详解

### 数据库配置

**DB_HOST 的配置规则：**

| 部署方式 | DB_HOST 值 | 说明 |
|---------|-----------|------|
| Docker 全套部署 | `postgres` | 使用 Docker Compose 中的 postgres 容器 |
| 连接外部数据库 | `10.10.4.144` 或域名 | 填写实际数据库地址 |
| 本地开发 | `localhost` 或 `127.0.0.1` | 连接本机数据库 |

**示例：**
```bash
# Docker 部署
DB_HOST=postgres

# 外部数据库
DB_HOST=db.example.com
DB_HOST=192.168.1.100

# 本地开发
DB_HOST=localhost
```

### Redis 配置

**REDIS_HOST 的配置规则：**

| 部署方式 | REDIS_HOST 值 |
|---------|--------------|
| Docker 全套部署 | `redis` |
| 连接外部 Redis | 实际 Redis 地址 |
| 本地开发 | `localhost` |

### 安全配置

```bash
# JWT 密钥 - 必须修改为随机字符串
AUTH_SECRET_KEY=your-super-secret-random-string-here

# 生成随机密钥的方法：
openssl rand -hex 32
# 或
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 不同场景的完整配置示例

### 示例1: 新服务器 Docker 部署

```bash
# .env
DB_HOST=postgres
DB_PORT=5432
DB_NAME=ocr_db
DB_USER=ocr_user
DB_PASSWORD=MyStr0ngP@ssw0rd!

REDIS_HOST=redis
REDIS_PORT=6379

AUTH_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

PRIMARY_LLM_PROVIDER=gemini
AISTUDIO_API_KEY=your_actual_api_key
```

部署命令：
```bash
./deploy.sh
```

### 示例2: 连接已有数据库

```bash
# .env
DB_HOST=10.10.4.144
DB_PORT=5432
DB_NAME=ocr_db
DB_USER=myuser
DB_PASSWORD=Czl8872575!

REDIS_HOST=10.10.4.144
REDIS_PORT=6379

AUTH_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

PRIMARY_LLM_PROVIDER=gemini
AISTUDIO_API_KEY=your_actual_api_key
```

部署命令：
```bash
# 只启动应用服务（不启动数据库容器）
./start_app.sh
```

## 环境变量优先级

1. `docker/.env` （最高优先级，Docker 专用）
2. `.env.local` （本地开发）
3. `.env` （默认配置）
4. Docker Compose 中的默认值（最低优先级）

## 常见问题

### Q: 本地开发和服务器部署配置不同怎么办？

**A:** 使用不同的配置文件：
- 本地：使用 `.env.local`（不提交到 Git）
- 服务器：使用 `.env`（从模板生成）

### Q: 如何在不修改代码的情况下切换数据库？

**A:** 只需修改 `.env` 中的 `DB_HOST`：
```bash
# 使用 Docker 数据库
DB_HOST=postgres

# 使用外部数据库
DB_HOST=your-database-server.com
```

### Q: 如何确保配置不被提交到 Git？

**A:** `.gitignore` 已配置忽略所有实际配置文件：
```
.env
.env.local
.env.production
docker/.env
```

## 配置检查

使用以下命令检查配置：

```bash
# 检查配置文件是否存在
ls -la .env*

# 检查数据库连接
docker exec -it ocr_backend python -c "
from web.backend.database import init_db_pool
init_db_pool()
print('数据库连接成功')
"
```

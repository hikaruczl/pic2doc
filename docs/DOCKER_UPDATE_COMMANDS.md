# Docker 更新命令说明

## 核心区别

### `docker compose restart`
- **作用**: 重启现有容器
- **不会**: 使用新构建的镜像
- **适用**: 修改环境变量、配置刷新

### `docker compose up -d`
- **作用**: 自动检测变化，停止旧容器，创建新容器
- **会**: 使用最新构建的镜像
- **适用**: 代码更新、镜像重新构建后
- **智能**: 无需手动 stop，自动替换

### `docker compose down`
- **作用**: 停止并删除所有容器
- **警告**: 会删除容器（但不删除 volumes）
- **适用**: 完全重新部署

## `up -d` 的智能行为

**不需要手动 stop！** Docker Compose 会自动：

1. 检测镜像是否变化
2. 如果镜像变了，停止旧容器
3. 创建新容器
4. 平滑切换（几乎无中断）

```bash
# ❌ 多余的操作
docker compose stop frontend    # 不需要！
docker compose build frontend
docker compose up -d frontend

# ✅ 正确且简洁
docker compose build frontend
docker compose up -d frontend   # 自动停止旧的，启动新的
```

## 常见场景

### 1. 修改了代码或 Dockerfile

```bash
# ❌ 错误
docker compose build frontend
docker compose restart frontend  # 不会使用新镜像！

# ✅ 正确
docker compose build frontend
docker compose up -d frontend    # 创建新容器
```

### 2. 仅修改了 .env 配置

```bash
# ✅ 正确（无需 build）
docker compose restart backend
```

### 3. 修改了 nginx.conf

```bash
# ✅ 正确（配置在镜像内）
docker compose build --no-cache frontend
docker compose up -d frontend
```

### 4. 修改了 docker-compose.yml

```bash
# ✅ 正确（无需 build，除非改了 build 配置）
docker compose up -d
```

## 完整更新流程

### 前端更新（代码/配置变更）

```bash
git pull origin main
cd docker

# 重新构建
docker compose build --no-cache frontend

# 创建新容器（关键！）
docker compose up -d frontend

# 验证
docker ps | grep frontend
```

### 后端更新

```bash
git pull origin main
cd docker

# 重新构建
docker compose build --no-cache backend

# 创建新容器
docker compose up -d backend

# 查看日志
docker compose logs -f backend
```

### 仅更新环境变量

```bash
# 编辑 .env
vi ../.env

# 重启即可（不需要 build）
docker compose restart backend
```

## 快速参考

| 修改内容 | 是否 build | 命令 |
|---------|-----------|------|
| 前端代码 | ✅ | `build` → `up -d` |
| 后端代码 | ✅ | `build` → `up -d` |
| nginx.conf | ✅ | `build` → `up -d` |
| Dockerfile | ✅ | `build` → `up -d` |
| .env 文件 | ❌ | `restart` |
| docker-compose.yml | ❌ | `up -d` |

## 验证更新是否生效

### 检查容器创建时间

```bash
docker ps --format "table {{.Names}}\t{{.CreatedAt}}\t{{.Status}}"
```

如果使用了 `up -d`，会看到新的创建时间。

### 检查镜像使用

```bash
docker images | grep ocr
```

查看镜像的创建时间是否是最新的。

### 验证配置

```bash
# Nginx 配置
docker exec ocr_frontend nginx -T | grep client_max_body_size

# 环境变量
docker exec ocr_backend env | grep MAX_IMAGE_SIZE_MB
```

## 常见错误

### ❌ 错误1: build 后用 restart

```bash
docker compose build frontend
docker compose restart frontend  # 仍在用旧镜像！
```

**后果**: 代码没更新，配置没生效

**正确**:
```bash
docker compose build frontend
docker compose up -d frontend
```

### ❌ 错误2: 不必要的 build

```bash
# 只改了 .env
docker compose build backend      # 浪费时间
docker compose up -d backend
```

**正确**:
```bash
# 只改了 .env
docker compose restart backend    # 快速重启即可
```

## 记忆口诀

> **Build 必 Up，Env 可 Restart**
>
> - 构建了镜像 → 必须 `up -d`
> - 只改环境变量 → 可以 `restart`

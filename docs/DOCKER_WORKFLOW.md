# Docker Compose 命令执行流程详解

## `docker compose up -d` 的完整流程

### 执行时会发生什么

```bash
docker compose up -d frontend
```

Docker Compose 会按以下顺序执行：

1. **读取配置** - 读取 `docker-compose.yml`
2. **检查镜像** - 比对容器使用的镜像 ID 和最新镜像 ID
3. **检测变化** - 如果镜像不同：
   - 停止旧容器（graceful stop，默认 10 秒超时）
   - 删除旧容器
   - 创建新容器
   - 启动新容器
4. **如果没变化** - 什么都不做，直接退出

### 实际演示

```bash
# 初始状态
$ docker ps
CONTAINER ID   IMAGE              STATUS         NAMES
abc123         ocr_frontend:old   Up 5 minutes   ocr_frontend

# 重新构建
$ docker compose build frontend
Successfully built xyz789

# 启动（自动替换）
$ docker compose up -d frontend
Recreating ocr_frontend ... done

# 新状态
$ docker ps
CONTAINER ID   IMAGE              STATUS         NAMES
xyz789         ocr_frontend:new   Up 2 seconds   ocr_frontend
```

## 不同命令的行为对比

### 场景：镜像已更新

| 命令 | 是否检测镜像变化 | 是否停止旧容器 | 是否创建新容器 | 是否使用新镜像 |
|------|-----------------|---------------|---------------|---------------|
| `restart` | ❌ | ✅ (重启) | ❌ | ❌ |
| `up -d` | ✅ | ✅ (替换) | ✅ | ✅ |
| `stop` + `up -d` | ✅ | ✅ | ✅ | ✅ |

### 结论

`up -d` 和 `stop` + `up -d` 效果相同，但 `up -d` 更简洁。

## 完整命令对比表

| 命令 | 作用 | 何时使用 | 是否需要先 stop |
|------|------|---------|----------------|
| `up -d` | 创建/重新创建容器 | 镜像更新、配置变更 | ❌ 不需要 |
| `restart` | 重启现有容器 | .env 变更 | ❌ 不需要 |
| `stop` | 停止容器 | 维护、调试 | - |
| `start` | 启动已停止容器 | 恢复服务 | - |
| `down` | 停止并删除容器 | 完全清理 | - |

## 常见疑问解答

### Q1: `up -d` 会中断服务吗？

**A**: 会有短暂中断（通常 1-3 秒），流程：
1. 旧容器停止（graceful shutdown）
2. 新容器启动
3. 健康检查通过后接收流量

对于零停机部署，需要：
- 使用负载均衡
- 或使用滚动更新策略

### Q2: 为什么不用 `stop` + `rm` + `up`？

**A**: `up -d` 内部已经做了这些：
```bash
# 手动方式（繁琐）
docker compose stop frontend
docker compose rm -f frontend
docker compose up -d frontend

# 自动方式（推荐）
docker compose up -d frontend  # 自动完成上述所有步骤
```

### Q3: `up -d` 会删除数据吗？

**A**: **不会！**
- ✅ Volume 数据保留
- ✅ 挂载的目录保留
- ❌ 容器内非持久化数据会丢失

示例：
```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data  # ✅ 保留
  - ./uploads:/app/uploads                  # ✅ 保留
# 容器内 /tmp 的数据                         # ❌ 丢失
```

### Q4: 什么时候必须用 `down`？

**A**: 只在以下情况：
- 修改了 `docker-compose.yml` 的网络配置
- 需要完全清理重新开始
- 调试网络问题

```bash
# 完全重建
docker compose down
docker compose up -d
```

## 最佳实践

### ✅ 推荐的更新流程

```bash
# 1. 拉取代码
git pull

# 2. 构建新镜像
docker compose build --no-cache service_name

# 3. 应用更新（自动替换）
docker compose up -d service_name

# 4. 查看日志确认
docker compose logs -f service_name
```

### ⚠️ 避免的做法

```bash
# ❌ 不必要的 stop
docker compose stop frontend
docker compose up -d frontend

# ❌ 不必要的 down（会删除所有容器）
docker compose down
docker compose up -d frontend

# ❌ 手动删除容器
docker rm -f ocr_frontend
docker compose up -d frontend
```

## 快速参考

### 日常更新（代码变更）
```bash
docker compose build service
docker compose up -d service  # 自动替换，无需 stop
```

### 环境变量变更
```bash
docker compose restart service  # 快速重启，无需 build
```

### 配置文件变更（docker-compose.yml）
```bash
docker compose up -d  # 重新读取配置，自动更新
```

### 完全重建
```bash
docker compose down -v  # 删除容器和 volumes
docker compose up -d    # 全新部署
```

## 记忆要点

> **`up -d` 是智能命令**
> - ✅ 自动检测变化
> - ✅ 自动停止旧容器
> - ✅ 自动创建新容器
> - ✅ 无需手动 stop
> - ✅ 保留 volumes 数据

> **简单记忆：`up -d` 包办一切！**

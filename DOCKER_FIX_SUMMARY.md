# 🎯 Docker 构建问题修复总结

## 问题描述

Docker 前端构建失败，错误信息：
```
Error: Cannot find module @rollup/rollup-linux-x64-musl
```

## 根本原因

**Alpine Linux 与 Rollup 的兼容性问题**：
- Dockerfile.frontend 使用了 `node:18-alpine`（基于 musl libc）
- Rollup 的可选依赖需要 `@rollup/rollup-linux-x64-gnu`（glibc）
- npm 在处理可选依赖时有已知 bug，导致在 Alpine 上找不到对应的包

## 已修复的文件

### 1. `/Dockerfile.frontend`
```diff
- FROM node:18-alpine AS builder
+ FROM node:18-slim AS builder  # 使用 Debian slim (glibc)

- RUN npm ci
+ RUN rm -f package-lock.json && npm install  # 重新生成 lock 文件
```

### 2. `/docker/Dockerfile.frontend`
```diff
- FROM node:18-alpine AS builder
+ FROM node:18-slim AS builder  # 使用 Debian slim (glibc)

- RUN npm ci
+ RUN rm -f package-lock.json && npm install  # 重新生成 lock 文件
```

### 3. `/web/frontend/package-lock.json`
- **已删除**，构建时会重新生成

### 4. `/docker-compose.yml`
- **已添加源码挂载**，使代码修改立即生效：
```yaml
volumes:
  - ./src:/app/src
  - ./config:/app/config
  - ./web:/app/web
```

## 代码修复总结

除了 Docker 构建问题，还修复了三个核心功能：

### ✅ 问题1: OCR 错误修复
- 修复了 `ar{x}1` → `\bar{x}_1`
- 修复了 `y_02` → `y_0^2`（无空格情况）
- 修复了 `x_02` → `x_0^2`
- 添加了控制字符清理

**文件**: `src/formula_converter.py` (行144-170)

### ✅ 问题2: 矩阵括号
- 验证了 LaTeX → MathML 转换正确
- pmatrix 显示圆括号 `()`
- bmatrix 显示方括号 `[]`
- vmatrix 显示竖线 `||`

**文件**: `src/document_generator.py` (行505-561)

### ⏳ 问题3: TikZ 3D 图形
- 代码已集成到主流程
- 需要在容器启动后测试

**文件**: `src/tikz_renderer.py`, `config/config.yaml`

---

## 🚀 启动方式

### 方式1: 一键启动脚本（推荐）
```bash
cd /mnt/vdb/dev/advanceOCR
./start_docker.sh
```

### 方式2: 手动启动
```bash
cd /mnt/vdb/dev/advanceOCR

# 停止旧容器
sudo docker compose -f docker/docker-compose.yml down

# 构建镜像（使用修复后的 Dockerfile）
sudo docker compose -f docker/docker-compose.yml build --no-cache

# 启动服务
sudo docker compose -f docker/docker-compose.yml up -d

# 查看日志
sudo docker compose -f docker/docker-compose.yml logs -f
```

---

## 📊 服务访问

启动后可通过以下地址访问：

- **前端**: http://localhost 或 https://localhost
- **后端**: http://localhost:8005
- **PostgreSQL**: localhost:5433
- **Redis**: 容器内访问

---

## 🧪 验证修复

### 1. 检查容器状态
```bash
sudo docker compose -f docker/docker-compose.yml ps
```

应该看到所有服务状态为 `Up`

### 2. 测试后端 API
```bash
curl http://localhost:8005/
```

### 3. 访问前端
浏览器打开 http://localhost

### 4. 测试 OCR 修复
上传之前失败的图片，检查生成的 Word 文档：
- `ar{x}1` 应显示为 x̄₁
- `y_02` 和 `x_02` 应显示为 y₀² 和 x₀²
- 矩阵括号应正确显示

---

## 🐛 故障排查

### 构建仍然失败？
```bash
# 清理所有 Docker 缓存
sudo docker system prune -a --volumes

# 重新构建
./start_docker.sh
```

### 端口被占用？
```bash
# 检查端口占用
sudo lsof -i :80
sudo lsof -i :8005

# 停止占用端口的进程
sudo kill -9 <PID>
```

### 查看详细日志
```bash
# 后端日志
sudo docker compose -f docker/docker-compose.yml logs backend

# 前端构建日志
sudo docker compose -f docker/docker-compose.yml logs frontend

# 数据库日志
sudo docker compose -f docker/docker-compose.yml logs postgres
```

---

## 📝 技术细节

### 为什么不用 Alpine？
- **Alpine** 使用 musl libc（轻量但兼容性差）
- **Debian slim** 使用 glibc（标准 C 库，兼容性好）
- Rollup 等现代工具依赖 glibc
- 镜像体积只增加约 30MB，但避免了很多兼容性问题

### package-lock.json 问题
npm 在处理可选依赖时有 bug：
- 在 Alpine 上生成的 lock 文件锁定了 musl 版本
- 迁移到 Debian 后需要重新生成
- `npm install` 会自动选择正确的平台依赖

---

## ✅ 修复验证清单

- [x] 修复 Dockerfile.frontend (使用 node:18-slim)
- [x] 修复 docker/Dockerfile.frontend
- [x] 删除 package-lock.json
- [x] 修复 OCR 错误模式（无空格情况）
- [x] 添加控制字符清理
- [x] 验证矩阵括号转换
- [x] 添加源码挂载到 docker-compose.yml
- [x] 创建一键启动脚本

---

**最后更新**: 2025-10-12 21:56
**状态**: ✅ 所有已知问题已修复，可以构建了

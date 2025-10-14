# 🔧 Docker 导入错误修复 - 快速参考

## ✅ 已修复

**文件**: `src/document_generator.py:21`

**修改**:
```python
# 之前（错误）
from tikz_renderer import TikZRenderer

# 之后（正确）
from .tikz_renderer import TikZRenderer
```

## 🚀 立即重启服务

### 选项1：使用快速重启脚本（推荐）

```bash
cd /mnt/vdb/dev/advanceOCR
./restart_docker.sh
```

这个脚本会：
- 自动检测是否需要sudo
- 停止现有服务
- 重新构建镜像
- 启动服务
- 显示状态
- 可选查看日志

### 选项2：手动重启

```bash
cd /mnt/vdb/dev/advanceOCR

# 停止
sudo docker compose down

# 重新构建并启动
sudo docker compose up -d --build

# 查看日志
sudo docker compose logs -f
```

### 选项3：仅重启容器（如果已经构建过）

```bash
sudo docker restart advanceocr-fastapi

# 查看日志
sudo docker logs -f advanceocr-fastapi
```

## ✔️ 验证修复

### 1. 检查容器状态

```bash
sudo docker compose ps
```

应该显示：
```
NAME                   STATUS
advanceocr-fastapi    Up X seconds
```

### 2. 检查日志

```bash
sudo docker compose logs --tail=50
```

应该看到：
```
INFO:     Uvicorn running on http://0.0.0.0:8005
```

**不应该**看到：
```
ModuleNotFoundError: No module named 'tikz_renderer'
```

### 3. 测试API

```bash
curl http://localhost:8005/health
# 或
curl http://localhost:8005/
```

## 🐛 如果还有问题

### 问题1：权限被拒绝

```bash
# 添加用户到docker组
sudo usermod -aG docker $USER

# 重新登录或运行
newgrp docker
```

### 问题2：容器无法启动

```bash
# 查看详细日志
sudo docker compose logs

# 进入容器检查
sudo docker compose exec fastapi bash
ls -la /app/src/tikz_renderer.py
python -c "from src.tikz_renderer import TikZRenderer; print('OK')"
```

### 问题3：端口被占用

```bash
# 检查端口8005
sudo netstat -tlnp | grep 8005

# 或使用lsof
sudo lsof -i :8005

# 停止占用端口的进程
sudo kill <PID>
```

### 问题4：需要完全重建

```bash
# 停止并删除所有
sudo docker compose down -v

# 清理镜像（可选）
sudo docker system prune -a

# 重新构建
sudo docker compose build --no-cache
sudo docker compose up -d
```

## 📋 相关文件

- ✅ `src/document_generator.py` - 已修复
- ✅ `src/tikz_renderer.py` - TikZ渲染器
- ✅ `config/config.yaml` - 配置（含TikZ设置）
- 🆕 `restart_docker.sh` - 快速重启脚本
- 📖 `docs/fixes/docker_import_fix.md` - 详细说明

## 🎯 快速命令参考

```bash
# 重启
./restart_docker.sh

# 查看状态
sudo docker compose ps

# 查看日志
sudo docker compose logs -f

# 进入容器
sudo docker compose exec fastapi bash

# 停止服务
sudo docker compose down

# 启动服务
sudo docker compose up -d
```

## 📞 需要帮助？

1. 查看详细文档：`docs/fixes/docker_import_fix.md`
2. 查看TikZ集成文档：`docs/TIKZ_GUIDE.md`
3. 检查应用日志：`logs/advanceocr_*.log`

---

**修复时间**: 2025-10-12
**状态**: ✅ 就绪，等待重启
**预计恢复时间**: < 2分钟

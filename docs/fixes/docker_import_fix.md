# 修复 Docker 导入错误

## 问题描述
```
ModuleNotFoundError: No module named 'tikz_renderer'
```

## 原因
`document_generator.py` 中使用了绝对导入而不是相对导入。

## 已修复
✅ 已将 `from tikz_renderer import TikZRenderer` 改为 `from .tikz_renderer import TikZRenderer`

## 重启 Docker 服务

### 方法 1：使用 Docker Compose（推荐）

```bash
# 进入项目目录
cd /mnt/vdb/dev/advanceOCR

# 停止服务
sudo docker compose down

# 重新构建并启动
sudo docker compose up -d --build

# 查看日志
sudo docker compose logs -f
```

### 方法 2：使用脚本

```bash
cd /mnt/vdb/dev/advanceOCR

# 停止服务
sudo ./stop_services.sh

# 启动服务
sudo ./start_services.sh

# 或使用 start_app.sh（如果存在）
sudo ./start_app.sh
```

### 方法 3：手动重启容器

```bash
# 查看运行中的容器
sudo docker ps

# 停止特定容器
sudo docker stop <container_id_or_name>

# 重新启动
sudo docker start <container_id_or_name>

# 或者重启
sudo docker restart <container_id_or_name>
```

## 验证修复

启动后，检查日志是否有错误：

```bash
# 查看最近的日志
sudo docker compose logs --tail=100

# 实时查看日志
sudo docker compose logs -f
```

如果看到服务正常启动（例如：`Uvicorn running on...`），则修复成功。

## 测试导入

在本地也可以测试导入是否正常：

```bash
cd /mnt/vdb/dev/advanceOCR
source .venv/bin/activate
python -c "from src.document_generator import DocumentGenerator; print('✅ Import successful')"
```

## 如果仍有问题

1. **检查 tikz_renderer.py 是否存在**：
   ```bash
   ls -la src/tikz_renderer.py
   ```

2. **检查 Docker 构建日志**：
   ```bash
   sudo docker compose build --no-cache
   ```

3. **进入容器检查**：
   ```bash
   sudo docker compose exec <service_name> bash
   ls -la /app/src/
   python -c "from src.tikz_renderer import TikZRenderer"
   ```

## 相关文件

- `src/document_generator.py` - 已修复导入
- `src/tikz_renderer.py` - TikZ渲染器
- `config/config.yaml` - 配置文件

---

**修复时间**: 2025-10-12
**状态**: ✅ 已修复，等待重启验证

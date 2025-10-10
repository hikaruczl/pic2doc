# 文件上传大小配置

## 问题：413 Request Entity Too Large

这是因为上传的文件超过了 Nginx 默认限制（1MB）。

## 已配置的限制

### Nginx 限制：100MB
```nginx
# docker/nginx.conf
client_max_body_size 100M;
client_body_buffer_size 10M;
```

### 后端应用限制：50MB（默认）
```bash
# .env
MAX_IMAGE_SIZE_MB=50
```

### API 超时配置
```nginx
proxy_connect_timeout 300s;  # 连接超时
proxy_send_timeout 300s;     # 发送超时
proxy_read_timeout 300s;     # 读取超时
```

## 修改上传限制

### 方法1: 修改环境变量（推荐）

编辑 `.env` 文件：
```bash
# 允许上传最大 100MB 的文件
MAX_IMAGE_SIZE_MB=100
```

### 方法2: 修改 Nginx 配置

如果需要更大的限制，编辑 `docker/nginx.conf`：
```nginx
client_max_body_size 200M;  # 修改为 200MB
```

然后重启服务：
```bash
cd docker
docker compose build frontend
docker compose up -d frontend  # 注意：必须用 up -d，不是 restart
```

## 当前配置说明

| 组件 | 限制 | 说明 |
|------|------|------|
| Nginx (全局) | 100MB | 总体请求大小限制 |
| Nginx (/api/) | 100MB | API 路由限制 |
| 应用层 | 50MB | 单个图片文件大小 |
| 超时时间 | 300秒 | 处理大文件的超时 |

## 推荐配置

### 小型部署（个人使用）
- Nginx: 50MB
- 应用: 20MB

### 中型部署（团队使用）
- Nginx: 100MB
- 应用: 50MB

### 大型部署（生产环境）
- Nginx: 200MB
- 应用: 100MB

## 验证配置

### 测试上传限制
```bash
# 创建一个大文件测试
dd if=/dev/zero of=test.jpg bs=1M count=60

# 上传测试（应该成功）
curl -X POST http://localhost:5173/api/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.jpg" \
  -F "llm_provider=gemini"
```

### 查看 Nginx 错误日志
```bash
docker logs ocr_frontend 2>&1 | grep "413\|client_max_body_size"
```

## 故障排查

### 1. 仍然报 413 错误

**检查 Nginx 配置是否生效：**
```bash
docker exec ocr_frontend nginx -T | grep client_max_body_size
```

应该看到：
```
client_max_body_size 100M;
```

### 2. 重新构建前端容器

如果修改了 `nginx.conf`，需要重建：
```bash
cd docker
docker compose build --no-cache frontend
docker compose up -d frontend
```

### 3. 检查应用层限制

查看后端日志：
```bash
docker logs ocr_backend | grep -i "size\|limit"
```

## 注意事项

⚠️ **重要：**
1. Nginx 限制应该 ≥ 应用层限制
2. 修改后需要重启相应容器
3. 批量上传时总大小不能超过限制
4. 超时时间应该根据文件大小适当调整

**推荐配置：**
```
Nginx限制 = 应用限制 × 2
```

这样可以为批量上传留出余地。

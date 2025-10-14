#!/bin/bash

# Advanced OCR Docker 启动脚本
# 修复了 Alpine/Rollup 兼容性问题

set -e  # 遇到错误立即退出

echo "=========================================="
echo "Advanced OCR - Docker 启动脚本"
echo "=========================================="
echo ""

# 切换到项目根目录
cd "$(dirname "$0")"

# 停止旧容器
echo "🛑 停止旧容器..."
sudo docker compose -f docker/docker-compose.yml down 2>/dev/null || true
echo ""

# 清理旧镜像（可选，注释掉可加快构建）
# echo "🗑️  清理旧镜像..."
# sudo docker rmi ocr_frontend ocr_backend 2>/dev/null || true
# echo ""

# 构建镜像
echo "🔨 构建 Docker 镜像（这需要几分钟）..."
echo "提示：已修复 rollup Alpine 兼容性问题"
sudo docker compose -f docker/docker-compose.yml build --no-cache

echo ""
echo "✅ 构建完成！"
echo ""

# 启动容器
echo "🚀 启动服务..."
sudo docker compose -f docker/docker-compose.yml up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 5

echo ""
echo "=========================================="
echo "📊 服务状态"
echo "=========================================="
sudo docker compose -f docker/docker-compose.yml ps

echo ""
echo "=========================================="
echo "✅ 启动完成！"
echo "=========================================="
echo ""
echo "🌐 访问地址："
echo "   前端: http://localhost (HTTP) 或 https://localhost (HTTPS)"
echo "   后端: http://localhost:8005"
echo ""
echo "📝 查看日志："
echo "   所有服务: sudo docker compose -f docker/docker-compose.yml logs -f"
echo "   后端:     sudo docker compose -f docker/docker-compose.yml logs -f backend"
echo "   前端:     sudo docker compose -f docker/docker-compose.yml logs -f frontend"
echo ""
echo "🛑 停止服务："
echo "   sudo docker compose -f docker/docker-compose.yml down"
echo ""

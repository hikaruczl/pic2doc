#!/bin/bash

# Advanced OCR 一键启动脚本（本地开发模式）
# 启动数据库、后端、前端服务

set -e

cd "$(dirname "$0")"

echo "=========================================="
echo "Advanced OCR - 本地开发环境启动"
echo "=========================================="
echo ""

# 1. 启动数据库和 Redis
echo "📦 启动数据库和 Redis..."
sudo docker compose -f docker/docker-compose.yml up -d postgres redis

echo "⏳ 等待数据库就绪..."
sleep 5

# 2. 启动后端
echo ""
echo "🔧 启动后端服务..."
./start_backend.sh

# 3. 启动前端
echo ""
echo "🎨 启动前端服务..."
./start_frontend.sh

echo ""
echo "=========================================="
echo "✅ 所有服务已启动"
echo "=========================================="
echo ""
echo "📊 服务状态:"
echo "   PostgreSQL: localhost:5433 (Docker)"
echo "   Redis:      容器内 (Docker)"
echo "   后端 API:   http://localhost:8005"
echo "   前端界面:   http://localhost:5173"
echo ""
echo "📝 查看日志:"
echo "   后端: tail -f logs/backend.log"
echo "   前端: tail -f logs/frontend.log"
echo "   数据库: sudo docker compose -f docker/docker-compose.yml logs postgres"
echo ""
echo "🛑 停止服务:"
echo "   pkill -f 'python.*app.py'"
echo "   pkill -f 'vite'"
echo "   sudo docker compose -f docker/docker-compose.yml stop postgres redis"
echo ""

#!/bin/bash

# Advanced OCR 本地启动脚本（连接本地数据库）
# 连接到已运行的 postgres:16 和 ocr_redis

set -e

cd "$(dirname "$0")"

echo "=========================================="
echo "Advanced OCR - 本地启动（带数据库）"
echo "=========================================="
echo ""

# 1. 检查数据库是否运行
echo "🔍 检查数据库状态..."

if ! sudo docker ps | grep -q "postgres"; then
    echo "❌ PostgreSQL 未运行"
    echo "   请先启动 PostgreSQL: sudo docker start postgres"
    exit 1
fi
echo "  ✅ PostgreSQL 运行中"

if ! sudo docker ps | grep -q "ocr_redis"; then
    echo "⚠️  Redis 未运行，尝试启动..."
    sudo docker compose -f docker/docker-compose.yml up -d redis
    sleep 2
fi
echo "  ✅ Redis 运行中"

echo ""

# 2. 停止旧进程
echo "🛑 停止旧进程..."
pkill -f "python.*web/backend/app.py" 2>/dev/null && echo "  ✅ 已停止后端" || echo "  ℹ️  后端未运行"
pkill -f "vite" 2>/dev/null && echo "  ✅ 已停止前端" || echo "  ℹ️  前端未运行"
echo ""

# 3. 启动后端（连接数据库）
echo "🔧 启动后端服务（连接数据库模式）..."

# 清除代理环境变量
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY

# 不设置 SKIP_DB_INIT，让它连接数据库
unset SKIP_DB_INIT

# 启动后端
nohup uv run python web/backend/app.py > logs/backend.log 2>&1 &
BACKEND_PID=$!

echo "  ✅ 后端已启动 (PID: $BACKEND_PID)"
sleep 3

# 检查后端是否启动成功
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "  ✅ 后端运行正常"
else
    echo "  ❌ 后端启动失败，查看日志:"
    tail -30 logs/backend.log
    exit 1
fi

echo ""

# 4. 启动前端
echo "🎨 启动前端服务..."
cd web/frontend
nohup npm run dev > ../../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../..

echo "  ✅ 前端已启动 (PID: $FRONTEND_PID)"
sleep 3

# 检查前端是否启动成功
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "  ✅ 前端运行正常"
else
    echo "  ❌ 前端启动失败，查看日志:"
    tail -20 logs/frontend.log
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 服务启动完成"
echo "=========================================="
echo ""
echo "📊 访问地址:"
echo "   前端: http://localhost:5173"
echo "   后端: http://localhost:8005"
echo ""
echo "✅ 功能完整（包括用户认证）"
echo ""
echo "📝 查看日志:"
echo "   后端: tail -f logs/backend.log"
echo "   前端: tail -f logs/frontend.log"
echo ""
echo "🛑 停止服务:"
echo "   ./stop_local.sh"
echo ""

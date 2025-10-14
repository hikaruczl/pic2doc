#!/bin/bash

# Advanced OCR 本地启动脚本（仅前后端，无需数据库）
# 适用于只测试 OCR 功能的场景

set -e

cd "$(dirname "$0")"

echo "=========================================="
echo "Advanced OCR - 本地启动（仅前后端）"
echo "=========================================="
echo ""

# 1. 停止旧进程
echo "🛑 停止旧进程..."
pkill -f "python.*web/backend/app.py" 2>/dev/null && echo "  ✅ 已停止后端" || echo "  ℹ️  后端未运行"
pkill -f "vite" 2>/dev/null && echo "  ✅ 已停止前端" || echo "  ℹ️  前端未运行"
echo ""

# 2. 启动后端（无数据库模式）
echo "🔧 启动后端服务（无数据库模式）..."

# 清除代理环境变量
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY

# 设置环境变量：跳过数据库和 Redis 初始化
export SKIP_DB_INIT=true

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
    tail -20 logs/backend.log
    exit 1
fi

echo ""

# 3. 启动前端
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
echo "⚠️  注意: 运行在无数据库模式，用户认证功能不可用"
echo "         但 OCR 核心功能正常工作"
echo ""
echo "📝 查看日志:"
echo "   后端: tail -f logs/backend.log"
echo "   前端: tail -f logs/frontend.log"
echo ""
echo "🛑 停止服务:"
echo "   pkill -f 'python.*app.py'"
echo "   pkill -f 'vite'"
echo ""

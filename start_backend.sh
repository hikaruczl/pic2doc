#!/bin/bash

# Advanced OCR Backend 启动脚本
# 清除代理环境变量（httpx 不支持 socks 代理）

cd /mnt/vdb/dev/advanceOCR

echo "🚀 启动 Advanced OCR 后端服务..."
echo ""

# 杀掉旧进程
pkill -f "python.*web/backend/app.py" 2>/dev/null && echo "✅ 已停止旧进程"

# 清除代理环境变量并启动
unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY
unset all_proxy
unset ALL_PROXY

echo "🔧 已清除代理环境变量"
echo ""

# 启动后端
nohup uv run python web/backend/app.py > logs/backend.log 2>&1 &
BACKEND_PID=$!

echo "✅ 后端已启动 (PID: $BACKEND_PID)"
echo ""

# 等待启动
sleep 3

# 检查是否成功启动
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ 后端运行中"
    echo ""
    echo "📊 访问地址:"
    echo "   http://localhost:8005"
    echo ""
    echo "📝 查看日志:"
    echo "   tail -f logs/backend.log"
else
    echo "❌ 后端启动失败，查看日志:"
    tail -20 logs/backend.log
fi

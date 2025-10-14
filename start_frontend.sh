#!/bin/bash

# Advanced OCR Frontend 启动脚本

cd /mnt/vdb/dev/advanceOCR/web/frontend

echo "🚀 启动 Advanced OCR 前端服务..."
echo ""

# 杀掉旧进程
pkill -f "vite" 2>/dev/null && echo "✅ 已停止旧进程"

# 启动前端开发服务器
nohup npm run dev > ../../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "✅ 前端已启动 (PID: $FRONTEND_PID)"
echo ""

# 等待启动
sleep 3

# 检查是否成功启动
if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ 前端运行中"
    echo ""
    echo "📊 访问地址:"
    echo "   http://localhost:5173"
    echo ""
    echo "📝 查看日志:"
    echo "   tail -f logs/frontend.log"
else
    echo "❌ 前端启动失败，查看日志:"
    tail -20 ../../logs/frontend.log
fi

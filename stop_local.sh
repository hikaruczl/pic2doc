#!/bin/bash

# 停止 Advanced OCR 本地服务

echo "🛑 停止 Advanced OCR 服务..."
echo ""

# 停止后端
if pkill -f "python.*web/backend/app.py" 2>/dev/null; then
    echo "✅ 后端已停止"
else
    echo "ℹ️  后端未运行"
fi

# 停止前端
if pkill -f "vite" 2>/dev/null; then
    echo "✅ 前端已停止"
else
    echo "ℹ️  前端未运行"
fi

echo ""
echo "✅ 服务已停止"

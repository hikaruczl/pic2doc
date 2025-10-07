#!/usr/bin/env bash
# 停止所有服务

echo "停止所有服务..."

# 停止backend
if pgrep -f "web/backend/app.py" > /dev/null; then
    pkill -f "web/backend/app.py"
    echo "✓ Backend API 已停止"
else
    echo "✗ Backend API 未运行"
fi

# 停止web
if pgrep -f "web_app.py" > /dev/null; then
    pkill -f "web_app.py"
    echo "✓ Web UI 已停止"
else
    echo "✗ Web UI 未运行"
fi

echo "所有服务已停止"

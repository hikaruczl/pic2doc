#!/usr/bin/env bash
# 停止所有服务

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_PID_FILE="$PROJECT_ROOT/logs/frontend.pid"

echo "停止所有服务..."

# 停止backend
if pgrep -f "web/backend/app.py" > /dev/null; then
    pkill -f "web/backend/app.py"
    echo "✓ Backend API 已停止"
else
    echo "✗ Backend API 未运行"
fi

# 停止React前端
FRONTEND_STOPPED=false
if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID="$(<"$FRONTEND_PID_FILE")"
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
        FRONTEND_STOPPED=true
    fi
    rm -f "$FRONTEND_PID_FILE"
fi

if pgrep -f "npm --prefix $PROJECT_ROOT/web/frontend run dev" > /dev/null; then
    pkill -f "npm --prefix $PROJECT_ROOT/web/frontend run dev"
    FRONTEND_STOPPED=true
fi

if [ "$FRONTEND_STOPPED" = true ]; then
    echo "✓ Frontend UI 已停止"
else
    echo "✗ Frontend UI 未运行"
fi

echo "所有服务已停止"

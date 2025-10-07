#!/usr/bin/env bash
# 启动所有服务(后台运行)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 设置环境变量以抑制警告
export UV_LINK_MODE=copy

# 停止已有进程
echo "停止已有服务..."
pkill -f "web/backend/app.py" 2>/dev/null || true
pkill -f "web_app.py" 2>/dev/null || true
sleep 2

# 启动后端API
echo "启动 Backend API (端口 8005)..."
nohup ./scripts/start_uv.sh backend > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

sleep 2

# 启动Web界面
echo "启动 Web UI (端口 7860)..."
nohup ./scripts/start_uv.sh web > logs/web.log 2>&1 &
WEB_PID=$!
echo "Web PID: $WEB_PID"

echo ""
echo "==================== 服务启动成功 ===================="
echo "Backend API: http://localhost:8005"
echo "Web UI:      http://localhost:7860"
echo ""
echo "查看日志:"
echo "  Backend: tail -f logs/backend.log"
echo "  Web UI:  tail -f logs/web.log"
echo ""
echo "停止服务:"
echo "  ./stop_services.sh"
echo "===================================================="

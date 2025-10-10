#!/usr/bin/env bash
# 启动所有服务(后台运行)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 设置环境变量以抑制警告
export UV_LINK_MODE=copy

mkdir -p "$PROJECT_ROOT/logs"

# 停止已有进程
echo "停止已有服务..."
pkill -f "web/backend/app.py" 2>/dev/null || true

FRONTEND_PID_FILE="$PROJECT_ROOT/logs/frontend.pid"
if [ -f "$FRONTEND_PID_FILE" ]; then
  FRONTEND_OLD_PID="$(<"$FRONTEND_PID_FILE")"
  if [ -n "$FRONTEND_OLD_PID" ] && kill -0 "$FRONTEND_OLD_PID" 2>/dev/null; then
    kill "$FRONTEND_OLD_PID" 2>/dev/null || true
  fi
  rm -f "$FRONTEND_PID_FILE"
fi

pkill -f "npm --prefix $PROJECT_ROOT/web/frontend run dev" 2>/dev/null || true
sleep 2

# 启动后端API
echo "启动 Backend API (端口 8005)..."
nohup ./scripts/start_uv.sh backend > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

sleep 2

# 启动前端 (React + Vite)
FRONTEND_DIR="$PROJECT_ROOT/web/frontend"
FRONTEND_PORT=5173
FRONTEND_LOG="$PROJECT_ROOT/logs/web.log"

if [ ! -d "$FRONTEND_DIR" ]; then
  echo "Error: Frontend directory not found at $FRONTEND_DIR" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm is required but was not found in PATH." >&2
  exit 1
fi

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "安装前端依赖 (npm install)..."
  npm --prefix "$FRONTEND_DIR" install
fi

echo "启动 Frontend UI (端口 $FRONTEND_PORT)..."
nohup npm --prefix "$FRONTEND_DIR" run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "==================== 服务启动成功 ===================="
echo "Backend API: http://localhost:8005"
echo "Frontend UI: http://localhost:$FRONTEND_PORT"
echo ""
echo "查看日志:"
echo "  Backend: tail -f logs/backend.log"
echo "  Frontend: tail -f logs/web.log"
echo ""
echo "停止服务:"
echo "  ./stop_services.sh"
echo "===================================================="

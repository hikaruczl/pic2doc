#!/usr/bin/env bash
# 启动前端与后端服务（假设数据库与缓存已运行）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="docker/docker-compose.components.yml"

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "未找到 $COMPOSE_FILE，无法启动服务" >&2
  exit 1
fi

# 检查 Docker 是否可用
if ! command -v docker >/dev/null 2>&1; then
  echo "错误: 未检测到 Docker，请先安装 Docker" >&2
  exit 1
fi

if ! docker ps >/dev/null 2>&1; then
  echo "错误: 当前用户无法访问 Docker 守护进程" >&2
  echo "请将用户加入 docker 组或使用 sudo 执行" >&2
  exit 1
fi

echo "==============================="
echo "启动 OCR 后端 / 前端服务"
echo "==============================="

if command -v docker-compose >/dev/null 2>&1; then
  docker-compose -f "$COMPOSE_FILE" up -d --no-deps backend frontend
else
  docker compose -f "$COMPOSE_FILE" up -d --no-deps backend frontend
fi

echo "服务已启动："
echo "  Backend  -> http://localhost:8005"
echo "  Frontend -> http://localhost:5173"
echo "如需停止，可执行："
echo "  docker compose -f $COMPOSE_FILE stop backend frontend"

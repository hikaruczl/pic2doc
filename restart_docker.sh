#!/usr/bin/env bash
# Docker服务快速重启脚本

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "================================"
echo "重启 AdvanceOCR Docker 服务"
echo "================================"

# 检查是否有sudo权限
if ! docker ps &> /dev/null; then
    echo "需要sudo权限来运行Docker命令"
    DOCKER_CMD="sudo docker"
    COMPOSE_CMD="sudo docker compose"
else
    DOCKER_CMD="docker"
    COMPOSE_CMD="docker compose"
fi

# 停止服务
echo ""
echo "1. 停止服务..."
$COMPOSE_CMD down

# 重新构建（使用缓存）
echo ""
echo "2. 重新构建镜像..."
$COMPOSE_CMD build

# 启动服务
echo ""
echo "3. 启动服务..."
$COMPOSE_CMD up -d

# 等待几秒让服务启动
echo ""
echo "4. 等待服务启动..."
sleep 3

# 检查状态
echo ""
echo "5. 检查服务状态..."
$COMPOSE_CMD ps

# 显示日志
echo ""
echo "================================"
echo "✅ 重启完成！"
echo "================================"
echo ""
echo "查看日志："
echo "  $COMPOSE_CMD logs -f"
echo ""
echo "查看最近100行日志："
echo "  $COMPOSE_CMD logs --tail=100"
echo ""
echo "进入容器："
echo "  $COMPOSE_CMD exec fastapi bash"
echo ""

# 询问是否查看日志
read -p "是否查看实时日志？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    $COMPOSE_CMD logs -f
fi

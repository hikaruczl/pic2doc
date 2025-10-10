#!/bin/bash
# 快速修复Docker权限问题

echo "=========================================="
echo "Docker权限快速修复"
echo "=========================================="
echo ""

# 检查是否已有Docker权限
if docker ps &> /dev/null; then
    echo "✅ 您已经有Docker权限，无需修复"
    exit 0
fi

echo "正在添加当前用户到docker组..."
sudo usermod -aG docker $USER

echo ""
echo "✅ 用户已添加到docker组"
echo ""
echo "请选择以下方式之一激活权限："
echo ""
echo "方案1: 重新登录系统（推荐）"
echo "  - 注销并重新登录"
echo "  - 或重启系统"
echo ""
echo "方案2: 在当前终端激活（临时）"
echo "  运行: newgrp docker"
echo "  然后: ./deploy.sh"
echo ""
echo "方案3: 直接使用sudo运行部署"
echo "  运行: sudo ./deploy.sh"
echo ""

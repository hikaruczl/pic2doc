#!/bin/bash
# One-click deployment script for OCR System

set -e

echo "============================================"
echo "图像转Word系统 - 一键部署脚本"
echo "============================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "错误: 未检测到Docker，请先安装Docker"
    echo "安装指南: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "错误: 未检测到Docker Compose，请先安装Docker Compose"
    echo "安装指南: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check Docker permissions
if ! docker ps &> /dev/null; then
    echo "错误: 没有Docker权限"
    echo ""
    echo "请选择以下解决方案之一："
    echo ""
    echo "方案1: 将当前用户添加到docker组（推荐）"
    echo "  sudo usermod -aG docker $USER"
    echo "  newgrp docker"
    echo "  然后重新运行: ./deploy.sh"
    echo ""
    echo "方案2: 使用sudo运行"
    echo "  sudo ./deploy.sh"
    echo ""
    exit 1
fi

# Change to script directory
cd "$(dirname "$0")"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "未找到.env文件，正在创建..."

    # 检测环境并使用相应的模板
    if [ -f ".env.server.example" ]; then
        cp .env.server.example .env
        echo "已使用服务器配置模板创建 .env"
    else
        cp .env.example .env
        echo "已使用默认配置模板创建 .env"
    fi

    echo ""
    echo "⚠️  请编辑 .env 文件并配置以下内容:"
    echo "   1. 数据库密码 (DB_PASSWORD)"
    echo "   2. JWT密钥 (AUTH_SECRET_KEY)"
    echo "   3. LLM API密钥 (OPENAI_API_KEY, ANTHROPIC_API_KEY等)"
    echo ""
    echo "提示: 如果使用外部数据库，请修改 DB_HOST"
    echo ""
    read -p "按回车键继续，或按Ctrl+C退出编辑.env文件..."
fi

echo "正在构建并启动服务..."
echo ""

# Navigate to docker directory
cd docker

# Build and start services
if command -v docker-compose &> /dev/null; then
    docker-compose up -d --build
else
    docker compose up -d --build
fi

echo ""
echo "============================================"
echo "✅ 部署完成！"
echo "============================================"
echo ""
echo "服务访问地址:"
echo "  - 前端界面: http://localhost:5173"
echo "  - 后端API:  http://localhost:8005"
echo "  - API文档:  http://localhost:8005/docs"
echo ""
echo "默认登录账号:"
echo "  用户名: admin"
echo "  密码:   admin123"
echo ""
echo "⚠️  重要提示:"
echo "  1. 请立即登录并修改默认密码！"
echo "  2. 生产环境请修改 .env 中的密钥"
echo "  3. 确保已配置LLM API密钥"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo "============================================"

#!/bin/bash
# 环境配置助手 - 自动检测和配置不同环境

set -e

echo "============================================"
echo "OCR 系统环境配置助手"
echo "============================================"
echo ""

# 检测环境
detect_environment() {
    echo "正在检测部署环境..."
    echo ""

    # 检查是否有外部数据库
    if [ -n "$DB_HOST" ] && [ "$DB_HOST" != "postgres" ]; then
        echo "检测到外部数据库配置: $DB_HOST"
        return 1  # 外部数据库
    fi

    # 检查是否在容器中
    if [ -f /.dockerenv ]; then
        echo "检测到 Docker 容器环境"
        return 0
    fi

    # 检查是否有 Docker
    if command -v docker &> /dev/null; then
        echo "检测到 Docker 环境"
        return 0
    fi

    echo "检测到本地开发环境"
    return 2
}

# 选择配置模板
select_template() {
    echo "请选择部署场景:"
    echo "  1) 服务器部署（使用 Docker，全新安装）"
    echo "  2) 本地开发（连接已有数据库）"
    echo "  3) 自定义配置"
    echo ""
    read -p "请选择 [1-3]: " choice

    case $choice in
        1)
            if [ -f ".env.server.example" ]; then
                cp .env.server.example .env
                echo "✓ 已使用服务器配置模板"
                echo ""
                echo "数据库配置: Docker 容器 (postgres)"
                echo "Redis 配置: Docker 容器 (redis)"
            else
                cp .env.example .env
                echo "✓ 已使用默认配置模板"
            fi
            ;;
        2)
            if [ -f ".env.local.example" ]; then
                cp .env.local.example .env
                echo "✓ 已使用本地开发配置模板"
                echo ""
                echo "⚠️  请手动配置以下信息:"
                echo "   - DB_HOST: 你的数据库地址"
                echo "   - DB_PASSWORD: 数据库密码"
                echo "   - REDIS_HOST: Redis 地址"
            else
                cp .env.example .env
                echo "✓ 已使用默认配置模板"
            fi
            ;;
        3)
            cp .env.example .env
            echo "✓ 已创建自定义配置"
            echo ""
            echo "请编辑 .env 文件进行自定义配置"
            ;;
        *)
            echo "无效选择，使用默认配置"
            cp .env.example .env
            ;;
    esac
}

# 主流程
main() {
    # 检查是否已有配置
    if [ -f ".env" ]; then
        echo "检测到已存在 .env 文件"
        read -p "是否重新配置? [y/N]: " reconfigure
        if [[ ! $reconfigure =~ ^[Yy]$ ]]; then
            echo "保持现有配置"
            exit 0
        fi
        echo "备份现有配置到 .env.backup"
        cp .env .env.backup
    fi

    # 选择配置模板
    select_template

    echo ""
    echo "============================================"
    echo "配置文件已创建: .env"
    echo "============================================"
    echo ""
    echo "下一步操作:"
    echo ""
    echo "1. 编辑配置文件:"
    echo "   vi .env"
    echo ""
    echo "2. 必须修改的配置项:"
    echo "   - DB_PASSWORD (数据库密码)"
    echo "   - AUTH_SECRET_KEY (JWT 密钥，使用随机字符串)"
    echo "   - API 密钥 (如 AISTUDIO_API_KEY)"
    echo ""
    echo "3. 根据实际情况修改:"
    echo "   - DB_HOST (使用 Docker 部署保持 'postgres'，否则改为实际数据库地址)"
    echo "   - REDIS_HOST (使用 Docker 部署保持 'redis'，否则改为实际 Redis 地址)"
    echo ""
    echo "4. 配置完成后运行:"
    echo "   ./deploy.sh       # Docker 一键部署"
    echo "   # 或"
    echo "   ./start_app.sh    # 仅启动应用（需要已有数据库）"
    echo ""

    read -p "是否现在编辑配置文件? [y/N]: " edit_now
    if [[ $edit_now =~ ^[Yy]$ ]]; then
        ${EDITOR:-vi} .env
    fi
}

main

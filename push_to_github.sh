#!/bin/bash
# GitHub 推送辅助脚本

echo "=================================="
echo "  GitHub 推送辅助工具"
echo "=================================="
echo ""

# 检查是否是git仓库
if [ ! -d .git ]; then
    echo "❌ 错误：当前目录不是Git仓库"
    exit 1
fi

echo "✅ Git仓库已就绪"
echo ""

# 检查是否已配置远程仓库
if git remote get-url origin > /dev/null 2>&1; then
    echo "ℹ️  已配置远程仓库："
    git remote get-url origin
    echo ""
    read -p "是否要重新配置？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "输入GitHub仓库URL: " repo_url
        git remote set-url origin "$repo_url"
        echo "✅ 远程仓库已更新"
    fi
else
    echo "📝 请输入GitHub仓库信息"
    echo ""
    echo "提示：仓库URL格式示例："
    echo "  HTTPS: https://github.com/username/advanceOCR.git"
    echo "  SSH:   git@github.com:username/advanceOCR.git"
    echo ""
    read -p "输入GitHub仓库URL: " repo_url
    
    if [ -z "$repo_url" ]; then
        echo "❌ 错误：仓库URL不能为空"
        exit 1
    fi
    
    git remote add origin "$repo_url"
    echo "✅ 远程仓库已配置"
fi

echo ""
echo "=================================="
echo "  准备推送到 GitHub"
echo "=================================="
echo ""

# 显示当前状态
echo "📊 当前状态："
echo "  分支: $(git branch --show-current)"
echo "  提交数: $(git rev-list --count HEAD)"
echo "  远程仓库: $(git remote get-url origin)"
echo ""

# 确认推送
read -p "确认推送到GitHub？(Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
    echo "❌ 已取消推送"
    exit 0
fi

echo ""
echo "🚀 开始推送..."
echo ""

# 推送到GitHub
if git push -u origin main; then
    echo ""
    echo "=================================="
    echo "  ✅ 推送成功！"
    echo "=================================="
    echo ""
    echo "你的代码已成功推送到GitHub！"
    echo ""
    echo "下一步："
    echo "  1. 访问你的GitHub仓库"
    echo "  2. 检查文件是否正确上传"
    echo "  3. 添加仓库描述和Topics标签"
    echo "  4. （可选）创建Release版本"
    echo ""
    echo "仓库地址: $(git remote get-url origin | sed 's/\.git$//')"
    echo ""
else
    echo ""
    echo "=================================="
    echo "  ❌ 推送失败"
    echo "=================================="
    echo ""
    echo "可能的原因："
    echo "  1. 认证失败 - 检查GitHub凭据或SSH密钥"
    echo "  2. 仓库不存在 - 确认已在GitHub创建仓库"
    echo "  3. 权限不足 - 检查仓库访问权限"
    echo "  4. 网络问题 - 检查网络连接"
    echo ""
    echo "解决方案："
    echo "  - 使用Personal Access Token而不是密码"
    echo "  - 或配置SSH密钥（更推荐）"
    echo ""
    echo "详细帮助请查看: GITHUB_SETUP.md"
    echo ""
    exit 1
fi

# GitHub 仓库设置指南

本指南将帮助你把 advanceOCR 项目推送到 GitHub。

## ✅ 已完成的步骤

1. ✅ 创建了 `.gitignore` 文件
2. ✅ 初始化了 Git 仓库
3. ✅ 创建了初始提交（51个文件，10332行代码）
4. ✅ 设置了默认分支为 `main`

## 📋 接下来的步骤

### 方法一：使用 GitHub 网页界面（推荐）

#### 1. 创建 GitHub 仓库

1. 访问 [GitHub](https://github.com)
2. 点击右上角的 `+` 按钮，选择 `New repository`
3. 填写仓库信息：
   - **Repository name**: `advanceOCR`（或你喜欢的名字）
   - **Description**: `Advanced OCR system with multi-LLM support and LaTeX formula rendering`
   - **Visibility**: 选择 `Public` 或 `Private`
   - ⚠️ **不要**勾选 "Initialize this repository with a README"
   - ⚠️ **不要**添加 `.gitignore` 或 `license`（我们已经有了）
4. 点击 `Create repository`

#### 2. 推送代码到 GitHub

创建仓库后，GitHub会显示推送代码的命令。在你的终端执行：

```bash
cd /mnt/vdb/dev/advanceOCR

# 添加远程仓库（替换 YOUR_USERNAME 为你的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/advanceOCR.git

# 推送代码到GitHub
git push -u origin main
```

**示例：**
```bash
# 如果你的用户名是 john
git remote add origin https://github.com/john/advanceOCR.git
git push -u origin main
```

#### 3. 输入凭据

第一次推送时，Git会要求输入GitHub凭据：
- **Username**: 你的GitHub用户名
- **Password**: 使用 Personal Access Token（不是密码）

**如何获取 Personal Access Token：**
1. GitHub设置 → Developer settings → Personal access tokens → Tokens (classic)
2. 点击 `Generate new token (classic)`
3. 勾选 `repo` 权限
4. 生成并复制token（只显示一次，请保存）

---

### 方法二：使用 GitHub CLI（如果已安装）

如果你安装了 GitHub CLI (`gh`)，可以直接执行：

```bash
cd /mnt/vdb/dev/advanceOCR

# 登录 GitHub（如果还没登录）
gh auth login

# 创建仓库并推送
gh repo create advanceOCR --public --source=. --remote=origin --push

# 或创建私有仓库
gh repo create advanceOCR --private --source=. --remote=origin --push
```

---

### 方法三：使用 SSH（推荐，更安全）

#### 1. 设置 SSH 密钥（如果还没有）

```bash
# 生成SSH密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 查看公钥
cat ~/.ssh/id_ed25519.pub
```

#### 2. 添加 SSH 密钥到 GitHub

1. 复制上面命令输出的公钥内容
2. 访问 GitHub → Settings → SSH and GPG keys → New SSH key
3. 粘贴公钥并保存

#### 3. 创建仓库并推送（使用SSH）

在GitHub网页创建仓库后：

```bash
cd /mnt/vdb/dev/advanceOCR

# 添加远程仓库（SSH方式）
git remote add origin git@github.com:YOUR_USERNAME/advanceOCR.git

# 推送代码
git push -u origin main
```

---

## 🔍 验证推送是否成功

推送成功后，访问你的GitHub仓库页面，应该能看到：
- ✅ 51个文件
- ✅ README.md 自动显示在首页
- ✅ 代码浏览器显示所有源文件
- ✅ 提交历史显示初始提交

---

## 📝 后续操作

### 更新 README.md

你可能想在 README.md 中添加GitHub相关的徽章和链接：

```markdown
# Advanced OCR System

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

[在这里添加项目描述...]
```

### 设置仓库

在GitHub仓库页面，可以设置：
- **About**: 添加描述和话题标签
- **Topics**: 添加如 `ocr`, `latex`, `llm`, `python` 等标签
- **Settings**: 配置仓库选项

### 创建 GitHub Actions（可选）

可以添加CI/CD自动化，例如：
- 自动运行测试
- 检查代码质量
- 自动部署

---

## 🚀 快速开始命令

### 创建Public仓库

```bash
cd /mnt/vdb/dev/advanceOCR

# 1. 在GitHub网页创建仓库（不要初始化）

# 2. 添加远程仓库并推送
git remote add origin https://github.com/YOUR_USERNAME/advanceOCR.git
git push -u origin main
```

### 创建Private仓库

步骤相同，只是在GitHub网页创建时选择 `Private`。

---

## ⚠️ 常见问题

### Q1: 推送时提示 "Authentication failed"

**解决方案：**
- 使用 Personal Access Token 而不是密码
- 或者使用 SSH 方式

### Q2: 推送时提示 "Repository not found"

**解决方案：**
- 检查仓库名是否正确
- 检查用户名是否正确
- 确认仓库已在GitHub创建

### Q3: 推送时提示 "Permission denied"

**解决方案：**
- 检查GitHub账号权限
- 使用正确的Personal Access Token
- 检查SSH密钥是否正确添加

### Q4: 想要更改仓库名

**解决方案：**
```bash
# 删除旧的远程仓库
git remote remove origin

# 添加新的远程仓库
git remote add origin https://github.com/YOUR_USERNAME/NEW_NAME.git

# 推送
git push -u origin main
```

---

## 📊 当前仓库统计

```
Branch: main
Commits: 1
Files: 51
Lines of code: 10,332
```

**包含的主要内容：**
- ✅ 源代码（src/）
- ✅ 配置文件（config/）
- ✅ 测试工具（tests/, test_*.py）
- ✅ 文档（*.md）
- ✅ Docker支持（Dockerfile, docker-compose.yml）
- ✅ Web界面（web/, web_app.py）
- ✅ 示例文件（sample_text.txt, example.py）

**排除的内容（.gitignore）：**
- ❌ 虚拟环境（.venv/）
- ❌ 环境变量（.env）
- ❌ 日志文件（logs/）
- ❌ 输出文档（output/*.docx）
- ❌ 缓存文件（__pycache__/）

---

## 🎯 推荐的 GitHub 仓库设置

### 描述（About）
```
Advanced OCR system with multi-LLM support (OpenAI, Anthropic, Gemini, Qwen) 
for mathematical content extraction and LaTeX formula rendering to Word documents.
```

### Topics（标签）
- `ocr`
- `latex`
- `llm`
- `python`
- `openai`
- `anthropic`
- `gemini`
- `qwen`
- `mathematics`
- `formula`
- `word-document`
- `mathml`

### Website
可以添加你的项目文档网站或演示网站（如果有）

---

## 📖 相关文档

- [README.md](README.md) - 项目总体说明
- [INSTALL.md](INSTALL.md) - 安装指南
- [QUICKSTART.md](QUICKSTART.md) - 快速开始
- [API.md](API.md) - API文档
- [CONFIGURATION.md](CONFIGURATION.md) - 配置说明

---

## ✨ 下一步

推送到GitHub后，你可以：
1. 📝 编辑README添加更多详细信息
2. 🏷️ 发布第一个版本（Release）
3. 📢 分享项目链接
4. 🤝 邀请协作者
5. ⭐ 获得Stars！

祝你的项目成功！🚀

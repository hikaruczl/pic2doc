# 安装指南

本文档提供详细的安装步骤和环境配置说明。

## 系统要求

- Python 3.8 或更高版本
- pip (Python包管理器)
- 至少 2GB 可用磁盘空间
- 稳定的网络连接 (用于API调用)

## 详细安装步骤

### 1. 安装Python

#### Windows

1. 访问 [Python官网](https://www.python.org/downloads/)
2. 下载Python 3.8+安装包
3. 运行安装程序,**勾选 "Add Python to PATH"**
4. 验证安装:
   ```cmd
   python --version
   ```

#### macOS

使用Homebrew安装:
```bash
brew install python@3.8
```

或从官网下载安装包。

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3.8 python3-pip
```

### 2. 克隆项目

```bash
git clone <repository-url>
cd advanceOCR
```

### 3. 创建虚拟环境 (推荐)

#### Windows
```cmd
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装Python依赖

```bash
pip install -r requirements.txt
```

如果遇到安装问题,可以尝试:
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 5. 安装系统依赖

#### PDF处理支持 (可选但推荐)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Windows:**
1. 下载 [poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/)
2. 解压到 `C:\Program Files\poppler`
3. 添加 `C:\Program Files\poppler\Library\bin` 到系统PATH

#### OpenCV依赖 (通常自动安装)

**Ubuntu/Debian:**
```bash
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0
```

### 6. 配置环境变量

1. 复制环境变量模板:
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件,添加API密钥:
   ```env
   OPENAI_API_KEY=sk-your-key-here
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

### 7. 创建必要的目录

```bash
mkdir -p output logs tests/sample_images
```

### 8. 验证安装

运行测试以验证安装:

```bash
# 运行单元测试
pytest tests/ -v

# 或运行示例 (需要先配置API密钥)
python example.py
```

## API密钥获取

### OpenAI API密钥

1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册/登录账号
3. 进入 [API Keys](https://platform.openai.com/api-keys)
4. 点击 "Create new secret key"
5. 复制密钥并保存到 `.env` 文件

**注意**: GPT-4 Vision需要付费账户

### Anthropic API密钥

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的API密钥
5. 复制密钥并保存到 `.env` 文件

## 常见安装问题

### 问题 1: pip安装失败

**错误**: `ERROR: Could not find a version that satisfies the requirement...`

**解决方案**:
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 问题 2: OpenCV安装失败

**错误**: `ImportError: libGL.so.1: cannot open shared object file`

**解决方案** (Linux):
```bash
sudo apt-get install libgl1-mesa-glx
```

### 问题 3: pdf2image错误

**错误**: `PDFInfoNotInstalledError: Unable to get page count`

**解决方案**: 安装poppler (见上文系统依赖部分)

### 问题 4: 权限错误

**错误**: `PermissionError: [Errno 13] Permission denied`

**解决方案**:
```bash
# 使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 然后重新安装
pip install -r requirements.txt
```

### 问题 5: SSL证书错误

**错误**: `SSL: CERTIFICATE_VERIFY_FAILED`

**解决方案**:
```bash
# macOS
/Applications/Python\ 3.x/Install\ Certificates.command

# 或使用pip选项
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

## 开发环境设置

如果你想参与开发,还需要安装开发依赖:

```bash
pip install -r requirements-dev.txt  # 如果有的话

# 或手动安装开发工具
pip install black flake8 mypy pylint
```

## Docker安装 (可选)

如果你熟悉Docker,可以使用容器化部署:

```dockerfile
# Dockerfile示例
FROM python:3.8-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要目录
RUN mkdir -p output logs

CMD ["python", "-m", "src.main"]
```

构建和运行:
```bash
docker build -t advanceocr .
docker run -v $(pwd)/output:/app/output --env-file .env advanceocr image.png
```

## 验证安装完成

运行以下命令验证所有组件正常工作:

```bash
# 检查Python版本
python --version

# 检查已安装的包
pip list

# 运行测试
pytest tests/ -v

# 检查配置
python -c "from src.main import AdvancedOCR; print('✓ 安装成功!')"
```

## 下一步

安装完成后,请阅读:
- [README.md](README.md) - 使用说明
- [example.py](example.py) - 示例代码
- [config/config.yaml](config/config.yaml) - 配置选项

## 获取帮助

如果遇到问题:
1. 查看本文档的"常见安装问题"部分
2. 查看项目的Issue页面
3. 提交新的Issue并附上详细的错误信息


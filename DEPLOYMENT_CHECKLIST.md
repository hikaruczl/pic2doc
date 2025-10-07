# 部署检查清单

使用本清单确保系统正确安装和配置。

## 📋 安装前检查

- [ ] Python 3.8+ 已安装
  ```bash
  python --version
  ```

- [ ] pip 已安装并更新
  ```bash
  pip --version
  pip install --upgrade pip
  ```

- [ ] Git 已安装 (如果从仓库克隆)
  ```bash
  git --version
  ```

## 📦 项目安装

- [ ] 克隆或下载项目
  ```bash
  git clone <repository-url>
  cd advanceOCR
  ```

- [ ] 创建虚拟环境 (推荐)
  ```bash
  python -m venv venv
  source venv/bin/activate  # Linux/macOS
  # 或
  venv\Scripts\activate  # Windows
  ```

- [ ] 安装Python依赖
  ```bash
  pip install -r requirements.txt
  ```

- [ ] 验证依赖安装
  ```bash
  pip list | grep -E "openai|anthropic|python-docx|Pillow"
  ```

## 🔧 系统依赖 (可选)

- [ ] 安装poppler (用于PDF处理)
  
  **Ubuntu/Debian:**
  ```bash
  sudo apt-get install poppler-utils
  ```
  
  **macOS:**
  ```bash
  brew install poppler
  ```
  
  **Windows:**
  - 下载并安装 poppler-windows
  - 添加到系统PATH

- [ ] 验证poppler安装
  ```bash
  pdftoppm -v
  ```

## 🔑 API配置

- [ ] 复制环境变量模板
  ```bash
  cp .env.example .env
  ```

- [ ] 获取OpenAI API密钥
  - 访问: https://platform.openai.com/api-keys
  - 创建新密钥
  - 复制密钥

- [ ] 获取Anthropic API密钥 (可选)
  - 访问: https://console.anthropic.com/
  - 创建新密钥
  - 复制密钥

- [ ] 编辑 `.env` 文件
  ```bash
  nano .env  # 或使用其他编辑器
  ```

- [ ] 设置API密钥
  ```env
  OPENAI_API_KEY=sk-your-actual-key-here
  ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
  PRIMARY_LLM_PROVIDER=openai
  ```

- [ ] 验证API密钥格式
  - OpenAI: 以 `sk-` 开头
  - Anthropic: 以 `sk-ant-` 开头

## 📁 目录结构

- [ ] 创建必要的目录
  ```bash
  mkdir -p output logs tests/sample_images
  ```

- [ ] 验证目录结构
  ```bash
  ls -la
  # 应该看到: src/, config/, tests/, output/, logs/
  ```

## ⚙️ 配置验证

- [ ] 检查配置文件存在
  ```bash
  ls config/config.yaml
  ```

- [ ] 验证YAML语法
  ```bash
  python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
  ```

- [ ] 检查环境变量加载
  ```bash
  python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key:', 'OK' if os.getenv('OPENAI_API_KEY') else 'MISSING')"
  ```

## 🧪 功能测试

- [ ] 测试导入
  ```bash
  python -c "from src.main import AdvancedOCR; print('✓ 导入成功')"
  ```

- [ ] 运行单元测试
  ```bash
  pytest tests/ -v
  ```

- [ ] 测试图像处理器
  ```bash
  pytest tests/test_image_processor.py -v
  ```

- [ ] 测试公式转换器
  ```bash
  pytest tests/test_formula_converter.py -v
  ```

## 📝 准备测试数据

- [ ] 准备测试图像
  - 在 `tests/sample_images/` 目录下放置测试图像
  - 或使用示例创建测试图像

- [ ] 验证测试图像
  ```bash
  ls tests/sample_images/
  ```

## 🚀 运行测试

- [ ] 运行示例程序
  ```bash
  python example.py
  ```

- [ ] 处理测试图像 (如果有)
  ```bash
  python -m src.main tests/sample_images/math_problem_1.png
  ```

- [ ] 检查输出
  ```bash
  ls output/
  # 应该看到生成的 .docx 文件
  ```

## 📊 性能检查

- [ ] 检查API响应时间
  - 单次调用应在 10-30 秒内完成

- [ ] 检查内存使用
  ```bash
  # 运行时监控内存
  top  # 或 htop
  ```

- [ ] 检查日志文件
  ```bash
  ls logs/
  cat logs/advanceocr_*.log
  ```

## 🔒 安全检查

- [ ] 确认 `.env` 在 `.gitignore` 中
  ```bash
  grep ".env" .gitignore
  ```

- [ ] 确认 API 密钥未暴露
  ```bash
  # 不应该在代码中看到实际的API密钥
  grep -r "sk-" src/
  ```

- [ ] 检查文件权限
  ```bash
  chmod 600 .env  # 仅所有者可读写
  ```

## 📚 文档检查

- [ ] README.md 存在且可读
- [ ] QUICKSTART.md 存在
- [ ] INSTALL.md 存在
- [ ] API.md 存在
- [ ] CONFIGURATION.md 存在

## 🎯 最终验证

- [ ] 完整流程测试
  ```bash
  # 1. 准备测试图像
  # 2. 运行处理
  python -m src.main test_image.png
  # 3. 检查输出文件
  # 4. 打开Word文档验证内容
  ```

- [ ] 错误处理测试
  ```bash
  # 测试不存在的文件
  python -m src.main nonexistent.png
  # 应该看到友好的错误消息
  ```

- [ ] 批量处理测试
  ```python
  from src.main import AdvancedOCR
  ocr = AdvancedOCR()
  results = ocr.process_batch(['img1.png', 'img2.png'])
  print(f"成功: {sum(1 for r in results if r['success'])}")
  ```

## ✅ 部署完成确认

完成以上所有检查后,系统应该:

- ✅ 能够成功导入所有模块
- ✅ 能够处理图像文件
- ✅ 能够调用LLM API
- ✅ 能够生成Word文档
- ✅ 所有测试通过
- ✅ 日志正常记录
- ✅ 错误处理正常工作

## 🐛 常见问题排查

### 问题: 导入错误

**检查:**
```bash
pip list
python -c "import sys; print(sys.path)"
```

**解决:**
```bash
pip install -r requirements.txt --force-reinstall
```

### 问题: API调用失败

**检查:**
```bash
echo $OPENAI_API_KEY  # Linux/macOS
set OPENAI_API_KEY    # Windows
```

**解决:**
- 验证API密钥正确
- 检查网络连接
- 查看日志文件

### 问题: PDF处理失败

**检查:**
```bash
which pdftoppm
pdftoppm -v
```

**解决:**
- 安装poppler
- 检查PATH设置

### 问题: 权限错误

**解决:**
```bash
chmod -R 755 .
chmod 600 .env
```

## 📞 获取帮助

如果遇到问题:

1. 查看日志文件: `logs/advanceocr_*.log`
2. 查看文档: README.md, INSTALL.md
3. 运行诊断: `python -m pytest tests/ -v`
4. 提交Issue (附上错误日志)

## 🎉 部署成功!

如果所有检查都通过,恭喜你!系统已经成功部署并可以使用了。

**下一步:**
- 阅读 [QUICKSTART.md](QUICKSTART.md) 快速上手
- 查看 [example.py](example.py) 学习使用方法
- 阅读 [API.md](API.md) 了解详细API
- 自定义 [config/config.yaml](config/config.yaml) 配置

---

**部署日期:** _____________

**部署人员:** _____________

**环境:** □ 开发 □ 测试 □ 生产

**备注:** _____________________________________________


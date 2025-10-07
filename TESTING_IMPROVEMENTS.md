# 测试改进说明

本次更新添加了完整的LLM输出日志和格式转换测试工具，大幅降低了测试和调试成本。

## 改进内容

### 1. LLM完整输出日志

**修改文件:** `src/llm_client.py`

**功能:** 所有LLM提供商（OpenAI、Anthropic、Gemini、Qwen）现在都会在日志中输出完整的响应文本。

**日志格式:**
```
================================================================================
[Provider] LLM 完整输出:
================================================================================
[完整的LLM响应文本]
================================================================================
```

**查看方式:**
- 控制台输出（如果 `console_output: true`）
- 日志文件 `logs/advanceocr_YYYYMMDD.log`

**用途:**
- 调试LLM输出格式
- 复制LLM输出用于离线测试
- 分析模型响应质量
- 优化提示词

### 2. 格式转换测试工具

**新增文件:** `test_format_conversion.py`

**功能:** 独立的测试工具，可以直接输入文本进行格式转换，无需调用LLM API。

**核心优势:**
- ✅ **零API成本** - 不调用任何付费API
- ✅ **快速迭代** - 修改代码后立即测试
- ✅ **灵活输入** - 支持文件、命令行、管道输入
- ✅ **详细日志** - 显示解析和转换的每一步
- ✅ **易于调试** - 快速定位格式问题

**使用示例:**
```bash
# 基本用法
.venv/bin/python test_format_conversion.py -f sample_text.txt

# 指定输出文件
.venv/bin/python test_format_conversion.py -f input.txt -o output.docx

# 直接输入文本
.venv/bin/python test_format_conversion.py -t "测试 \$x^2 + y^2\$"

# 从管道读取
cat llm_output.txt | .venv/bin/python test_format_conversion.py
```

### 3. 示例和文档

**新增文件:**
- `sample_text.txt` - 完整的示例输入文本，包含各种公式格式
- `TEST_FORMAT_GUIDE.md` - 详细的使用指南和最佳实践

## 典型工作流程

### 场景1: 开发新功能

1. 修改 `formula_converter.py` 或 `document_generator.py`
2. 运行测试工具验证修改:
   ```bash
   .venv/bin/python test_format_conversion.py -f sample_text.txt -o test.docx
   ```
3. 打开生成的Word文档检查效果
4. 如有问题，查看日志定位问题并重复步骤1-3

**无需调用API，几秒钟完成一次测试迭代！**

### 场景2: 调试LLM输出问题

1. 运行主程序并查看日志中的LLM完整输出
2. 发现输出格式有问题
3. 复制LLM输出到文件 `debug.txt`
4. 使用测试工具验证转换:
   ```bash
   .venv/bin/python test_format_conversion.py -f debug.txt -o debug.docx
   ```
5. 根据结果决定是修改代码还是优化提示词

### 场景3: 优化提示词

1. 修改 `config/config.yaml` 中的提示词
2. 用真实图片测试一次（调用API）
3. 从日志复制LLM输出
4. 保存到文件并用测试工具验证多次:
   ```bash
   .venv/bin/python test_format_conversion.py -f llm_v1.txt -o test_v1.docx
   .venv/bin/python test_format_conversion.py -f llm_v2.txt -o test_v2.docx
   ```
5. 对比不同版本的转换效果

## 技术细节

### 测试工具架构

```
test_format_conversion.py
    ├── 读取输入文本（文件/命令行/stdin）
    ├── 调用 FormulaConverter.parse_content()
    │   └── 解析 $...$ 和 $$...$$ 公式
    ├── 调用 FormulaConverter.format_for_word()
    │   └── 转换为Word文档格式
    └── 调用 DocumentGenerator.create_document()
        └── 生成最终的.docx文件
```

### 解析和转换流程

1. **解析阶段** (`parse_content`)
   - 识别显示公式 `$$...$$`
   - 识别行内公式 `$...$`
   - 提取普通文本
   - 转换LaTeX为MathML

2. **格式化阶段** (`format_for_word`)
   - 分段处理文本
   - 标记公式类型（inline/display）
   - 组织段落结构

3. **生成阶段** (`create_document`)
   - 创建Word文档对象
   - 插入段落和公式
   - 应用样式和格式
   - 保存.docx文件

### 日志级别

测试工具使用INFO级别日志，输出包括：
- 输入文本（完整）
- 解析结果（每个元素）
- 格式化结果（段落/公式统计）
- 生成状态（文件路径）

## 当前配置状态

根据之前的修改，当前配置：

```yaml
formula:
  preserve_latex: false  # 不显示LaTeX注释

prompts:
  system_message: |
    You are an expert in accurately transcribing mathematical content from images.
    Your task is to faithfully reproduce ALL content from the image exactly as it appears.
    # ... (简化的提示词)
```

**效果:**
- ✅ 公式正常显示（MathML格式）
- ✅ 不显示LaTeX注释行
- ✅ 保持图片原始内容和格式

## 性能对比

| 测试方法 | API调用 | 成本 | 时间 | 适用场景 |
|---------|---------|------|------|---------|
| 完整测试 | 是 | $$$ | ~10s | 端到端验证 |
| 格式测试 | 否 | $0 | ~1s | 格式调试、快速迭代 |

**结论:** 使用格式转换测试工具，可以将测试迭代速度提升10倍，成本降为0。

## 最佳实践

1. **开发阶段** - 优先使用格式转换测试工具
2. **集成测试** - 定期进行完整的端到端测试
3. **保存输出** - 将有代表性的LLM输出保存为测试用例
4. **版本对比** - 用相同的输入测试不同版本的代码

## 文件清单

### 新增文件
- `test_format_conversion.py` - 格式转换测试工具
- `sample_text.txt` - 示例输入文本
- `TEST_FORMAT_GUIDE.md` - 使用指南
- `TESTING_IMPROVEMENTS.md` - 本文档

### 修改文件
- `src/llm_client.py` - 添加完整输出日志

### 生成文件
- `output/test_sample.docx` - 测试生成的示例文档

## 常见问题

### Q: 为什么要用虚拟环境？
A: 项目依赖已安装在 `.venv` 虚拟环境中，使用 `.venv/bin/python` 确保使用正确的依赖版本。

### Q: 可以不用虚拟环境吗？
A: 可以，但需要确保系统Python已安装所有依赖（见 `requirements.txt`）。

### Q: 测试工具支持哪些Python版本？
A: Python 3.6+ 都支持，项目使用Python 3.12测试通过。

### Q: 如何调试公式转换问题？
A: 查看日志中的解析结果，确认公式被正确识别。如果MathML转换失败，会回退到LaTeX文本显示。

### Q: 可以批量测试吗？
A: 可以，参见 `TEST_FORMAT_GUIDE.md` 中的"批量测试"章节。

## 后续改进方向

1. **单元测试** - 为核心模块添加自动化单元测试
2. **回归测试** - 建立测试用例库，自动对比输出
3. **性能基准** - 测试大文档的处理性能
4. **错误处理** - 增强对异常输入的处理能力
5. **格式验证** - 自动验证生成的Word文档格式

## 总结

通过添加完整的日志输出和独立的测试工具，我们现在可以：

1. **快速调试** - 看到完整的LLM输出，快速定位问题
2. **低成本测试** - 无需调用API即可测试格式转换
3. **高效迭代** - 修改代码后1秒内看到效果
4. **灵活测试** - 支持多种输入方式，适应不同场景

这些改进显著提升了开发效率，降低了测试成本，是项目质量保证的重要基础设施。

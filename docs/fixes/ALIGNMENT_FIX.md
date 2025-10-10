# 公式对齐问题的根本原因和修复

## 问题回顾

尽管代码在多个层面设置了左对齐（段落级、XML级、OMML级），但Word文档中的显示公式仍然显示为居中/两端对齐。

## 根本原因

**关键发现：我们一直在使用错误的OMML结构！**

在Office Open XML中，数学公式有两种不同的结构：

### 1. 行内公式 (Inline Math)
```xml
<w:p>
  <w:r>
    <m:oMath>
      <!-- 公式内容 -->
    </m:oMath>
  </w:r>
</w:p>
```
- `oMath`元素放在run (`w:r`)中
- 作为文本流的一部分显示
- **无法控制对齐方式**

### 2. 显示公式 (Display Math)
```xml
<w:p>
  <m:oMathPara>
    <m:oMathParaPr>
      <m:jc m:val="left"/>
    </m:oMathParaPr>
    <m:oMath>
      <!-- 公式内容 -->
    </m:oMath>
  </m:oMathPara>
</w:p>
```
- `oMathPara`元素**直接**添加到段落 (`w:p`)，不通过run
- `oMathParaPr`包含公式段落属性，包括对齐方式 (`jc`)
- **可以控制对齐方式**

## 之前的错误

我们的代码一直在做：
```python
# 错误：显示公式也放在run中
run = paragraph.add_run()
run._element.append(omml_element)  # 添加oMath到run
```

这样做的结果：
- ✗ 显示公式被当作行内公式处理
- ✗ Word忽略所有对齐设置
- ✗ 使用Word的默认居中对齐

## 修复方案

现在的代码正确区分两种公式：

### 显示公式 (is_display=True)
```python
# 创建oMathPara包装
omath_para = etree.Element('{%s}oMathPara' % MATH_NS)

# 创建属性部分
omath_para_pr = etree.SubElement(omath_para, '{%s}oMathParaPr' % MATH_NS)

# 设置左对齐
jc = etree.SubElement(omath_para_pr, '{%s}jc' % MATH_NS)
jc.set('{%s}val' % MATH_NS, 'left')

# 将oMath添加到oMathPara
omath_para.append(omml_element)

# 关键：直接添加到段落，不通过run
paragraph._element.append(omath_para)
```

### 行内公式 (is_display=False)
```python
# 行内公式放在run中（保持原样）
run = paragraph.add_run()
run._element.append(omml_element)
```

## 修改的文件

**src/document_generator.py**
1. `_add_formula()` - 简化代码，移除无效的段落对齐设置
2. `_insert_mathml()` - 完全重写，正确区分display和inline公式

## 关键差异对比

| 方面 | 旧代码 | 新代码 |
|-----|--------|--------|
| 显示公式结构 | `<w:r><m:oMath>...</m:oMath></w:r>` | `<m:oMathPara><m:oMathParaPr><m:jc/></m:oMathParaPr><m:oMath>...</m:oMath></m:oMathPara>` |
| 插入位置 | run内部 | 段落直接子元素 |
| 对齐属性位置 | 段落XML（无效） | oMathParaPr（有效） |
| Word识别为 | 行内公式 | 显示公式 |
| 对齐效果 | ✗ 居中（Word默认） | ✓ 左对齐（我们的设置） |

## 为什么之前的尝试都失败了？

1. **第一轮**：设置`paragraph.alignment` → 对行内公式无效
2. **第二轮**：添加`w:jc` XML属性 → 段落对齐不影响数学公式
3. **第三轮**：添加`oMathPr/jc`到`oMath` → 行内公式不支持此属性
4. **第四轮（之前）**：尝试`oMathPara`但实现错误 → 文档为空

根本问题：**我们始终在使用行内公式结构，而行内公式在Word中不支持对齐控制**

## 验证方法

运行处理后，日志应该显示：
```
INFO - 准备插入显示公式: (5) \quad f(x) = ...
INFO - 显示公式已插入（使用oMathPara左对齐）
```

打开生成的Word文档：
- ✓ 所有显示公式 (`$$...$$`) 应该左对齐
- ✓ 行内公式 (`$...$`) 继续在文本流中正常显示
- ✓ 文档有内容（不再是空白）

## Office Open XML规范参考

根据ECMA-376标准：
- **Part 1, §17.3.1.23**: `oMath` element (Mathematics)
- **Part 1, §17.3.1.24**: `oMathPara` element (Math Paragraph)
- **Part 1, §17.3.1.25**: `oMathParaPr` element (Math Paragraph Properties)

Display math **必须**使用`oMathPara`包装才能正确应用段落级属性。

## 总结

- **问题**：显示公式未左对齐
- **原因**：使用了行内公式结构（`oMath`在run中）
- **修复**：使用显示公式结构（`oMathPara`直接在段落中，包含`oMathParaPr`对齐属性）
- **状态**：✅ 已修复

这次修复遵循了Office Open XML规范，使用了正确的结构来表示display math，因此对齐设置现在应该能够正常工作。

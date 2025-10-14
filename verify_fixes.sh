#!/usr/bin/env bash
# 自动验证所有三个问题的修复

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "========================================================================"
echo "自动验证：三个问题修复状态"
echo "========================================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

# 检查函数
check_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((pass_count++))
}

check_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((fail_count++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

# ========================================================================
# 检查1：代码文件是否存在修复
# ========================================================================
echo "检查1：代码文件修复"
echo "------------------------------------------------------------------------"

# 检查formula_converter.py中的OCR修复
if grep -q "ar.*bar" src/formula_converter.py; then
    check_pass "OCR错误修复代码存在（ar{ → \\bar{）"
else
    check_fail "OCR错误修复代码不存在"
fi

if grep -q "subscript_space_number" src/formula_converter.py; then
    check_pass "下标空格修复代码存在（y_0 2 → y_0^2）"
else
    check_fail "下标空格修复代码不存在"
fi

# 检查document_generator.py中的矩阵修复
if grep -q "is_matrix_pattern" src/document_generator.py; then
    check_pass "矩阵括号检测代码存在"
else
    check_fail "矩阵括号检测代码不存在"
fi

# 检查tikz_renderer.py是否存在
if [ -f "src/tikz_renderer.py" ]; then
    check_pass "TikZ渲染器文件存在"
else
    check_fail "TikZ渲染器文件不存在"
fi

# 检查document_generator.py中的TikZ集成
if grep -q "tikz_renderer" src/document_generator.py; then
    check_pass "TikZ渲染器已集成到DocumentGenerator"
else
    check_fail "TikZ渲染器未集成"
fi

echo ""

# ========================================================================
# 检查2：配置文件
# ========================================================================
echo "检查2：配置文件"
echo "------------------------------------------------------------------------"

if grep -q "graphics:" config/config.yaml; then
    check_pass "graphics配置节存在"
else
    check_fail "graphics配置节不存在"
fi

if grep -q "TikZ" config/config.yaml; then
    check_pass "提示词包含TikZ指导"
else
    check_warn "提示词可能缺少TikZ指导"
fi

if grep -q "矩阵" config/config.yaml; then
    check_pass "提示词包含矩阵指导"
else
    check_warn "提示词可能缺少矩阵指导"
fi

echo ""

# ========================================================================
# 检查3：运行Python测试
# ========================================================================
echo "检查3：运行Python测试"
echo "------------------------------------------------------------------------"

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
    check_pass "虚拟环境已激活"
else
    check_warn "虚拟环境不存在，使用系统Python"
fi

# 运行综合测试
echo "运行综合测试（可能需要30-60秒）..."
if python tests/test_all_fixes.py > /tmp/test_output.log 2>&1; then
    # 检查输出中是否有失败标记
    if grep -q "❌" /tmp/test_output.log; then
        check_fail "测试执行成功但有失败项"
        echo "  查看详情: cat /tmp/test_output.log"
    else
        check_pass "所有测试通过"
    fi
else
    check_fail "测试执行失败"
    echo "  查看详情: cat /tmp/test_output.log"
fi

# 检查生成的文档
echo ""
echo "检查生成的测试文档..."
for doc in test_matrices.docx test_tikz.docx test_real_scenario.docx; do
    if [ -f "output/$doc" ]; then
        size=$(du -h "output/$doc" | cut -f1)
        check_pass "文档已生成: $doc ($size)"
    else
        check_warn "文档未生成: $doc"
    fi
done

echo ""

# ========================================================================
# 检查4：Docker环境（如果有）
# ========================================================================
echo "检查4：Docker环境"
echo "------------------------------------------------------------------------"

if command -v docker &> /dev/null; then
    check_pass "Docker已安装"

    # 检查容器是否运行
    if docker ps | grep -q "advanceocr"; then
        check_pass "AdvanceOCR容器正在运行"

        # 检查容器内的代码
        echo "检查容器内的代码..."
        if docker exec $(docker ps -q -f name=advanceocr) test -f /app/src/tikz_renderer.py; then
            check_pass "容器内TikZ渲染器文件存在"
        else
            check_fail "容器内TikZ渲染器文件不存在"
            echo "  需要重建Docker镜像: sudo docker compose build --no-cache"
        fi

        # 检查容器内的修复代码
        if docker exec $(docker ps -q -f name=advanceocr) grep -q "ar{" /app/src/formula_converter.py; then
            check_pass "容器内OCR修复代码存在"
        else
            check_fail "容器内OCR修复代码不存在"
            echo "  需要重建Docker镜像"
        fi

    else
        check_warn "AdvanceOCR容器未运行"
        echo "  启动容器: sudo docker compose up -d"
    fi
else
    check_warn "Docker未安装或无权限"
fi

echo ""

# ========================================================================
# 检查5：TikZ依赖
# ========================================================================
echo "检查5：TikZ依赖"
echo "------------------------------------------------------------------------"

if command -v pdflatex &> /dev/null; then
    check_pass "pdflatex已安装"
else
    check_warn "pdflatex未安装（TikZ渲染将无法工作）"
    echo "  安装: sudo apt-get install texlive-latex-base texlive-latex-extra texlive-pictures"
fi

if command -v pdftoppm &> /dev/null; then
    check_pass "pdftoppm已安装"
else
    check_warn "pdftoppm未安装（TikZ渲染将使用备选方案）"
    echo "  安装: sudo apt-get install poppler-utils"
fi

echo ""

# ========================================================================
# 总结
# ========================================================================
echo "========================================================================"
echo "验证总结"
echo "========================================================================"
echo ""
echo -e "通过: ${GREEN}$pass_count${NC}"
echo -e "失败: ${RED}$fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}🎉 所有检查通过！${NC}"
    echo ""
    echo "生成的测试文档位于 output/ 目录："
    echo "  - test_matrices.docx (矩阵括号测试)"
    echo "  - test_tikz.docx (TikZ渲染测试)"
    echo "  - test_real_scenario.docx (实际场景测试)"
    echo ""
    echo "请在Word中打开这些文档，验证显示是否正确。"
    echo ""
    echo "如果使用Docker，请运行:"
    echo "  sudo docker compose down"
    echo "  sudo docker compose build --no-cache"
    echo "  sudo docker compose up -d"
    exit 0
else
    echo -e "${RED}⚠️  发现 $fail_count 个问题${NC}"
    echo ""
    echo "请查看上述失败项，并采取相应的修复措施。"
    echo ""
    echo "常见问题解决："
    echo "  1. 如果代码检查失败，请确认git pull已执行"
    echo "  2. 如果Docker检查失败，请重建镜像（使用--no-cache）"
    echo "  3. 如果测试失败，查看 /tmp/test_output.log"
    echo ""
    exit 1
fi

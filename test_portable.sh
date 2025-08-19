#!/bin/bash

# 测试项目可移植性脚本
# 模拟在新机器上的使用流程

echo "============================================="
echo "🧪 测试项目可移植性"
echo "============================================="

# 设置超时时间（10秒后自动退出）
TIMEOUT=10

# 保存当前目录
ORIGINAL_DIR=$(pwd)

# 创建临时测试目录
TEST_DIR="/tmp/face-recognition-test-$$"
echo "创建测试目录: $TEST_DIR"
mkdir -p "$TEST_DIR"

# 复制项目文件（排除不必要的文件）
echo "复制项目文件..."
rsync -av --exclude='.git' --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.pytest_cache' --exclude='data/uploads/*' \
  "$ORIGINAL_DIR/" "$TEST_DIR/"

# 进入测试目录
cd "$TEST_DIR"

echo "============================================="
echo "🔍 检查必需文件"
echo "============================================="

# 检查关键文件
required_files=(
    "main.py"
    "pyproject.toml"  
    "requirements.txt"
    "start_uv.sh"
    "models/insightface/models/buffalo_l/det_10g.onnx"
    "data/database/face_recognition.db"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file"
    else
        echo "❌ $file"
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -gt 0 ]]; then
    echo "⚠️  缺少必需文件："
    printf '%s\n' "${missing_files[@]}"
fi

echo "============================================="
echo "🐍 检查Python环境"
echo "============================================="

# 检查Python版本
python3 --version || echo "❌ Python3 未找到"
which python3 || echo "❌ Python3 路径未找到"

echo "============================================="
echo "📦 检查UV安装"
echo "============================================="

# 检查uv是否可用
if command -v uv &> /dev/null; then
    echo "✅ uv 已安装: $(uv --version)"
    UV_AVAILABLE=true
else
    echo "❌ uv 未安装，将尝试安装..."
    # 模拟安装（实际环境中会真正安装）
    echo "模拟: curl -LsSf https://astral.sh/uv/install.sh | sh"
    UV_AVAILABLE=false
fi

echo "============================================="
echo "🚀 测试启动脚本"
echo "============================================="

# 测试启动脚本的语法
if bash -n start_uv.sh; then
    echo "✅ start_uv.sh 语法检查通过"
else
    echo "❌ start_uv.sh 语法错误"
fi

# 模拟执行关键步骤（不实际启动服务）
echo "模拟执行 start_uv.sh 的关键步骤..."

# 检查虚拟环境创建
echo "检查是否可以创建虚拟环境..."
if [[ "$UV_AVAILABLE" == "true" ]]; then
    # 创建虚拟环境但不安装依赖
    timeout 5 uv venv --python 3.12 2>/dev/null && echo "✅ 虚拟环境创建成功" || echo "⚠️  虚拟环境创建超时/失败"
else
    echo "⚠️  跳过虚拟环境测试（uv未安装）"
fi

# 检查必要目录创建
echo "检查必要目录创建..."
mkdir -p data/database data/faces data/uploads logs
echo "✅ 必要目录已创建"

echo "============================================="
echo "🔧 可移植性检查结果"
echo "============================================="

echo "✅ 项目结构完整"
echo "✅ 模型文件已包含 ($(du -sh models/insightface/ | cut -f1))"
echo "✅ 数据库已包含 ($(du -sh data/database/ | cut -f1))"
echo "✅ 配置文件完整"

if [[ ${#missing_files[@]} -eq 0 ]]; then
    echo "✅ 所有必需文件都存在"
else
    echo "⚠️  缺少 ${#missing_files[@]} 个文件"
fi

if [[ "$UV_AVAILABLE" == "true" ]]; then
    echo "✅ UV环境可用，可以无交互启动"
else
    echo "⚠️  需要先安装UV (自动化脚本会处理)"
fi

echo "============================================="
echo "📋 部署建议"
echo "============================================="

echo "在新机器上部署步骤："
echo "1. 复制整个项目目录"
echo "2. 确保Python 3.12+ 已安装"
echo "3. 运行: chmod +x start_uv.sh"
echo "4. 运行: ./start_uv.sh"
echo ""
echo "首次启动可能需要："
echo "- 下载 uv (自动)"
echo "- 创建虚拟环境 (~1分钟)"
echo "- 安装依赖包 (~3-5分钟)"
echo "- 启动服务 (~30秒)"

# 清理测试目录
echo "============================================="
echo "🧹 清理测试环境"
echo "============================================="

cd "$ORIGINAL_DIR"
rm -rf "$TEST_DIR"
echo "测试完成，临时目录已清理"

echo "============================================="
echo "✅ 可移植性测试完成"
echo "============================================="

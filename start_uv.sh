#!/bin/bash

# 使用 uv 的先进人脸识别系统启动脚本 (InsightFace + DeepFace)

echo "============================================="
echo "🚀 先进人脸识别系统启动 (UV + InsightFace + DeepFace)"
echo "============================================="

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装，正在安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # 重新加载 shell 配置
    source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || true
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "✅ uv 版本: $(uv --version)"

# 检查Python版本
echo "检查Python环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ 未找到Python3，请先安装Python 3.12+"
    exit 1
fi

# 创建或同步虚拟环境 (使用Python 3.12)
echo "创建/同步虚拟环境 (Python 3.12)..."
if [[ ! -d ".venv" ]]; then
    uv venv --python 3.12
else
    echo "虚拟环境已存在，跳过创建步骤"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 安装依赖 (包含先进的人脸识别框架)
echo "使用 uv 安装先进依赖包 (TensorFlow, InsightFace, DeepFace)..."
uv pip install -e .

# 检查必要目录
echo "检查必要目录..."
mkdir -p data/database
mkdir -p data/faces
mkdir -p data/uploads
mkdir -p logs

# 启动应用
echo "🚀 启动先进人脸识别系统 (InsightFace + DeepFace + FastAPI)..."
echo "特性: 99.83% LFW精度 + 多模型支持 + 属性分析"

# 检查是否是测试模式
if [[ "$1" == "--test" ]]; then
    echo "🧪 测试模式：检查依赖和配置..."
    python -c "
import sys
sys.path.insert(0, '.')
try:
    from src.utils.model_manager import setup_model_environment
    setup_model_environment()
    print('✅ 模型环境配置正常')
except Exception as e:
    print(f'❌ 模型环境配置失败: {e}')
    sys.exit(1)

try:
    from src.api.advanced_fastapi_app import create_app
    app = create_app()
    print('✅ FastAPI应用创建正常')
except Exception as e:
    print(f'❌ FastAPI应用创建失败: {e}')
    sys.exit(1)

print('✅ 所有依赖检查通过，可以正常启动服务')
"
    echo "测试完成！运行 './start_uv.sh' 启动服务"
else
    python main.py "$@"
fi

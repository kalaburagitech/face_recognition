#!/bin/bash

# 人脸识别系统启动脚本 - 支持开发和生产模式

echo "============================================="
echo "🚀 人脸识别系统启动 (InsightFace + FastAPI)"
echo "============================================="

# 参数解析
PRODUCTION=false
PORT=8000
HOST="0.0.0.0"
THREADS=4

while [[ $# -gt 0 ]]; do
    case $1 in
        --production)
            PRODUCTION=true
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --threads)
            THREADS="$2"
            shift 2
            ;;
        --test)
            TEST_MODE=true
            shift
            ;;
        --help)
            echo "使用方法:"
            echo "  ./start_uv.sh                    # 开发模式"
            echo "  ./start_uv.sh --production       # 生产模式"
            echo "  ./start_uv.sh --test             # 测试模式"
            echo "  ./start_uv.sh --port 8080        # 指定端口"
            echo "  ./start_uv.sh --threads 8        # 指定线程数"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装，正在安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || true
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "✅ uv 版本: $(uv --version)"

# 创建虚拟环境
echo "创建/同步虚拟环境..."
if [[ ! -d ".venv" ]]; then
    uv venv --python 3.12
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
echo "安装依赖包..."
uv pip install -e .

# 检查必要目录
mkdir -p data/database data/faces data/uploads logs

# 测试模式
if [[ "$TEST_MODE" == true ]]; then
    echo "🧪 测试模式：检查依赖和配置..."
    python -c "
import sys
sys.path.insert(0, '.')
try:
    from src.utils.model_manager import setup_model_environment
    setup_model_environment()
    from src.api.advanced_fastapi_app import create_app
    app = create_app()
    print('✅ 所有依赖检查通过')
except Exception as e:
    print(f'❌ 配置失败: {e}')
    sys.exit(1)
"
    echo "测试完成！运行 './start_uv.sh' 启动服务"
    exit 0
fi

# 启动服务
if [[ "$PRODUCTION" == true ]]; then
    echo "🚀 生产模式启动 (多线程: $THREADS, 端口: $PORT)"
    echo "⚠️  使用单worker避免入库冲突"
    python main.py --use-gunicorn --workers 1 --threads $THREADS --host $HOST --port $PORT
else
    echo "🚀 开发模式启动 (端口: $PORT)"
    python main.py --reload --host $HOST --port $PORT
fi

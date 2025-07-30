#!/bin/bash

# 人脸识别系统开发模式启动脚本

echo "=================================="
echo "人脸识别系统 - 开发模式"
echo "=================================="

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "虚拟环境不存在，请先运行 ./start_uv.sh 或 ./start.sh"
    exit 1
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 启动开发服务器 (热重载)
echo "启动开发服务器 (热重载模式)..."
python main.py --reload --log-level DEBUG
#!/bin/bash

# 人脸识别系统启动脚本

echo "=================================="
echo "人脸识别系统启动脚本"
echo "=================================="

# 检查Python版本
echo "检查Python环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: 未找到Python3，请先安装Python 3.7+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt

# 检查必要目录
echo "检查必要目录..."
mkdir -p data/database
mkdir -p data/faces
mkdir -p data/uploads
mkdir -p logs

# 启动应用
echo "启动人脸识别系统..."
python main.py

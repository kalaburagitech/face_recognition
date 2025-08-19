#!/bin/bash

# 完整的项目可移植性验证脚本
# 验证项目是否可以在新机器上直接运行

echo "============================================="
echo "🌟 人脸识别系统 - 完整部署验证"
echo "============================================="

# 检查当前环境
echo "当前环境检查："
echo "- 操作系统: $(uname -a)"
echo "- Python版本: $(python3 --version 2>/dev/null || echo '未安装')"
echo "- 当前用户: $(whoami)"
echo "- 工作目录: $(pwd)"

echo ""
echo "============================================="
echo "📦 检查项目完整性"
echo "============================================="

# 检查关键文件和目录
required_items=(
    "main.py:file"
    "pyproject.toml:file"
    "requirements.txt:file"
    "start_uv.sh:file"
    "src/:dir"
    "models/insightface/models/buffalo_l/:dir"
    "data/database/:dir"
    "web/:dir"
)

missing_count=0
echo "检查必需文件和目录："
for item in "${required_items[@]}"; do
    name="${item%%:*}"
    type="${item##*:}"
    
    if [[ "$type" == "file" ]]; then
        if [[ -f "$name" ]]; then
            echo "✅ $name (文件)"
        else
            echo "❌ $name (文件缺失)"
            ((missing_count++))
        fi
    elif [[ "$type" == "dir" ]]; then
        if [[ -d "$name" ]]; then
            echo "✅ $name (目录)"
        else
            echo "❌ $name (目录缺失)"
            ((missing_count++))
        fi
    fi
done

echo ""
echo "模型文件大小："
if [[ -d "models/insightface/" ]]; then
    echo "- InsightFace模型: $(du -sh models/insightface/ | cut -f1)"
fi

if [[ -d "data/database/" ]]; then
    echo "- 数据库大小: $(du -sh data/database/ | cut -f1)"
fi

echo ""
echo "============================================="
echo "🔧 环境依赖检查"
echo "============================================="

# 检查Python
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1)
    echo "✅ Python: $python_version"
    
    # 检查Python版本是否符合要求
    if python3 -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" 2>/dev/null; then
        echo "✅ Python版本符合要求 (>=3.9)"
    else
        echo "⚠️  Python版本可能不符合要求，建议使用3.9+"
    fi
else
    echo "❌ Python3 未安装"
    ((missing_count++))
fi

# 检查uv
if command -v uv &> /dev/null; then
    echo "✅ uv: $(uv --version)"
else
    echo "⚠️  uv 未安装 (将自动安装)"
fi

echo ""
echo "============================================="
echo "🧪 启动脚本测试"
echo "============================================="

# 检查启动脚本权限
if [[ -x "start_uv.sh" ]]; then
    echo "✅ start_uv.sh 有执行权限"
else
    echo "⚠️  start_uv.sh 需要执行权限，正在设置..."
    chmod +x start_uv.sh
fi

# 语法检查
if bash -n start_uv.sh; then
    echo "✅ start_uv.sh 语法检查通过"
else
    echo "❌ start_uv.sh 语法错误"
    ((missing_count++))
fi

echo ""
echo "============================================="
echo "🚀 实际部署测试"
echo "============================================="

if [[ $missing_count -eq 0 ]]; then
    echo "开始完整部署测试（这将需要几分钟）..."
    echo "正在运行: ./start_uv.sh --test"
    echo ""
    
    # 运行测试模式
    if timeout 180 ./start_uv.sh --test; then
        echo ""
        echo "✅ 部署测试成功！"
        
        echo ""
        echo "============================================="
        echo "🎉 部署就绪报告"
        echo "============================================="
        
        echo "✅ 项目结构完整"
        echo "✅ 依赖环境正常"
        echo "✅ 启动脚本工作正常"
        echo "✅ 模型文件完整 ($(du -sh models/ | cut -f1))"
        echo "✅ 数据库文件完整"
        echo "✅ 所有组件测试通过"
        
        echo ""
        echo "🚀 生产部署指令："
        echo "1. 确保项目权限正确: chmod +x start_uv.sh"
        echo "2. 启动服务: ./start_uv.sh"
        echo "3. 访问Web界面: http://localhost:8000"
        echo "4. API文档: http://localhost:8000/docs"
        
        echo ""
        echo "📊 首次启动预计时间："
        echo "- 安装uv (如需要): ~30秒"
        echo "- 创建虚拟环境: ~1分钟"  
        echo "- 安装依赖包: ~3-5分钟"
        echo "- 启动服务: ~30秒"
        echo "- 总计: 约5-7分钟"
        
    else
        echo ""
        echo "❌ 部署测试失败"
        echo "请检查错误信息并解决问题"
        exit 1
    fi
else
    echo "❌ 发现 $missing_count 个问题，无法进行部署测试"
    echo "请先解决上述问题"
    exit 1
fi

echo ""
echo "============================================="
echo "✨ 验证完成 - 项目可移植！"
echo "============================================="

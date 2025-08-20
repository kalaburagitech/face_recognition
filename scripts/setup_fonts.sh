#!/bin/bash
# 字体环境设置脚本
# 确保项目字体正确配置

echo "🔧 设置中文字体环境..."

# 检查是否在项目根目录
if [ ! -f "main.py" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 创建字体目录
echo "📁 创建字体目录..."
mkdir -p assets/fonts

# 检查系统字体
echo "🔍 检查系统字体..."
if [ -f "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc" ]; then
    echo "✅ 发现文泉驿微米黑字体"
    
    # 复制到项目如果不存在
    if [ ! -f "assets/fonts/wqy-microhei.ttc" ]; then
        cp "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc" assets/fonts/
        echo "✅ 已复制微米黑字体到项目"
    else
        echo "ℹ️  项目中已有微米黑字体"
    fi
else
    echo "⚠️  系统未找到文泉驿微米黑字体"
    echo "💡 建议安装: sudo apt-get install fonts-wqy-microhei"
fi

if [ -f "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc" ]; then
    echo "✅ 发现文泉驿正黑字体"
    
    # 复制到项目如果不存在
    if [ ! -f "assets/fonts/wqy-zenhei.ttc" ]; then
        cp "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc" assets/fonts/
        echo "✅ 已复制正黑字体到项目"
    else
        echo "ℹ️  项目中已有正黑字体"
    fi
else
    echo "⚠️  系统未找到文泉驿正黑字体"
    echo "💡 建议安装: sudo apt-get install fonts-wqy-zenhei"
fi

# 刷新字体缓存
echo "🔄 刷新字体缓存..."
if command -v fc-cache >/dev/null 2>&1; then
    fc-cache -fv >/dev/null 2>&1
    echo "✅ 字体缓存已刷新"
else
    echo "⚠️  fc-cache不可用，跳过缓存刷新"
fi

# 检查项目字体
echo "📊 项目字体统计:"
if [ -d "assets/fonts" ]; then
    font_count=$(ls -1 assets/fonts/*.tt* 2>/dev/null | wc -l)
    echo "   字体文件数量: $font_count"
    
    if [ $font_count -gt 0 ]; then
        total_size=$(du -sh assets/fonts/ | cut -f1)
        echo "   总占用空间: $total_size"
        echo "   字体文件:"
        ls -lh assets/fonts/*.tt* 2>/dev/null | awk '{print "     " $9 " (" $5 ")"}'
    fi
else
    echo "   ❌ 字体目录不存在"
fi

# 运行字体测试（如果Python环境可用）
if command -v python >/dev/null 2>&1; then
    echo "🧪 运行字体测试..."
    if python -c "import sys; sys.path.append('.'); from src.utils.font_manager import get_font_manager; fm=get_font_manager(); print('✅ 字体管理器正常' if fm.get_font(20) else '❌ 字体加载失败')" 2>/dev/null; then
        echo "✅ 字体功能测试通过"
    else
        echo "⚠️  字体功能测试失败，请检查Python环境"
    fi
else
    echo "⚠️  Python不可用，跳过功能测试"
fi

echo ""
echo "🎉 字体环境设置完成！"
echo ""
echo "📝 使用说明:"
echo "   - 运行 'python scripts/font_manager.py check' 检查详细状态"
echo "   - 运行 'python scripts/font_manager.py test' 测试字体渲染"
echo "   - 字体文件位于 assets/fonts/ 目录"
echo ""
echo "🐳 Docker部署注意事项:"
echo "   - Dockerfile已配置自动安装系统字体"
echo "   - assets/fonts/ 目录会被复制到容器中"
echo "   - 容器启动时会自动刷新字体缓存"

#!/bin/bash

# 项目清理脚本
# 清理不必要的文件和目录

echo "🧹 开始清理人脸识别系统项目..."

# 项目根目录
PROJECT_ROOT="/opt/data2/chenlei/face-recognition-system"
cd "$PROJECT_ROOT"

# 清理日志文件
echo "📄 清理日志文件..."
if [ -d "logs" ]; then
    # 保留最近3天的日志，删除其他
    find logs/ -name "*.log" -type f -mtime +3 -delete 2>/dev/null || true
    # 清空当前日志文件内容但保留文件
    if [ -f "logs/face_recognition.log" ]; then
        > logs/face_recognition.log
        echo "   ✅ 清空了当前日志文件"
    fi
fi

# 清理Python缓存
echo "🐍 清理Python缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
echo "   ✅ 已清理Python缓存文件"

# 清理测试文件
echo "🧪 清理测试文件..."
test_files=(
    "test_upload.html"
    "debug_upload.html"
    "test_*.py"
    "debug_*.py"
    "*_test.py"
    "test_*"
)

for pattern in "${test_files[@]}"; do
    find . -name "$pattern" -type f -delete 2>/dev/null || true
done
echo "   ✅ 已清理测试文件"

# 清理临时文件
echo "🗂️  清理临时文件..."
temp_patterns=(
    "*.tmp"
    "*.temp"
    "*~"
    ".DS_Store"
    "Thumbs.db"
    "*.swp"
    "*.swo"
    ".*.swp"
)

for pattern in "${temp_patterns[@]}"; do
    find . -name "$pattern" -type f -delete 2>/dev/null || true
done
echo "   ✅ 已清理临时文件"

# 清理上传目录中的测试文件
echo "📂 清理上传目录..."
if [ -d "data/uploads" ]; then
    # 删除7天前的上传文件
    find data/uploads/ -type f -mtime +7 -delete 2>/dev/null || true
    echo "   ✅ 已清理7天前的上传文件"
fi

# 清理空目录
echo "📁 清理空目录..."
find . -type d -empty -delete 2>/dev/null || true
echo "   ✅ 已清理空目录"

# 清理数据库备份文件（如果存在）
echo "🗄️  清理数据库文件..."
if [ -d "data/database" ]; then
    # 清理SQLite的临时文件
    find data/database/ -name "*.db-shm" -delete 2>/dev/null || true
    find data/database/ -name "*.db-wal" -delete 2>/dev/null || true
    # 删除旧的备份文件
    find data/database/ -name "*.db.bak*" -mtime +7 -delete 2>/dev/null || true
    echo "   ✅ 已清理数据库临时文件"
fi

# 优化项目结构
echo "🏗️  优化项目结构..."

# 确保重要目录存在
important_dirs=(
    "data/faces"
    "data/uploads"
    "data/database"
    "logs"
    "web/assets/css"
    "web/assets/js"
    "web/assets/images"
)

for dir in "${important_dirs[@]}"; do
    mkdir -p "$dir"
done

# 创建.gitkeep文件来保持空目录
for dir in "${important_dirs[@]}"; do
    if [ -d "$dir" ] && [ -z "$(ls -A "$dir")" ]; then
        touch "$dir/.gitkeep"
    fi
done

echo "   ✅ 已优化项目结构"

# 检查文件权限
echo "🔐 检查文件权限..."
chmod +x *.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true
chmod -R 755 web/assets/ 2>/dev/null || true
echo "   ✅ 已设置正确的文件权限"

# 生成清理报告
echo "📊 生成清理报告..."
{
    echo "# 项目清理报告"
    echo "**清理时间**: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "## 清理内容"
    echo "- ✅ Python缓存文件 (__pycache__, *.pyc, *.pyo)"
    echo "- ✅ 测试文件 (test_*, debug_*, *_test.py)"
    echo "- ✅ 临时文件 (*.tmp, *.temp, *~, .DS_Store, *.swp)"
    echo "- ✅ 旧日志文件 (>3天)"
    echo "- ✅ 旧上传文件 (>7天)"
    echo "- ✅ 数据库临时文件 (*.db-shm, *.db-wal)"
    echo "- ✅ 空目录"
    echo ""
    echo "## 当前目录结构"
    echo '```'
    tree -I '__pycache__|*.pyc|*.pyo|node_modules|.git' -L 3 2>/dev/null || find . -type d -not -path '*/\.*' | head -20
    echo '```'
    echo ""
    echo "## 磁盘使用情况"
    echo '```'
    du -sh . 2>/dev/null || echo "无法获取磁盘使用信息"
    echo '```'
} > "CLEANUP_REPORT.md"

echo "   ✅ 已生成清理报告: CLEANUP_REPORT.md"

# 最终统计
echo ""
echo "🎉 项目清理完成！"
echo ""
echo "📈 清理统计:"
echo "   - 项目根目录: $PROJECT_ROOT"
echo "   - 清理时间: $(date '+%Y-%m-%d %H:%M:%S')"
if command -v du >/dev/null 2>&1; then
    echo "   - 当前大小: $(du -sh . 2>/dev/null | cut -f1)"
fi

echo ""
echo "🚀 下一步建议:"
echo "   1. 运行 'python main.py' 测试系统功能"
echo "   2. 检查 web 界面是否正常工作"
echo "   3. 查看 CLEANUP_REPORT.md 了解详细清理信息"
echo ""

# 检查是否有Git仓库，如果有则显示状态
if [ -d ".git" ]; then
    echo "📋 Git 状态:"
    git status --porcelain 2>/dev/null | head -10 || echo "   无法获取Git状态"
    echo ""
fi

echo "✨ 清理脚本执行完毕！"

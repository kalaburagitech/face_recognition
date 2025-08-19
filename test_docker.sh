#!/bin/bash
# 人脸识别系统 Docker 测试脚本

echo "🧪 Docker 部署测试..."

# 构建镜像
echo "📦 构建镜像..."
docker-compose build

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待启动
echo "⏳ 等待启动完成..."
sleep 60

# 测试健康检查
echo "🔍 测试健康检查..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ 健康检查通过"
else
    echo "❌ 健康检查失败"
    docker-compose logs
    exit 1
fi

# 测试API
echo "📡 测试API接口..."
if curl -s http://localhost:8000/api/statistics | grep -q "total_persons"; then
    echo "✅ API接口正常"
else
    echo "❌ API接口异常"
fi

echo "🎉 测试完成！"
echo "🌐 访问地址: http://localhost:8000"
echo "� 停止服务: docker-compose down"

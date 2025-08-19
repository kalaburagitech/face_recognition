# 人脸识别系统 - Docker 部署指南

## 🚀 快速开始

### 1. 基础要求
- Docker 和 Docker Compose
- 2GB+ 内存
- 1GB+ 磁盘空间

### 2. 一键部署
```bash
# 克隆项目
git clone <your-repo-url>
cd face-recognition-system

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps
```

### 3. 访问系统
- **主页**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📋 主要特性

✅ **一键部署** - Docker Compose 自动化  
✅ **模型内置** - 无需额外下载模型文件  
✅ **自动重启** - 服务异常自动恢复  
✅ **健康监控** - 自动检测服务状态  
✅ **数据持久化** - 数据和日志不丢失  

## 🛠️ 管理命令

```bash
# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 完全清理
docker-compose down -v
```

## 📊 系统配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| 端口 | 8000 | Web 服务端口 |
| 内存限制 | 2GB | 容器最大内存 |
| 启动时间 | ~60s | 首次启动时间 |
| 数据目录 | ./data | 持久化存储 |

## ⚠️ 注意事项

1. **首次启动**: 需要60-90秒下载和安装依赖
2. **端口冲突**: 确保8000端口未被占用
3. **资源需求**: 建议至少2GB内存
4. **数据备份**: ./data 和 ./logs 目录包含重要数据

---

有问题？检查 `docker-compose logs` 或访问 `/health` 接口

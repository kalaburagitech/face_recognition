# 🎯 人脸识别系统 (Face Recognition System)

基于 **InsightFace** 和 **DeepFace** 的高精度人脸识别系统，支持实时检测、人员入库、在线识别等功能。

## 🌟 核心特性

### 🔬 先进算法
- **InsightFace Buffalo-L**: 99.83% LFW精度，业界领先的人脸识别模型
- **DeepFace支持**: 多种预训练模型 (ArcFace, Facenet512, VGG-Face)
- **ONNX优化**: CPU和GPU推理优化，快速响应

### 🚀 高性能架构  
- **FastAPI + AsyncIO**: 高性能异步Web框架
- **多线程安全**: 支持Gunicorn多线程部署，共享模型内存
- **智能缓存**: 内存缓存系统，快速人脸匹配
- **5-8x性能提升**: 相比单线程模式

### 💾 完整功能
- **人脸检测**: 高精度人脸检测和关键点定位
- **人员入库**: 支持单人/批量入库，智能去重
- **实时识别**: 毫秒级人脸识别响应
- **属性分析**: 年龄、性别、表情分析
- **Web管理界面**: 直观的可视化管理
- **RESTful API**: 完整的API接口

## 🚀 快速开始

### 一键启动（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/ccfco/face-recognition-system.git
cd face-recognition-system

# 2. 启动服务（自动安装依赖和模型）
chmod +x start_uv.sh
./start_uv.sh
```

### 生产部署

```bash
# 生产模式（推荐）
./start_uv.sh --production --threads 8

# 自定义配置
./start_uv.sh --production --port 8080 --threads 4
```

### Docker部署

```bash
# 使用docker-compose（推荐）
docker-compose up -d

# 或者直接使用Docker
docker build -t face-recognition-system .
docker run -p 8000:8000 -v ./data:/app/data face-recognition-system
```

### 手动部署

```bash
# 开发模式
python main.py --reload

# 生产模式（推荐单worker多线程）
python main.py --use-gunicorn --workers 1 --threads 8
```

## 📊 系统架构

### ⚠️ 重要提醒
**生产环境强烈建议使用单worker多线程模式**，避免多进程入库时的数据竞争问题。

### 推荐配置
```bash
# 轻量级部署（2-4GB内存）
python main.py --use-gunicorn --workers 1 --threads 4

# 高性能部署（4-8GB内存）  
python main.py --use-gunicorn --workers 1 --threads 8

# 开发调试模式
python main.py --reload --log-level DEBUG
```

### 系统要求
| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| **Python** | 3.9+ | 3.12+ |
| **内存** | 2GB | 4GB+ |
| **存储** | 1GB | 2GB+ |
| **CPU** | 2核 | 4核+ |

### 目录结构
```
face-recognition-system/
├── main.py                    # 统一启动入口
├── start_uv.sh               # 一键启动脚本  
├── requirements.txt          # Python依赖
├── docker-compose.yml        # Docker编排
├── data/                     # 数据目录
│   ├── database/            # SQLite数据库
│   ├── faces/               # 人脸图片存储
│   └── uploads/             # 上传临时文件
├── models/                  # AI模型文件
│   ├── insightface/         # InsightFace模型（326MB）
│   └── deepface/            # DeepFace模型缓存
├── src/                     # 源代码
│   ├── api/                 # FastAPI应用
│   ├── services/            # 业务服务层
│   ├── models/              # 数据模型
│   └── utils/               # 工具函数
└── web/                     # 前端界面
    ├── index.html           # 主页面
    └── assets/              # 静态资源
```

## 🎮 使用指南

### Web管理界面
访问 `http://localhost:8000` 使用完整的图形界面：

| 功能模块 | 描述 | 操作 |
|----------|------|------|
| **人员管理** | 查看、编辑、删除已入库人员 | 支持批量操作 |
| **人脸入库** | 单人或批量添加人脸数据 | 自动质量检测和去重 |
| **实时识别** | 上传照片进行人脸识别 | 返回匹配度和详细信息 |
| **系统统计** | 查看系统运行状态和统计 | 实时性能监控 |

### API接口
访问 `http://localhost:8000/docs` 查看交互式API文档。

#### 核心接口
```bash
# 人员入库
curl -X POST "http://localhost:8000/api/enroll" \
  -F "name=张三" \
  -F "description=员工001" \
  -F "file=@photo.jpg"

# 人脸识别  
curl -X POST "http://localhost:8000/api/recognize" \
  -F "file=@test.jpg"

# 获取统计信息
curl "http://localhost:8000/api/statistics"

# 获取所有人员
curl "http://localhost:8000/api/persons"
```

#### 响应示例
```json
{
  "success": true,
  "person_id": 1,
  "person_name": "张三",
  "faces_detected": 1,
  "face_quality": 0.95,
  "processing_time": 0.123
}
```

## ⚙️ 配置与优化

### 启动参数
```bash
python main.py --help
```

| 参数 | 说明 | 默认值 | 推荐值 |
|------|------|--------|--------|
| `--host` | 监听地址 | 0.0.0.0 | 0.0.0.0 |
| `--port` | 监听端口 | 8000 | 8000 |
| `--use-gunicorn` | 启用多线程模式 | False | True（生产） |
| `--threads` | 线程数 | 4 | 4-8 |
| `--workers` | 进程数 | 1 | 1（避免冲突） |
| `--reload` | 热重载 | False | True（开发） |
| `--log-level` | 日志级别 | INFO | INFO |

### 环境变量配置
```bash
# 可选配置
export FACE_RECOGNITION_MODEL=buffalo_l      # 模型选择
export FACE_RECOGNITION_THRESHOLD=0.25       # 识别阈值  
export FACE_RECOGNITION_LOG_LEVEL=INFO       # 日志级别
export FACE_RECOGNITION_CACHE_SIZE=1000      # 缓存大小
```

### 性能基准

**测试环境**: Intel i7-8700K, 16GB RAM, Python 3.12

| 配置 | 人脸检测 | 人脸识别 | 并发请求 | 内存使用 |
|------|----------|----------|----------|----------|
| 单线程 | ~50ms | ~10ms | 20 req/s | ~400MB |
| 4线程 | ~45ms | ~8ms | 80 req/s | ~450MB |
| 8线程 | ~40ms | ~7ms | 150 req/s | ~500MB |

**优化建议**：
- 生产环境使用4-8线程获得最佳性价比
- 启用模型预加载减少首次访问延迟  
- 合理配置识别阈值平衡精度和召回率

## 🐛 故障排除

### 常见问题

**1. 模型下载失败**
```bash
# 手动检查模型文件
ls -la models/insightface/models/buffalo_l/
# 应该包含: det_10g.onnx, w600k_r50.onnx 等5个文件

# 重新下载模型
rm -rf models/insightface/
python -c "from src.utils.model_manager import setup_model_environment; setup_model_environment()"
```

**2. 内存不足错误**
```bash
# 检查内存使用
free -h

# 减少线程数
python main.py --use-gunicorn --threads 2

# 或关闭模型预加载
export FACE_RECOGNITION_PRELOAD=false
```

**3. 识别精度问题**
```bash
# 查看当前阈值
curl http://localhost:8000/api/config

# 调整识别阈值（降低阈值提高召回率）
curl -X POST "http://localhost:8000/api/update-threshold" -F "threshold=0.2"

# 查看人脸质量评分，确保入库图片质量 > 0.5
```

**4. 端口占用错误**
```bash
# 检查端口占用
netstat -tulpn | grep 8000

# 使用其他端口
python main.py --port 8080
```

**5. Docker构建失败**
```bash
# 清理Docker缓存
docker system prune -f

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

### 日志调试
```bash
# 启用详细日志
python main.py --log-level DEBUG

# 查看实时日志
tail -f logs/face_recognition.log

# 检查服务状态
curl http://localhost:8000/health
```

### 性能诊断
```bash
# 测试服务响应
curl -w "@curl-format.txt" -o /dev/null http://localhost:8000/api/statistics

# 内存监控
watch -n 1 'ps aux | grep python | grep -v grep'

# 验证多线程效果
ab -n 100 -c 10 http://localhost:8000/api/statistics
```

## 📈 监控与维护

### 系统监控
```bash
# 服务健康检查
curl http://localhost:8000/health

# 获取系统统计
curl http://localhost:8000/api/statistics | jq

# 检查缓存状态
curl http://localhost:8000/api/cache/status
```

### 数据备份
```bash
# 备份数据库
cp data/database/face_recognition.db backup/$(date +%Y%m%d_%H%M%S).db

# 备份人脸数据
tar -czf faces_backup_$(date +%Y%m%d).tar.gz data/faces/

# 完整备份
tar --exclude='.venv' --exclude='logs' -czf full_backup_$(date +%Y%m%d).tar.gz .
```

### 维护操作
```bash
# 清理孤立数据
curl -X POST http://localhost:8000/api/maintenance/cleanup

# 重建缓存
curl -X POST http://localhost:8000/api/cache/rebuild

# 数据库优化
curl -X POST http://localhost:8000/api/maintenance/optimize
```

## 🔒 安全配置

### 生产部署安全建议
```bash
# 1. 修改默认端口
python main.py --port 8443

# 2. 启用访问日志
python main.py --use-gunicorn --access-log

# 3. 限制访问来源（nginx配置）
# allow 192.168.1.0/24;
# deny all;

# 4. 启用HTTPS（nginx配置）
# ssl_certificate /path/to/cert.pem;
# ssl_certificate_key /path/to/key.pem;
```

## 🚀 更新与升级

### 版本更新
```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 验证更新
./start_uv.sh --test
```

### 数据迁移
```bash
# 检查数据库版本
python -c "from src.models.database import DatabaseManager; print(DatabaseManager().get_version())"

# 执行数据迁移（如需要）
python scripts/migrate_database.py
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [InsightFace](https://github.com/deepinsight/insightface) - 高精度人脸识别算法
- [DeepFace](https://github.com/serengil/deepface) - 人脸分析框架  
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Web框架
- [OpenCV](https://opencv.org/) - 计算机视觉库

---

## 📞 技术支持

- **GitHub Issues**: [提交问题](https://github.com/ccfco/face-recognition-system/issues)
- **项目文档**: [详细文档](https://github.com/ccfco/face-recognition-system/wiki)
- **更新日志**: [版本历史](https://github.com/ccfco/face-recognition-system/releases)

🚀 **立即体验世界级人脸识别技术！**

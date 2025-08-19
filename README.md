# 🎯 人脸识别系统 (Face Recognition System)

基于 **InsightFace** 和 **DeepFace** 的高精度人脸识别系统，支持实时检测、人员入库、在线识别等功能。

## 🌟 核心特性

- **InsightFace Buffalo-L**: 99.83% LFW精度，业界领先
- **FastAPI + AsyncIO**: 高性能异步Web框架
- **多线程安全**: 支持Gunicorn多线程部署，共享模型内存
- **智能缓存**: 内存缓存系统，快速人脸匹配

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

### Docker部署

```bash
docker-compose up -d
```

### 生产部署（多线程）

```bash
# 开发模式
python main.py --reload

# 生产模式（推荐）
python main.py --use-gunicorn --threads 4

# 高并发模式（注意：仅限单worker避免入库冲突）
python main.py --use-gunicorn --workers 1 --threads 8
```

## 📊 部署说明

### ⚠️ 重要提醒
**生产环境建议使用单worker多线程模式**，避免多worker入库时的数据竞争问题。

**推荐配置**：
```bash
python main.py --use-gunicorn --workers 1 --threads 4-8
```

### 系统要求
- **Python**: 3.9+ 
- **内存**: 最少2GB，推荐4GB+
- **存储**: 至少1GB可用空间

## 🎮 使用方式

### Web界面
访问 `http://localhost:8000` 使用图形界面：
- 人员管理
- 人脸入库  
- 实时识别

### API接口
访问 `http://localhost:8000/docs` 查看完整API文档。

**核心接口**：
- `POST /api/enroll` - 人员入库
- `POST /api/recognize` - 人脸识别
- `GET /api/statistics` - 系统统计

## ⚙️ 性能优化

**多线程优势**：
- 模型共享：避免重复加载326MB模型文件
- 缓存同步：人脸特征在线程间共享
- 5-8x性能提升

**线程安全**：
- SQLAlchemy scoped_session
- threading.RLock 保护缓存
- 单例模式模型管理

## 🔧 配置选项

```bash
python main.py --help
```

主要参数：
- `--use-gunicorn`: 使用多线程部署
- `--threads N`: 线程数（推荐4-8）  
- `--workers N`: 进程数（推荐1）
- `--reload`: 开发模式热重载

## 🐛 故障排除

**模型下载**：首次启动会自动下载InsightFace模型（约326MB）

**内存不足**：减少线程数或升级内存

**识别精度**：调整阈值参数（默认0.25）

## 📄 许可证

MIT License

---

🚀 **立即体验世界级人脸识别技术！**

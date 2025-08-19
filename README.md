# 🎯 人脸识别系统 (Face Recognition System)

基于 **InsightFace** 和 **DeepFace** 的高精度人脸识别系统，支持实时检测、人员入库、在线识别等功能。

## 🌟 核心特性

### 🔥 先进技术栈
- **InsightFace Buffalo-L**: 99.83% LFW精度，业界领先
- **DeepFace ArcFace**: 多模型支持 (ArcFace, Facenet512, VGG-Face, OpenFace)
- **FastAPI + AsyncIO**: 高性能异步Web框架
- **SQLAlchemy**: 完整的数据库ORM支持
- **OpenCV + PIL**: 强大的图像处理能力

### ⚡ 性能优化
- **多线程安全**: 支持Gunicorn多线程部署，共享模型内存
- **智能缓存**: 内存缓存系统，快速人脸匹配
- **ONNX Runtime**: CPU/GPU优化推理
- **异步处理**: 非阻塞式请求处理

### 🎨 功能完整
- **人脸检测**: 高精度人脸检测和定位
- **人员入库**: 支持单人/批量入库，自动去重
- **实时识别**: 毫秒级人脸识别响应
- **属性分析**: 年龄、性别、表情分析
- **可视化**: 丰富的检测结果可视化
- **Web界面**: 直观的管理界面

## 🚀 快速开始

### 方式一：直接启动（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/ccfco/face-recognition-system.git
cd face-recognition-system

# 2. 启动服务（自动安装依赖）
chmod +x start_uv.sh
./start_uv.sh
```

### 方式二：Docker部署

```bash
# 构建和启动
docker-compose up -d

# 查看状态
docker-compose logs -f
```

### 方式三：生产部署（多线程）

```bash
# 使用优化的主程序
python main_optimized.py --use-gunicorn --threads=8 --workers=2
```

## 📊 部署架构对比

| 部署方式 | 优势 | 适用场景 | 性能 |
|---------|------|----------|------|
| **Uvicorn单进程** | 简单部署，开发友好 | 开发测试，轻量应用 | ⭐⭐⭐ |
| **Gunicorn多线程** | 共享模型内存，高并发 | 生产环境，高负载 | ⭐⭐⭐⭐⭐ |
| **Docker容器** | 环境隔离，易扩展 | 容器化部署 | ⭐⭐⭐⭐ |

### 🎯 推荐配置

**生产环境推荐**：
```bash
python main_optimized.py \
  --use-gunicorn \
  --workers=1 \
  --threads=8 \
  --host=0.0.0.0 \
  --port=8000
```

**高并发环境**：
```bash
python main_optimized.py \
  --use-gunicorn \
  --workers=2 \
  --threads=16 \
  --host=0.0.0.0 \
  --port=8000
```

## 🔧 配置说明

### 系统要求
- **Python**: 3.9+ (推荐 3.12)
- **内存**: 最少2GB，推荐8GB+
- **存储**: 至少1GB可用空间
- **CPU**: 支持AVX2指令集（现代CPU）

### 环境变量
```bash
# 可选配置
export FACE_RECOGNITION_LOG_LEVEL=INFO
export FACE_RECOGNITION_MODEL=buffalo_l
export FACE_RECOGNITION_THRESHOLD=0.25
```

### 目录结构
```
face-recognition-system/
├── main.py                 # 标准启动脚本
├── main_optimized.py       # 优化启动脚本（支持Gunicorn）
├── start_uv.sh            # 一键启动脚本
├── data/                  # 数据目录
│   ├── database/          # SQLite数据库
│   ├── faces/             # 人脸图片
│   └── uploads/           # 上传临时文件
├── models/                # 模型文件
│   ├── insightface/       # InsightFace模型 (326MB)
│   └── deepface/          # DeepFace模型缓存
├── src/                   # 源代码
│   ├── api/               # API接口
│   ├── services/          # 业务服务
│   ├── models/            # 数据模型
│   └── utils/             # 工具函数
└── web/                   # Web界面
```

## 🎮 使用指南

### Web界面
访问 `http://localhost:8000` 使用图形界面：
- 人员管理
- 人脸入库
- 实时识别
- 系统统计

### API接口
访问 `http://localhost:8000/docs` 查看完整API文档：

#### 核心接口示例

**人员入库**：
```python
import requests

# 单人入库
response = requests.post(
    "http://localhost:8000/api/enroll",
    data={"name": "张三", "description": "员工001"},
    files={"file": open("photo.jpg", "rb")}
)
```

**人脸识别**：
```python
# 人脸识别
response = requests.post(
    "http://localhost:8000/api/recognize",
    files={"file": open("test.jpg", "rb")}
)
result = response.json()
print(f"识别结果: {result['matches']}")
```

**系统统计**：
```python
# 获取统计信息
response = requests.get("http://localhost:8000/api/statistics")
stats = response.json()
print(f"总人员数: {stats['total_persons']}")
```

## ⚙️ 性能调优

### 多线程 vs 多进程

**为什么推荐多线程？**

1. **模型共享**: 多线程共享模型内存，避免重复加载
2. **缓存一致**: 人脸缓存在线程间同步，提高识别速度
3. **资源效率**: 相比多进程，内存使用更少

**线程安全保证**：
- 使用 `threading.RLock()` 保护缓存操作
- 单例模式确保模型实例唯一
- 数据库操作自动同步

### 性能基准

**测试环境**: Intel i7-8700K, 16GB RAM

| 配置 | 人脸检测 | 人脸识别 | 并发处理 |
|------|----------|----------|----------|
| 单线程 | ~50ms | ~10ms | 20 req/s |
| 8线程 | ~45ms | ~8ms | 80 req/s |
| 16线程 | ~40ms | ~7ms | 150 req/s |

### 优化建议

1. **内存优化**：
   ```bash
   # 限制模型精度（如需要）
   export ONNXRUNTIME_OPTIMIZATION_LEVEL=1
   ```

2. **GPU加速**（如有GPU）：
   ```python
   # 修改 src/services/advanced_face_service.py
   providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
   ```

3. **缓存调优**：
   ```python
   # 调整缓存大小
   MAX_CACHE_SIZE = 1000  # 支持1000人
   ```

## 📈 监控和日志

### 日志配置
```bash
# 启动时指定日志级别
python main_optimized.py --log-level=DEBUG
```

### 系统监控
```bash
# 查看实时日志
tail -f logs/face_recognition.log

# 检查系统状态
curl http://localhost:8000/health
```

### 性能监控
```python
# 获取详细统计
import requests
stats = requests.get("http://localhost:8000/api/statistics").json()
print(f"缓存大小: {stats['cache_size']}")
print(f"识别阈值: {stats['recognition_threshold']}")
```

## 🐛 故障排除

### 常见问题

**1. 模型加载失败**
```bash
# 检查模型文件
ls -la models/insightface/models/buffalo_l/
# 应该包含: det_10g.onnx, w600k_r50.onnx 等文件
```

**2. 内存不足**
```bash
# 监控内存使用
free -h
# 减少线程数或升级内存
```

**3. 识别精度低**
```python
# 调整识别阈值
curl -X POST "http://localhost:8000/api/update-threshold" \
  -F "threshold=0.2"  # 降低阈值提高召回率
```

### 性能诊断
```bash
# 运行完整验证
chmod +x verify_deployment.sh
./verify_deployment.sh
```

## 🔄 更新和维护

### 版本更新
```bash
git pull origin main
./start_uv.sh --test  # 测试新版本
```

### 数据备份
```bash
# 备份数据库
cp data/database/face_recognition.db backup/
# 备份人脸数据
tar -czf faces_backup.tar.gz data/faces/
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境
```bash
# 克隆项目
git clone https://github.com/ccfco/face-recognition-system.git
cd face-recognition-system

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
python -m pytest
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [InsightFace](https://github.com/deepinsight/insightface) - 高精度人脸识别
- [DeepFace](https://github.com/serengil/deepface) - 人脸分析框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Web框架
- [OpenCV](https://opencv.org/) - 计算机视觉库

---

**🚀 立即体验世界级人脸识别技术！**

如有问题，请提交 [Issue](https://github.com/ccfco/face-recognition-system/issues) 或查看 [文档](https://github.com/ccfco/face-recognition-system/wiki)。
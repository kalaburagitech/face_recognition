# 统一模型管理系统

## 概述

本项目已实现统一模型管理系统，将所有机器学习模型文件统一存储在项目的 `models/` 目录下，避免模型文件散布在系统各处，便于管理和部署。

## 目录结构

```
models/
├── insightface/           # InsightFace 模型目录
│   └── models/
│       └── buffalo_l/     # buffalo_l 模型文件
│           ├── 1k3d68.onnx         # 68点关键点检测 (137MB)
│           ├── 2d106det.onnx       # 106点关键点检测 (4.8MB)
│           ├── det_10g.onnx        # 人脸检测 (16.1MB)
│           ├── genderage.onnx      # 性别年龄识别 (1.3MB)
│           └── w600k_r50.onnx      # 人脸特征提取 (166.3MB)
├── deepface/              # DeepFace 模型目录
│   └── .deepface/         # DeepFace 自动创建的目录结构
│       ├── weights/       # 模型权重文件
│       │   └── arcface_weights.h5  # ArcFace 模型权重 (130.7MB)
│       └── models/        # 其他模型文件
└── cache/                 # 通用缓存目录
    ├── huggingface/       # HuggingFace 模型缓存
    ├── torch/             # PyTorch 模型缓存
    └── transformers/      # Transformers 模型缓存
```

## 功能特性

### 1. 自动路径配置

系统会自动设置以下环境变量，重定向所有模型下载到项目目录：

**核心模型路径:**
- `DEEPFACE_HOME`: `models/deepface`
- `INSIGHTFACE_HOME`: `models/insightface`

**通用缓存路径:**
- `HUGGINGFACE_HUB_CACHE`: `models/cache/huggingface`
- `TORCH_HOME`: `models/cache/torch`
- `TRANSFORMERS_CACHE`: `models/cache/transformers`

**科学计算库缓存:**
- `SKLEARN_DATA_DIR`: `models/cache/sklearn`
- `MPLCONFIGDIR`: `models/cache/matplotlib`
- `KERAS_HOME`: `models/cache/keras`

**优化配置:**
- `TF_CPP_MIN_LOG_LEVEL`: `1` (减少TensorFlow日志噪音)

**注意**: DeepFace 库有固定的目录结构行为：
- 设置 `DEEPFACE_HOME=models/deepface` 后，DeepFace 会自动在该目录下创建 `.deepface` 子目录
- 实际的模型文件会存储在 `models/deepface/.deepface/weights/` 下
- 这是 DeepFace 库的内部逻辑，无法改变，但不影响正常使用

### 2. 自动模型迁移

- 检查系统默认位置（如 `~/.deepface/`）的现有模型
- 自动迁移到项目目录
- 保持目录结构和文件完整性

### 3. 统一管理接口

通过 `ModelManager` 类提供统一的模型管理功能：

```python
from src.utils.model_manager import get_model_manager

# 获取模型管理器
manager = get_model_manager()

# 获取所有模型路径
paths = manager.get_model_paths()

# 获取统计信息
stats = manager.get_statistics()

# 清理未使用的模型（预览模式）
cleanup_info = manager.clean_unused_models(dry_run=True)
```

## 使用方法

### 1. 应用启动时自动设置

在 `main.py` 中，模型环境会在应用启动时自动设置：

```python
# 设置模型环境（在导入其他模块之前）
from src.utils.model_manager import setup_model_environment
setup_model_environment()
```

### 2. 服务中使用

在 `AdvancedFaceRecognitionService` 中会自动使用统一配置：

```python
class AdvancedFaceRecognitionService:
    def __init__(self, model_name: str = 'buffalo_l'):
        # 初始化模型管理器
        self.model_manager = get_model_manager()
        # ... 其他初始化代码
```

### 3. 测试验证

运行测试脚本验证配置是否正确：

```bash
python test_model_management.py
```

## 配置文件更新

`config.json` 中添加了模型管理相关配置：

```json
{
  "models": {
    "insightface_root": "models/insightface",
    "deepface_root": "models/deepface", 
    "cache_dir": "models/cache",
    "unified_management": true,
    "auto_migrate": true
  }
}
```

## 优势

### 1. 便于管理
- 所有模型文件集中在项目目录
- 清晰的目录结构
- 统一的管理接口

### 2. 便于部署
- 模型文件跟随项目代码
- 无需担心系统路径差异
- 支持容器化部署

### 3. 便于维护
- 模型文件版本控制
- 清理未使用模型
- 统计模型使用情况

### 4. 开发友好
- 自动路径配置
- 无需手动设置环境变量
- 兼容现有代码

## 模型文件大小统计

当前项目中的模型文件：

| 类型 | 数量 | 总大小 | 位置 |
|-----|-----|-------|------|
| InsightFace ONNX | 5个 | ~601MB | `models/insightface/models/buffalo_l/` |
| DeepFace H5 | 2个 | ~684MB | `models/deepface/.deepface/weights/` |
| **总计** | **7个** | **~1.3GB** | **项目 models/ 目录** |

**模型详情:**
- `arcface_weights.h5` (130.7MB) - ArcFace 人脸识别模型
- `vgg_face_weights.h5` (553.2MB) - VGG-Face 人脸识别模型  
- InsightFace Buffalo-L 模型组 (5个ONNX文件)

## 迁移说明

### 从旧版本升级

1. **自动迁移**: 系统会自动检测并迁移 `~/.deepface/` 中的模型文件
2. **手动清理**: 迁移完成后可手动清理系统默认目录：
   ```bash
   # 确认迁移完成后再删除
   rm -rf ~/.deepface/
   ```

### 新项目部署

1. 克隆项目代码
2. 安装依赖：`pip install -r requirements.txt`
3. 运行应用，模型会自动下载到正确位置

## 故障排除

### 1. 模型下载失败

```bash
# 检查网络连接
ping github.com

# 手动测试模型管理器
python test_model_management.py
```

### 2. 路径配置问题

```bash
# 检查环境变量
python -c "import os; print('DEEPFACE_HOME:', os.environ.get('DEEPFACE_HOME'))"
```

### 3. 权限问题

```bash
# 确保模型目录有写权限
chmod -R 755 models/
```

## 更新日志

- **v1.0** (2024-08-11): 实现统一模型管理系统
  - 自动路径配置
  - 模型文件迁移
  - 测试验证脚本
  - 文档完善

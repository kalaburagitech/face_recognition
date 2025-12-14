# Unified model management system

## Overview

This project has implemented a unified model management system，Store all machine learning model files in the project's `models/` under directory，Prevent model files from being scattered throughout the system，Easy to manage and deploy。

## Directory structure

```
models/
├── insightface/           # InsightFace Model catalog
│   └── models/
│       └── buffalo_l/     # buffalo_l model file
│           ├── 1k3d68.onnx         # 68Key point detection (137MB)
│           ├── 2d106det.onnx       # 106Key point detection (4.8MB)
│           ├── det_10g.onnx        # Face detection (16.1MB)
│           ├── genderage.onnx      # gender age identification (1.3MB)
│           └── w600k_r50.onnx      # Facial feature extraction (166.3MB)
├── deepface/              # DeepFace Model catalog
│   └── .deepface/         # DeepFace Automatically created directory structure
│       ├── weights/       # Model weight file
│       │   └── arcface_weights.h5  # ArcFace Model weight (130.7MB)
│       └── models/        # Other model files
└── cache/                 # Common cache directory
    ├── huggingface/       # HuggingFace Model caching
    ├── torch/             # PyTorch Model caching
    └── transformers/      # Transformers Model caching
```

## Features

### 1. Automatic path configuration

The system will automatically set the following environment variables，Redirect all model downloads to the project directory：

**core model path:**
- `DEEPFACE_HOME`: `models/deepface`
- `INSIGHTFACE_HOME`: `models/insightface`

**Universal cache path:**
- `HUGGINGFACE_HUB_CACHE`: `models/cache/huggingface`
- `TORCH_HOME`: `models/cache/torch`
- `TRANSFORMERS_CACHE`: `models/cache/transformers`

**Scientific Computing Library Cache:**
- `SKLEARN_DATA_DIR`: `models/cache/sklearn`
- `MPLCONFIGDIR`: `models/cache/matplotlib`
- `KERAS_HOME`: `models/cache/keras`

**Optimize configuration:**
- `TF_CPP_MIN_LOG_LEVEL`: `1` (reduceTensorFlowlog noise)

**Notice**: DeepFace Libraries have fixed directory structure behavior：
- set up `DEEPFACE_HOME=models/deepface` back，DeepFace will be automatically created in this directory `.deepface` subdirectory
- The actual model files will be stored in `models/deepface/.deepface/weights/` Down
- This is DeepFace The internal logic of the library，cannot be changed，But it does not affect normal use

### 2. Automatic model migration

- Check system default location（like `~/.deepface/`）of existing models
- Automatically migrate to project directory
- Maintain directory structure and file integrity

### 3. Unified management interface

pass `ModelManager` Class provides unified model management functions：

```python
from src.utils.model_manager import get_model_manager

# Get model manager
manager = get_model_manager()

# Get all model paths
paths = manager.get_model_paths()

# Get statistics
stats = manager.get_statistics()

# Clean up unused models（preview mode）
cleanup_info = manager.clean_unused_models(dry_run=True)
```

## How to use

### 1. Set automatically when app starts

exist `main.py` middle，The model environment is automatically set when the application starts：

```python
# Set up the model environment（before importing other modules）
from src.utils.model_manager import setup_model_environment
setup_model_environment()
```

### 2. used in service

exist `AdvancedFaceRecognitionService` will automatically use the unified configuration：

```python
class AdvancedFaceRecognitionService:
    def __init__(self, model_name: str = 'buffalo_l'):
        # Initialize model manager
        self.model_manager = get_model_manager()
        # ... Other initialization code
```

### 3. Test verification

Run the test script to verify that the configuration is correct：

```bash
python test_model_management.py
```

## Configuration file update

`config.json` Added model management related configurations in：

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

## Advantages

### 1. Easy to manage
- All model files are concentrated in the project directory
- clear directory structure
- Unified management interface

### 2. Easy to deploy
- Model files follow project code
- No need to worry about system path differences
- Support containerized deployment

### 3. Easy to maintain
- Model file version control
- Clean up unused models
- Statistical model usage

### 4. Development friendly
- Automatic path configuration
- No need to manually set environment variables
- Compatible with existing code

## Model file size statistics

Model files in the current project：

| type | quantity | total size | Location |
|-----|-----|-------|------|
| InsightFace ONNX | 5indivual | ~601MB | `models/insightface/models/buffalo_l/` |
| DeepFace H5 | 2indivual | ~684MB | `models/deepface/.deepface/weights/` |
| **total** | **7indivual** | **~1.3GB** | **project models/ Table of contents** |

**Model details:**
- `arcface_weights.h5` (130.7MB) - ArcFace face recognition model
- `vgg_face_weights.h5` (553.2MB) - VGG-Face face recognition model  
- InsightFace Buffalo-L model group (5indivualONNXdocument)

## Migration instructions

### Upgrading from an older version

1. **Automatic migration**: The system will automatically detect and migrate `~/.deepface/` model files in
2. **Manual cleanup**: After the migration is completed, you can manually clean up the system default directory.：
   ```bash
   # Confirm migration is complete before deleting
   rm -rf ~/.deepface/
   ```

### New project deployment

1. Clone project code
2. Install dependencies：`pip install -r requirements.txt`
3. Run application，The model will automatically download to the correct location

## troubleshooting

### 1. Model download failed

```bash
# Check network connection
ping github.com

# Manually test the model manager
python test_model_management.py
```

### 2. Path configuration problem

```bash
# Check environment variables
python -c "import os; print('DEEPFACE_HOME:', os.environ.get('DEEPFACE_HOME'))"
```

### 3. Permissions issue

```bash
# Make sure the model directory has write permissions
chmod -R 755 models/
```

## Change log

- **v1.0** (2024-08-11): Implement a unified model management system
  - Automatic path configuration
  - Model file migration
  - Test verification script
  - Complete documentation

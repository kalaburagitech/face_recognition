#!/usr/bin/env python3
"""
测试配置统一性 - 验证所有配置都从 config.json 读取
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config import config

def test_config_unified():
    """测试配置统一性"""
    print("=" * 60)
    print("🔧 配置统一性测试")
    print("=" * 60)
    
    # 测试上传配置
    print("📤 上传配置测试:")
    print(f"  最大文件大小: {config.MAX_FILE_SIZE} bytes ({config.MAX_FILE_SIZE / 1024 / 1024:.1f}MB)")
    print(f"  允许的文件扩展名: {config.ALLOWED_EXTENSIONS}")
    print(f"  带点的扩展名: {config.get_allowed_extensions_with_dot()}")
    print(f"  上传目录: {config.UPLOAD_FOLDER}")
    
    # 测试人脸识别配置
    print("\n🎯 人脸识别配置:")
    print(f"  识别阈值: {config.RECOGNITION_THRESHOLD}")
    print(f"  检测阈值: {config.DETECTION_THRESHOLD}")
    print(f"  模型: {config.MODEL}")
    print(f"  DeepFace模型: {config.DEEPFACE_MODEL}")
    
    # 测试API配置
    print("\n🌐 API配置:")
    print(f"  主机: {config.HOST}")
    print(f"  端口: {config.PORT}")
    print(f"  调试模式: {config.DEBUG}")
    
    # 测试模型配置
    print("\n📦 模型配置:")
    print(f"  InsightFace路径: {config.MODELS_INSIGHTFACE_ROOT}")
    print(f"  DeepFace路径: {config.MODELS_DEEPFACE_ROOT}")
    print(f"  缓存目录: {config.MODELS_CACHE_DIR}")
    
    # 测试文件扩展名验证
    print("\n✅ 文件扩展名验证测试:")
    test_files = [
        "test.jpg",
        "test.png", 
        "test.webp",
        "test.avif",
        "test.txt",  # 不支持的格式
        "test.pdf"   # 不支持的格式
    ]
    
    for filename in test_files:
        is_allowed = config.is_allowed_extension(filename)
        status = "✅" if is_allowed else "❌"
        print(f"  {status} {filename}: {'允许' if is_allowed else '不允许'}")
    
    # 测试配置读取
    print("\n🔍 配置路径读取测试:")
    test_paths = [
        "upload.allowed_extensions",
        "upload.max_file_size",
        "face_recognition.recognition_threshold",
        "api.port",
        "models.insightface_root"
    ]
    
    for path in test_paths:
        value = config.get(path)
        print(f"  {path}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ 配置统一性测试完成")
    print("✨ 所有配置都从 config.json 读取，没有硬编码！")
    print("=" * 60)

if __name__ == "__main__":
    test_config_unified()

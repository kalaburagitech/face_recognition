#!/usr/bin/env python3
"""
统一模型管理测试脚本
验证模型路径配置和环境变量设置是否正确
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_model_environment():
    """测试模型环境配置"""
    print("=" * 60)
    print("测试统一模型管理器配置")
    print("=" * 60)
    
    # 导入模型管理器
    from src.utils.model_manager import get_model_manager
    
    try:
        # 初始化模型管理器
        manager = get_model_manager()
        print("✅ 模型管理器初始化成功")
        
        # 获取模型路径配置
        paths = manager.get_model_paths()
        print(f"\n📁 模型目录配置:")
        for key, path in paths.items():
            print(f"  {key}: {path}")
            # 检查目录是否存在
            if Path(path).exists():
                print(f"    ✅ 目录存在")
            else:
                print(f"    ❌ 目录不存在")
        
        # 检查环境变量
        print(f"\n🌍 环境变量设置:")
        env_vars = [
            'DEEPFACE_HOME',
            'INSIGHTFACE_HOME', 
            'HUGGINGFACE_HUB_CACHE',
            'TORCH_HOME',
            'TRANSFORMERS_CACHE',
            'SKLEARN_DATA_DIR',
            'MPLCONFIGDIR',
            'KERAS_HOME',
            'TF_CPP_MIN_LOG_LEVEL'
        ]
        
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                print(f"  {var}: {value}")
                if Path(value).exists():
                    print(f"    ✅ 路径存在")
                else:
                    print(f"    ⚠️  路径不存在，将在使用时创建")
            else:
                print(f"  {var}: 未设置")
        
        # 获取统计信息
        print(f"\n📊 模型统计信息:")
        stats = manager.get_statistics()
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_insightface_integration():
    """测试 InsightFace 集成"""
    print(f"\n" + "=" * 60)
    print("测试 InsightFace 集成")
    print("=" * 60)
    
    try:
        from src.services.advanced_face_service import AdvancedFaceRecognitionService
        
        # 初始化服务（这会触发模型下载）
        print("正在初始化人脸识别服务...")
        service = AdvancedFaceRecognitionService()
        
        if service.app:
            print("✅ InsightFace 初始化成功")
            
            # 检查模型文件是否在正确位置
            models_dir = Path("models/insightface/models")
            if models_dir.exists():
                model_files = list(models_dir.rglob("*.onnx"))
                print(f"  找到 {len(model_files)} 个 ONNX 模型文件:")
                for model_file in model_files:
                    size_mb = model_file.stat().st_size / (1024 * 1024)
                    print(f"    {model_file.name}: {size_mb:.1f} MB")
            else:
                print("  ⚠️  模型目录不存在")
        else:
            print("❌ InsightFace 初始化失败")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ InsightFace 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_deepface_integration():
    """测试 DeepFace 集成"""
    print(f"\n" + "=" * 60)
    print("测试 DeepFace 集成")
    print("=" * 60)
    
    try:
        # 检查 DeepFace 是否能正确识别模型路径
        import numpy as np
        from deepface import DeepFace
        
        # 创建一个测试图像（随机数据）
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        print("测试 DeepFace 模型加载（可能需要下载模型）...")
        
        # 尝试使用 DeepFace 进行特征提取
        try:
            result = DeepFace.represent(
                img_path=test_image,
                model_name='ArcFace',
                enforce_detection=False
            )
            print("✅ DeepFace ArcFace 模型加载成功")
            
            # 检查模型是否下载到了正确位置
            deepface_dir = Path("models/deepface")
            if deepface_dir.exists():
                model_files = []
                for ext in ["*.h5", "*.pb", "*.onnx", "*.pth", "*.bin"]:
                    model_files.extend(deepface_dir.rglob(ext))
                
                print(f"  在项目目录中找到 {len(model_files)} 个 DeepFace 模型文件:")
                for model_file in model_files:
                    size_mb = model_file.stat().st_size / (1024 * 1024)
                    print(f"    {model_file.name}: {size_mb:.1f} MB")
            else:
                print("  ⚠️  DeepFace 模型目录不存在")
            
            return True
            
        except Exception as e:
            print(f"⚠️  DeepFace 模型加载失败（可能需要网络下载）: {e}")
            return False
            
    except Exception as e:
        print(f"❌ DeepFace 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始统一模型管理测试")
    
    tests = [
        ("模型环境配置", test_model_environment),
        ("InsightFace 集成", test_insightface_integration),
        ("DeepFace 集成", test_deepface_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        results[test_name] = test_func()
    
    # 总结测试结果
    print(f"\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！统一模型管理配置正确。")
        return 0
    else:
        print("⚠️  有测试失败，请检查配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())

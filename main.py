#!/usr/bin/env python3
"""
基于 FastAPI 的人脸识别系统主应用程序
"""
import os
import sys
from pathlib import Path
import uvicorn
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api.advanced_fastapi_app import create_app
from src.utils.config import setup_logging, ensure_directories, config

def main():
    """主函数"""
    # 确保必要目录存在
    ensure_directories()
    
    # 设置日志
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("启动先进人脸识别系统 (基于 InsightFace & DeepFace)")
    
    # 创建 FastAPI 应用
    app = create_app()
    
    # 获取配置
    host = config.get("api.host", "0.0.0.0")
    port = config.get("api.port", 8000)  # FastAPI 默认使用 8000 端口
    
    print("="*70)
    print("🚀 先进人脸识别系统启动 (InsightFace + DeepFace)")
    print("="*70)
    print(f"🌐 Web界面: http://{host}:{port}")
    print(f"📋 API文档: http://{host}:{port}/docs")
    print(f"📚 ReDoc文档: http://{host}:{port}/redoc")
    print(f"❤️  健康检查: http://{host}:{port}/api/health")
    print("⚡ 特性: InsightFace高精度检测 + DeepFace多模型支持")
    print("⌨️  按 Ctrl+C 停止服务")
    print("="*70)
    
    try:
        # 使用 uvicorn 启动应用
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            reload=False  # 生产环境建议设为 False
        )
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()

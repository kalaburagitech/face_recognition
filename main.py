#!/usr/bin/env python3
"""
人脸识别系统主程序入口
支持 Web API 和 CLI 模式
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置模型环境（在导入其他模块之前）
from src.utils.model_manager import setup_model_environment
setup_model_environment()

# 导入FastAPI应用
from src.api.advanced_fastapi_app import create_app


def setup_logging(log_level: str = "INFO"):
    """配置日志系统"""
    # 确保日志目录存在
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 配置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(log_dir / "face_recognition.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        "data/database",
        "data/faces", 
        "data/uploads",
        "logs",
        "models"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ 目录已创建/确认: {directory}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="人脸识别系统")
    parser.add_argument("--host", default="0.0.0.0", help="服务器监听地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器监听端口")
    parser.add_argument("--reload", action="store_true", help="启用热重载 (开发模式)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="日志级别")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # 确保目录存在
    ensure_directories()
    
    # 打印启动信息
    print("=" * 60)
    print("🎯 人脸识别系统 (Face Recognition System)")
    print("=" * 60)
    print("🚀 启动地址: http://{}:{}".format(args.host, args.port))
    print("📊 管理界面: http://{}:{}/docs".format(args.host, args.port))
    print("📝 日志级别: {}".format(args.log_level))
    print("🔄 热重载: {}".format('启用' if args.reload else '禁用'))
    print("💡 架构: 单进程 + AsyncIO (高性能异步)")
    print("=" * 60)
    
    try:
        # 创建FastAPI应用
        app = create_app()
        
        # 启动服务器
        import uvicorn
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level.lower(),
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("用户中断，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

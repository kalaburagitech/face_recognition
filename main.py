#!/usr/bin/env python3
"""
Face Recognition System Main Program Entry - Unified Version
Supports Web API and CLI modes, compatible with single-process and multi-threaded deployment
"""


import sys
import os
import argparse
import logging
from pathlib import Path


# Add project root directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# Set up model environment (before importing other modules)
from src.utils.model_manager import setup_model_environment
setup_model_environment()


# Import FastAPI application
from src.api.advanced_fastapi_app import create_app



def setup_logging(log_level: str = "INFO"):
    """Configure logging system"""
    # Ensure log directory exists
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configure log format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(log_dir / "face_recognition.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )



def ensure_directories():
    """Ensure necessary directories exist"""
    directories = [
        "data/database",
        "data/faces", 
        "data/uploads",
        "logs"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)



def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Face Recognition System")
    parser.add_argument("--host", default="0.0.0.0", help="Server listening address")
    parser.add_argument("--port", type=int, default=8000, help="Server listening port")
    parser.add_argument("--reload", action="store_true", help="Enable hot reload (development mode)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes (recommend using --threads)")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads per process (recommend 4-8)")
    parser.add_argument("--use-gunicorn", action="store_true", help="Use Gunicorn multi-threaded deployment (recommended for production)")
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Ensure directories exist
    ensure_directories()
    
    # Print startup information
    print("=" * 60)
    print("🎯 Face Recognition System")
    print("=" * 60)
    print("🚀 Startup Address: http://{}:{}".format(args.host, args.port))
    print("📊 Management Interface: http://{}:{}/docs".format(args.host, args.port))
    print("📝 Log Level: {}".format(args.log_level))
    print("🔄 Hot Reload: {}".format('Enabled' if args.reload else 'Disabled'))
    
    if args.use_gunicorn and not args.reload:
        # Check worker configuration
        if args.workers > 1:
            print("⚠️  Warning: Detected multi-worker configuration (workers={})".format(args.workers))
            print("⚠️  Multi-process mode may cause face database data race issues")
            print("⚠️  Recommended: --workers 1 --threads {} for optimal performance and data consistency".format(args.threads * args.workers))
            print("-" * 60)
        
        print("🚀 Architecture: Gunicorn + {} workers + {} threads (production optimized)".format(args.workers, args.threads))
        print("💡 Features: Multi-threaded shared model memory, 5-8x performance improvement")
        print("🔒 Thread Safety: SQLAlchemy scoped_session + RLock protection")
        print("=" * 60)
        
        # Start with Gunicorn
        import subprocess
        gunicorn_cmd = [
            "gunicorn", 
            "main:create_app_factory",
            f"--bind={args.host}:{args.port}",
            f"--workers={args.workers}",
            f"--threads={args.threads}",
            "--worker-class=uvicorn.workers.UvicornWorker",
            f"--log-level={args.log_level.lower()}",
            "--access-logfile=-",
            "--error-logfile=-",
            "--timeout=120",
            "--max-requests=1000",
            "--max-requests-jitter=50",
            "--preload"  # Preload application, share model memory
        ]
        
        logger.info(f"Starting Gunicorn: {' '.join(gunicorn_cmd)}")
        subprocess.run(gunicorn_cmd)
        
    else:
        print("💡 Architecture: Uvicorn + AsyncIO (development/simple deployment)")
        print("=" * 60)
        
        try:
            # Create FastAPI application
            app = create_app()
            
            # Start server
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
            logger.info("User interrupted, shutting down server...")
        except Exception as e:
            logger.error(f"Server startup failed: {e}")
            sys.exit(1)



# Factory function for Gunicorn deployment
def create_app_factory():
    """Factory function for Gunicorn deployment"""
    setup_logging()
    ensure_directories()
    return create_app()



if __name__ == "__main__":
    main()

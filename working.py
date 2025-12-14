#!/usr/bin/env python3
"""
Facial recognition system main program entrance - unified version
support Web API and CLI model，Compatible with single-process and multi-threaded deployments
"""


import sys
import os
import argparse
import logging
from pathlib import Path


# Add the project root directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# Set up the model environment（before importing other modules）
from src.utils.model_manager import setup_model_environment
setup_model_environment()


# importFastAPIapplication
from src.api.advanced_fastapi_app import create_app



def setup_logging(log_level: str = "INFO"):
    """Configure the logging system"""
    # Make sure the log directory exists
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
    """Make sure the necessary directories exist"""
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
    """main function"""
    parser = argparse.ArgumentParser(description="Facial recognition system")
    parser.add_argument("--host", default="0.0.0.0", help="Server listening address")
    parser.add_argument("--port", type=int, default=8000, help="Server listening port")
    parser.add_argument("--reload", action="store_true", help="Enable hot reload (development mode)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes (Recommended--threads)")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads per process (recommend4-8)")
    parser.add_argument("--use-gunicorn", action="store_true", help="useGunicornMulti-threaded deployment(Recommended production environment)")
    
    args = parser.parse_args()
    
    # Setup log
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Make sure the directory exists
    ensure_directories()
    
    # Print startup information
    print("=" * 60)
    print("🎯 Facial recognition system (Face Recognition System)")
    print("=" * 60)
    print("🚀 Start address: http://{}:{}".format(args.host, args.port))
    print("📊 Management interface: http://{}:{}/docs".format(args.host, args.port))
    print("📝 Log level: {}".format(args.log_level))
    print("🔄 Hot reload: {}".format('enable' if args.reload else 'Disable'))
    
    if args.use_gunicorn and not args.reload:
        # examineworkerConfiguration
        if args.workers > 1:
            print("⚠️  warn: Many detectedworkerConfiguration (workers={})".format(args.workers))
            print("⚠️  Multi-process mode may cause face database data competition issues")
            print("⚠️  Recommended: --workers 1 --threads {} Get the best performance and data consistency".format(args.threads * args.workers))
            print("-" * 60)
        
        print("🚀 Architecture: Gunicorn + {}worker + {}thread (Production optimization)".format(args.workers, args.threads))
        print("💡 characteristic: Multi-threaded shared model memory，5-8xPerformance improvements")
        print("🔒 Thread safety: SQLAlchemy scoped_session + RLockProtect")
        print("=" * 60)
        
        # use Gunicorn start up
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
            "--preload"  # Preload apps，Shared model memory
        ]
        
        logger.info(f"start upGunicorn: {' '.join(gunicorn_cmd)}")
        subprocess.run(gunicorn_cmd)
        
    else:
        print("💡 Architecture: Uvicorn + AsyncIO (develop/Simple deployment)")
        print("=" * 60)
        
        try:
            # createFastAPIapplication
            app = create_app()
            
            # Start the server
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
            logger.info("User interruption，Shutting down server...")
        except Exception as e:
            logger.error(f"Server startup failed: {e}")
            sys.exit(1)



# Factory function，used forGunicorndeploy
def create_app_factory():
    """Factory function，used forGunicorndeploy"""
    setup_logging()
    ensure_directories()
    return create_app()



if __name__ == "__main__":
    main()


"""
Unified configuration management tool - Make sure all configurations start with config.json read，Avoid hardcoding
"""
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Config:
    """Unified configuration management class - All configurations are from config.json read"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        
        # Read all parameters from configuration file，Do not set default class attributes
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all configuration from configuration file into class properties"""
        # Face recognition configuration
        face_config = self.config.get('face_recognition', {})
        self.RECOGNITION_THRESHOLD = face_config.get('recognition_threshold', 0.25)
        self.DETECTION_THRESHOLD = face_config.get('detection_threshold', 0.4)
        self.MODEL = face_config.get('model', 'buffalo_l')
        self.DEEPFACE_MODEL = face_config.get('deepface_model', 'ArcFace')
        self.DET_SIZE = face_config.get('det_size', [640, 640])
        self.PROVIDERS = face_config.get('providers', ["CPUExecutionProvider"])
        self.DUPLICATE_THRESHOLD = face_config.get('duplicate_threshold', 0.93)
        self.ENABLE_CACHE = face_config.get('enable_cache', True)
        self.CACHE_LIMIT = face_config.get('cache_limit', 5000)
        self.BATCH_SIZE = face_config.get('batch_size', 500)
        
        # Database configuration
        db_config = self.config.get('database', {})
        self.DATABASE_PATH = db_config.get('path', 'data/database/face_recognition.db')
        
        # APIConfiguration
        api_config = self.config.get('api', {})
        self.HOST = api_config.get('host', '0.0.0.0')
        self.PORT = api_config.get('port', 8000)
        self.DEBUG = api_config.get('debug', False)
        
        # Upload configuration - completely from config.json read
        upload_config = self.config.get('upload', {})
        self.MAX_FILE_SIZE = upload_config.get('max_file_size', 16777216)
        self.ALLOWED_EXTENSIONS = upload_config.get('allowed_extensions', 
            ["jpg", "jpeg", "png", "bmp", "tiff", "gif", "webp", "avif"])
        self.UPLOAD_FOLDER = upload_config.get('upload_folder', 'data/uploads')
        
        # Log configuration
        log_config = self.config.get('logging', {})
        self.LOG_LEVEL = log_config.get('level', 'INFO')
        self.LOG_FORMAT = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Model configuration
        models_config = self.config.get('models', {})
        self.MODELS_INSIGHTFACE_ROOT = models_config.get('insightface_root', 'models/insightface')
        self.MODELS_DEEPFACE_ROOT = models_config.get('deepface_root', 'models/deepface')
        self.MODELS_CACHE_DIR = models_config.get('cache_dir', 'models/cache')
        self.UNIFIED_MANAGEMENT = models_config.get('unified_management', True)
        self.AUTO_MIGRATE = models_config.get('auto_migrate', True)
    
    def _load_config(self) -> dict:
        """Load configuration file"""
        # Default configuration - and config.json Be consistent
        default_config = {
            "database": {
                "path": "data/database/face_recognition.db"
            },
            "face_recognition": {
                "recognition_threshold": 0.25,
                "detection_threshold": 0.4,
                "model": "buffalo_l",
                "deepface_model": "ArcFace",
                "det_size": [640, 640],
                "providers": ["CPUExecutionProvider"],
                "duplicate_threshold": 0.93,
                "enable_cache": True,
                "cache_limit": 5000,
                "batch_size": 500
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False
            },
            "upload": {
                "max_file_size": 16777216,
                "allowed_extensions": ["jpg", "jpeg", "png", "bmp", "tiff", "gif", "webp", "avif"],
                "upload_folder": "data/uploads"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "models": {
                "insightface_root": "models/insightface",
                "deepface_root": "models/deepface",
                "cache_dir": "models/cache",
                "unified_management": True,
                "auto_migrate": True
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge default configuration，Make sure all necessary keys are present
                    merged_config = self._merge_configs(default_config, config)
                    logger.info(f"Configuration file loaded successfully: {self.config_file}")
                    return merged_config
            except Exception as e:
                logger.warning(f"Failed to load configuration file，Use default configuration: {str(e)}")
        
        # If the configuration file does not exist，Create default configuration
        logger.info(f"Configuration file {self.config_file} does not exist，Create default configuration")
        self._save_config(default_config)
        return default_config
    
    def _merge_configs(self, default: dict, user: dict) -> dict:
        """Recursively merge configuration dictionaries"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _save_config(self, config: dict):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to: {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration file: {str(e)}")
    
    def get(self, key_path: str, default=None):
        """
        Get configuration value based on path
        
        Args:
            key_path: Configuration path，like "upload.allowed_extensions"
            default: default value
            
        Returns:
            configuration value
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_allowed_extensions(self):
        """Get a list of allowed file extensions"""
        return self.ALLOWED_EXTENSIONS
    
    def get_allowed_extensions_with_dot(self):
        """Get a list of extensions with dots（for document verification）"""
        return [f'.{ext}' for ext in self.ALLOWED_EXTENSIONS]
    
    def is_allowed_extension(self, filename: str) -> bool:
        """Check if the filename has an allowed extension"""
        if not filename:
            return False
        
        file_ext = Path(filename).suffix.lower().lstrip('.')
        return file_ext in [ext.lower() for ext in self.ALLOWED_EXTENSIONS]
    
    def get_upload_config(self):
        """Get upload configuration"""
        return {
            'MAX_FILE_SIZE': self.MAX_FILE_SIZE,
            'ALLOWED_EXTENSIONS': self.ALLOWED_EXTENSIONS,
            'UPLOAD_FOLDER': self.UPLOAD_FOLDER
        }
    
    def set(self, key_path: str, value):
        """
        Set configuration values ​​and save to file
        
        Args:
            key_path: Configuration path
            value: new value
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to target location
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set value
        config[keys[-1]] = value
        
        # Reload class properties
        self._load_all_configs()
        
        # Save configuration
        self._save_config(self.config)
        logger.info(f"Configuration has been updated: {key_path} = {value}")
    
    def reload(self):
        """Reload configuration"""
        self.config = self._load_config()
        self._load_all_configs()
        logger.info("Configuration file has been reloaded")
    
    def save(self):
        """Save current configuration to file"""
        self._save_config(self.config)

# Global configuration example
config = Config()

def ensure_directories():
    """Make sure the necessary directories exist"""
    directories = [
        "data",
        "data/database", 
        "data/faces",
        config.UPLOAD_FOLDER,  # Use the upload directory in the configuration
        config.MODELS_INSIGHTFACE_ROOT,
        config.MODELS_DEEPFACE_ROOT,
        config.MODELS_CACHE_DIR,
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Directory created/confirm: {directory}")

# Backwards compatible helper functions
def setup_logging():
    """Set log configuration"""
    level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format=config.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/face_recognition.log', encoding='utf-8')
        ]
    )

def get_upload_config():
    """Get upload configuration - backwards compatible"""
    return config.get_upload_config()
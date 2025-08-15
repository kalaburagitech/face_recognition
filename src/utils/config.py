"""
统一配置管理工具 - 确保所有配置都从 config.json 读取，避免硬编码
"""
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Config:
    """统一配置管理类 - 所有配置都从 config.json 读取"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        
        # 从配置文件读取所有参数，不设置默认的类属性
        self._load_all_configs()
    
    def _load_all_configs(self):
        """从配置文件加载所有配置到类属性"""
        # 人脸识别配置
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
        
        # 数据库配置
        db_config = self.config.get('database', {})
        self.DATABASE_PATH = db_config.get('path', 'data/database/face_recognition.db')
        
        # API配置
        api_config = self.config.get('api', {})
        self.HOST = api_config.get('host', '0.0.0.0')
        self.PORT = api_config.get('port', 8000)
        self.DEBUG = api_config.get('debug', False)
        
        # 上传配置 - 完全从 config.json 读取
        upload_config = self.config.get('upload', {})
        self.MAX_FILE_SIZE = upload_config.get('max_file_size', 16777216)
        self.ALLOWED_EXTENSIONS = upload_config.get('allowed_extensions', 
            ["jpg", "jpeg", "png", "bmp", "tiff", "gif", "webp", "avif"])
        self.UPLOAD_FOLDER = upload_config.get('upload_folder', 'data/uploads')
        
        # 日志配置
        log_config = self.config.get('logging', {})
        self.LOG_LEVEL = log_config.get('level', 'INFO')
        self.LOG_FORMAT = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 模型配置
        models_config = self.config.get('models', {})
        self.MODELS_INSIGHTFACE_ROOT = models_config.get('insightface_root', 'models/insightface')
        self.MODELS_DEEPFACE_ROOT = models_config.get('deepface_root', 'models/deepface')
        self.MODELS_CACHE_DIR = models_config.get('cache_dir', 'models/cache')
        self.UNIFIED_MANAGEMENT = models_config.get('unified_management', True)
        self.AUTO_MIGRATE = models_config.get('auto_migrate', True)
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        # 默认配置 - 与 config.json 保持一致
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
                    # 合并默认配置，确保所有必要的键都存在
                    merged_config = self._merge_configs(default_config, config)
                    logger.info(f"成功加载配置文件: {self.config_file}")
                    return merged_config
            except Exception as e:
                logger.warning(f"加载配置文件失败，使用默认配置: {str(e)}")
        
        # 如果配置文件不存在，创建默认配置
        logger.info(f"配置文件 {self.config_file} 不存在，创建默认配置")
        self._save_config(default_config)
        return default_config
    
    def _merge_configs(self, default: dict, user: dict) -> dict:
        """递归合并配置字典"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _save_config(self, config: dict):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存到: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
    
    def get(self, key_path: str, default=None):
        """
        根据路径获取配置值
        
        Args:
            key_path: 配置路径，如 "upload.allowed_extensions"
            default: 默认值
            
        Returns:
            配置值
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
        """获取允许的文件扩展名列表"""
        return self.ALLOWED_EXTENSIONS
    
    def get_allowed_extensions_with_dot(self):
        """获取带点号的扩展名列表（用于文件验证）"""
        return [f'.{ext}' for ext in self.ALLOWED_EXTENSIONS]
    
    def is_allowed_extension(self, filename: str) -> bool:
        """检查文件名是否有允许的扩展名"""
        if not filename:
            return False
        
        file_ext = Path(filename).suffix.lower().lstrip('.')
        return file_ext in [ext.lower() for ext in self.ALLOWED_EXTENSIONS]
    
    def get_upload_config(self):
        """获取上传配置"""
        return {
            'MAX_FILE_SIZE': self.MAX_FILE_SIZE,
            'ALLOWED_EXTENSIONS': self.ALLOWED_EXTENSIONS,
            'UPLOAD_FOLDER': self.UPLOAD_FOLDER
        }
    
    def set(self, key_path: str, value):
        """
        设置配置值并保存到文件
        
        Args:
            key_path: 配置路径
            value: 新值
        """
        keys = key_path.split('.')
        config = self.config
        
        # 导航到目标位置
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 设置值
        config[keys[-1]] = value
        
        # 重新加载类属性
        self._load_all_configs()
        
        # 保存配置
        self._save_config(self.config)
        logger.info(f"配置已更新: {key_path} = {value}")
    
    def reload(self):
        """重新加载配置"""
        self.config = self._load_config()
        self._load_all_configs()
        logger.info("配置文件已重新加载")
    
    def save(self):
        """保存当前配置到文件"""
        self._save_config(self.config)

# 全局配置实例
config = Config()

def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        "data",
        "data/database", 
        "data/faces",
        config.UPLOAD_FOLDER,  # 使用配置中的上传目录
        config.MODELS_INSIGHTFACE_ROOT,
        config.MODELS_DEEPFACE_ROOT,
        config.MODELS_CACHE_DIR,
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ 目录已创建/确认: {directory}")

# 向后兼容的辅助函数
def setup_logging():
    """设置日志配置"""
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
    """获取上传配置 - 向后兼容"""
    return config.get_upload_config()
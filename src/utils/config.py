"""
配置管理工具
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

class Config:
    """配置管理类"""
    
    # 人脸识别配置
    RECOGNITION_THRESHOLD = 0.25
    MODEL = "buffalo_l"
    DEEPFACE_MODEL = "ArcFace"
    DET_SIZE = [640, 640]
    
    # 数据库配置
    DATABASE_PATH = "data/database/face_recognition.db"
    
    # API配置
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = False
    
    # 上传配置
    MAX_FILE_SIZE = 16777216  # 16MB
    ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "bmp", "tiff"]
    UPLOAD_FOLDER = "data/uploads"
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        # 从配置文件更新类属性
        self._update_from_config()
    
    def _update_from_config(self):
        """从配置文件更新类属性"""
        if 'face_recognition' in self.config:
            face_config = self.config['face_recognition']
            self.RECOGNITION_THRESHOLD = face_config.get('recognition_threshold', 0.25)
            self.DETECTION_THRESHOLD = face_config.get('detection_threshold', 0.5)
            self.MODEL = face_config.get('model', 'buffalo_l')
            self.DEEPFACE_MODEL = face_config.get('deepface_model', 'ArcFace')
            self.DET_SIZE = face_config.get('det_size', [640, 640])
            self.PROVIDERS = face_config.get('providers', ["CPUExecutionProvider"])
            
        if 'database' in self.config:
            db_config = self.config['database']
            self.DATABASE_PATH = db_config.get('path', 'data/database/face_recognition.db')
            
        if 'upload' in self.config:
            upload_config = self.config['upload']
            self.MAX_FILE_SIZE = upload_config.get('max_file_size', 16777216)
            self.ALLOWED_EXTENSIONS = upload_config.get('allowed_extensions', ["jpg", "jpeg", "png", "bmp", "tiff", "webp", "avif"])
            self.UPLOAD_FOLDER = upload_config.get('upload_folder', 'data/uploads')
        
        if 'api' in self.config:
            api_config = self.config['api']
            self.HOST = api_config.get('host', '0.0.0.0')
            self.PORT = api_config.get('port', 8000)
            self.DEBUG = api_config.get('debug', False)
            
        if 'models' in self.config:
            models_config = self.config['models']
            self.MODELS_INSIGHTFACE_ROOT = models_config.get('insightface_root', 'models/insightface')
            self.MODELS_CACHE_DIR = models_config.get('cache_dir', 'models/cache')
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        default_config = {
            "database": {
                "path": "data/database/face_recognition.db"
            },
            "face_recognition": {
                "recognition_threshold": 0.6,  # 人脸识别阈值（用于匹配已知人脸）
                "detection_threshold": 0.5,    # 人脸检测阈值（用于检测是否有人脸）
                "model": "buffalo_l",  # InsightFace 模型: buffalo_l, buffalo_m, buffalo_s
                "deepface_model": "ArcFace",  # DeepFace 模型: ArcFace, Facenet512, VGG-Face, OpenFace
                "det_size": [640, 640],  # 检测尺寸
                "providers": ["CPUExecutionProvider"],  # ONNX 运行提供商
                "duplicate_threshold": 0.95  # 重复入库阈值
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,  # FastAPI 默认端口
                "debug": False
            },
            "upload": {
                "max_file_size": 16777216,  # 16MB
                "allowed_extensions": ["jpg", "jpeg", "png", "bmp", "tiff"],
                "upload_folder": "data/uploads"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "models": {
                "insightface_root": "models/insightface",
                "cache_dir": "models/cache"
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    merged_config = self._merge_configs(default_config, config)
                    return merged_config
            except Exception as e:
                logger.warning(f"加载配置文件失败，使用默认配置: {str(e)}")
        
        # 保存默认配置
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
            key_path: 配置路径，如 "database.path"
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
    
    def set(self, key_path: str, value):
        """
        设置配置值
        
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
        
        # 保存配置
        self._save_config(self.config)
    
    def reload(self):
        """重新加载配置"""
        self.config = self._load_config()
        self._update_from_config()
        logger.info("配置文件已重新加载")
    
    def save(self):
        """保存当前配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存到 {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            raise

# 全局配置实例
config = Config()

def setup_logging():
    """设置日志配置"""
    level_str = config.get("logging.level", "INFO")
    if isinstance(level_str, str):
        level = getattr(logging, level_str.upper())
    else:
        level = logging.INFO
        
    format_str = config.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    if not isinstance(format_str, str):
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('face_recognition.log', encoding='utf-8')
        ]
    )

def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        "data",
        "data/database",
        "data/faces",
        "data/uploads",
        "models",
        "models/insightface",
        "models/cache",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"确保目录存在: {directory}")

def get_upload_config():
    """获取上传配置"""
    return {
        'MAX_FILE_SIZE': config.get("upload.max_file_size", 16777216),
        'ALLOWED_EXTENSIONS': config.get("upload.allowed_extensions", ["jpg", "jpeg", "png"]),
        'UPLOAD_FOLDER': config.get("upload.upload_folder", "data/uploads")
    }

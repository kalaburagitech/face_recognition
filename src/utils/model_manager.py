"""
统一模型管理器
负责管理所有机器学习模型的下载、存储和配置路径
"""
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Any
import json

logger = logging.getLogger(__name__)

class ModelManager:
    """统一模型管理器"""
    
    def __init__(self, project_root: Optional[str] = None):
        """
        初始化模型管理器
        
        Args:
            project_root: 项目根目录，如果为None则自动检测
        """
        if project_root is None:
            # 自动检测项目根目录
            current_file = Path(__file__).resolve()
            self.project_root = current_file.parent.parent.parent
        else:
            self.project_root = Path(project_root)
            
        # 模型根目录
        self.models_root = self.project_root / "models"
        
        # 各类模型目录
        self.insightface_dir = self.models_root / "insightface"
        self.deepface_dir = self.models_root / "deepface"
        self.cache_dir = self.models_root / "cache"
        
        # 确保目录存在
        self._ensure_directories()
        
        # 设置环境变量
        self._setup_environment()
        
        logger.info(f"模型管理器初始化完成，模型根目录: {self.models_root}")
    
    def _ensure_directories(self):
        """确保所有必需的目录存在"""
        directories = [
            self.models_root,
            self.insightface_dir,
            self.deepface_dir,
            self.cache_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"确保目录存在: {directory}")
    
    def _setup_environment(self):
        """设置环境变量以重定向模型下载路径"""
        
        # 设置 DeepFace 模型路径
        os.environ['DEEPFACE_HOME'] = str(self.deepface_dir)
        
        # 设置 InsightFace 模型路径
        os.environ['INSIGHTFACE_HOME'] = str(self.insightface_dir)
        
        # 设置通用缓存目录
        os.environ['HUGGINGFACE_HUB_CACHE'] = str(self.cache_dir / "huggingface")
        os.environ['TORCH_HOME'] = str(self.cache_dir / "torch")
        os.environ['TRANSFORMERS_CACHE'] = str(self.cache_dir / "transformers")
        
        # 设置其他可能的ML库缓存目录
        os.environ['SKLEARN_DATA_DIR'] = str(self.cache_dir / "sklearn")
        os.environ['MPLCONFIGDIR'] = str(self.cache_dir / "matplotlib") 
        os.environ['KERAS_HOME'] = str(self.cache_dir / "keras")
        
        # 设置TensorFlow相关环境变量
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'  # 减少TensorFlow日志噪音
        
        logger.info("环境变量设置完成")
        logger.debug(f"DEEPFACE_HOME: {os.environ.get('DEEPFACE_HOME')}")
        logger.debug(f"INSIGHTFACE_HOME: {os.environ.get('INSIGHTFACE_HOME')}")
    
    def get_model_paths(self) -> Dict[str, str]:
        """
        获取所有模型路径配置
        
        Returns:
            包含所有模型路径的字典
        """
        return {
            'models_root': str(self.models_root),
            'insightface_dir': str(self.insightface_dir),
            'deepface_dir': str(self.deepface_dir),
            'cache_dir': str(self.cache_dir),
            'deepface_weights': str(self.deepface_dir / ".deepface" / "weights"),
            'deepface_models': str(self.deepface_dir / ".deepface" / "models"),
            'huggingface_cache': str(self.cache_dir / "huggingface"),
            'torch_cache': str(self.cache_dir / "torch"),
            'transformers_cache': str(self.cache_dir / "transformers"),
            'sklearn_cache': str(self.cache_dir / "sklearn"),
            'matplotlib_cache': str(self.cache_dir / "matplotlib"),
            'keras_cache': str(self.cache_dir / "keras"),
        }
    
    def configure_insightface(self, model_name: str = 'buffalo_l') -> str:
        """
        配置 InsightFace 模型路径
        
        Args:
            model_name: 模型名称
            
        Returns:
            InsightFace 模型根目录路径
        """
        # 确保 InsightFace 模型目录存在
        models_dir = self.insightface_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查模型是否已存在
        model_dir = models_dir / model_name
        if model_dir.exists():
            logger.info(f"InsightFace 模型 {model_name} 已存在: {model_dir}")
        else:
            logger.info(f"InsightFace 模型 {model_name} 将下载到: {model_dir}")
        
        return str(self.insightface_dir)
    
    def configure_deepface(self) -> Dict[str, str]:
        """
        配置 DeepFace 模型路径
        
        Returns:
            DeepFace 相关路径配置
        """
        # DeepFace 会在 DEEPFACE_HOME 下自动创建 .deepface 目录结构
        # 我们只需要确保基础目录存在即可
        self.deepface_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查是否需要从系统默认位置迁移模型
        home_deepface = Path.home() / ".deepface"
        if home_deepface.exists():
            self._migrate_deepface_models(home_deepface, self.deepface_dir / ".deepface")
        
        return {
            'deepface_home': str(self.deepface_dir),
            'weights_dir': str(self.deepface_dir / ".deepface" / "weights"),
            'models_dir': str(self.deepface_dir / ".deepface" / "models")
        }
    
    def _migrate_deepface_models(self, source_dir: Path, target_dir: Path):
        """
        迁移 DeepFace 模型文件到项目目录
        
        Args:
            source_dir: 源目录 (通常是 ~/.deepface)
            target_dir: 目标目录 (项目中的 models/deepface)
        """
        try:
            if not source_dir.exists():
                return
            
            # 检查源目录中是否有模型文件
            model_files = []
            for pattern in ["*.h5", "*.pb", "*.onnx", "*.pth", "*.bin"]:
                model_files.extend(source_dir.rglob(pattern))
            
            if not model_files:
                logger.info("未发现需要迁移的 DeepFace 模型文件")
                return
            
            logger.info(f"发现 {len(model_files)} 个 DeepFace 模型文件，开始迁移...")
            
            for model_file in model_files:
                # 保持相对路径结构
                relative_path = model_file.relative_to(source_dir)
                target_file = target_dir / relative_path
                
                # 确保目标目录存在
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 复制文件（如果不存在或者源文件更新）
                if not target_file.exists() or model_file.stat().st_mtime > target_file.stat().st_mtime:
                    import shutil
                    shutil.copy2(model_file, target_file)
                    logger.info(f"迁移模型文件: {model_file} -> {target_file}")
                
        except Exception as e:
            logger.error(f"DeepFace 模型迁移失败: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取模型管理统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            'models_root': str(self.models_root),
            'total_size_mb': 0,
            'directories': {},
            'model_counts': {}
        }
        
        try:
            # 遍历模型目录统计
            for subdir in self.models_root.iterdir():
                if subdir.is_dir():
                    size = self._get_directory_size(subdir)
                    file_count = len(list(subdir.rglob("*.*")))
                    
                    stats['directories'][subdir.name] = {
                        'path': str(subdir),
                        'size_mb': round(size / (1024 * 1024), 2),
                        'file_count': file_count
                    }
                    
                    stats['total_size_mb'] += size / (1024 * 1024)
            
            stats['total_size_mb'] = round(stats['total_size_mb'], 2)
            
            # 统计各类模型文件
            for ext in ['.onnx', '.h5', '.pb', '.pth', '.bin']:
                count = len(list(self.models_root.rglob(f"*{ext}")))
                if count > 0:
                    stats['model_counts'][ext] = count
            
        except Exception as e:
            logger.error(f"统计模型信息失败: {e}")
        
        return stats
    
    def _get_directory_size(self, directory: Path) -> int:
        """
        计算目录大小（字节）
        
        Args:
            directory: 目录路径
            
        Returns:
            目录大小（字节）
        """
        total = 0
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total += file_path.stat().st_size
        except Exception as e:
            logger.warning(f"计算目录大小失败 {directory}: {e}")
        
        return total
    
    def clean_unused_models(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        清理未使用的模型文件
        
        Args:
            dry_run: 是否只是预览而不实际删除
            
        Returns:
            清理结果信息
        """
        result = {
            'files_to_remove': [],
            'space_to_free_mb': 0,
            'dry_run': dry_run,
            'removed_files': []
        }
        
        try:
            # 查找可能的重复或过时文件
            # 这里可以添加具体的清理逻辑
            
            # 示例：查找空目录
            for directory in self.models_root.rglob("*"):
                if directory.is_dir() and not any(directory.iterdir()):
                    result['files_to_remove'].append({
                        'path': str(directory),
                        'type': 'empty_directory',
                        'size_mb': 0
                    })
            
            if not dry_run:
                # 实际执行清理
                for item in result['files_to_remove']:
                    path = Path(item['path'])
                    if path.exists():
                        if path.is_dir():
                            path.rmdir()
                        else:
                            path.unlink()
                        result['removed_files'].append(item['path'])
                        logger.info(f"已删除: {path}")
            
        except Exception as e:
            logger.error(f"清理模型文件失败: {e}")
        
        return result

# 全局模型管理器实例
_model_manager = None

def get_model_manager() -> ModelManager:
    """获取全局模型管理器实例"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager

def setup_model_environment():
    """设置模型环境（在应用启动时调用）"""
    manager = get_model_manager()
    logger.info("模型环境设置完成")
    return manager

"""
Unified Model Manager
Responsible for managing the download of all machine learning models、Storage and configuration paths
"""
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Any
import json

logger = logging.getLogger(__name__)

class ModelManager:
    """Unified Model Manager"""
    
    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize model manager
        
        Args:
            project_root: Project root directory，if forNonethen automatically detect
        """
        if project_root is None:
            # Automatically detect project root directory
            current_file = Path(__file__).resolve()
            self.project_root = current_file.parent.parent.parent
        else:
            self.project_root = Path(project_root)
            
        # Model root directory
        self.models_root = self.project_root / "models"
        
        # Catalog of various models
        self.insightface_dir = self.models_root / "insightface"
        self.deepface_dir = self.models_root / "deepface"
        self.cache_dir = self.models_root / "cache"
        
        # Make sure the directory exists
        self._ensure_directories()
        
        # Set environment variables
        self._setup_environment()
        
        logger.info(f"Model manager initialization completed，Model root directory: {self.models_root}")
    
    def _ensure_directories(self):
        """Make sure all required directories exist"""
        directories = [
            self.models_root,
            self.insightface_dir,
            self.deepface_dir,
            self.cache_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Make sure the directory exists: {directory}")
    
    def _setup_environment(self):
        """Set environment variables to redirect model download paths"""
        
        # set up DeepFace model path
        os.environ['DEEPFACE_HOME'] = str(self.deepface_dir)
        
        # set up InsightFace model path
        os.environ['INSIGHTFACE_HOME'] = str(self.insightface_dir)
        
        # Set general cache directory
        os.environ['HUGGINGFACE_HUB_CACHE'] = str(self.cache_dir / "huggingface")
        os.environ['TORCH_HOME'] = str(self.cache_dir / "torch")
        os.environ['TRANSFORMERS_CACHE'] = str(self.cache_dir / "transformers")
        
        # Set other possibleMLlibrary cache directory
        os.environ['SKLEARN_DATA_DIR'] = str(self.cache_dir / "sklearn")
        os.environ['MPLCONFIGDIR'] = str(self.cache_dir / "matplotlib") 
        os.environ['KERAS_HOME'] = str(self.cache_dir / "keras")
        
        # set upTensorFlowRelated environment variables
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'  # reduceTensorFlowlog noise
        
        logger.info("Environment variable setting completed")
        logger.debug(f"DEEPFACE_HOME: {os.environ.get('DEEPFACE_HOME')}")
        logger.debug(f"INSIGHTFACE_HOME: {os.environ.get('INSIGHTFACE_HOME')}")
    
    def get_model_paths(self) -> Dict[str, str]:
        """
        Get all model path configurations
        
        Returns:
            A dictionary containing all model paths
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
        Configuration InsightFace model path
        
        Args:
            model_name: Model name
            
        Returns:
            InsightFace Model root directory path
        """
        # make sure InsightFace Model directory exists
        models_dir = self.insightface_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if the model already exists
        model_dir = models_dir / model_name
        if model_dir.exists():
            logger.info(f"InsightFace Model {model_name} Already exists: {model_dir}")
        else:
            logger.info(f"InsightFace Model {model_name} will be downloaded to: {model_dir}")
        
        return str(self.insightface_dir)
    
    def configure_deepface(self) -> Dict[str, str]:
        """
        Configuration DeepFace model path
        
        Returns:
            DeepFace Related path configuration
        """
        # DeepFace will be in DEEPFACE_HOME Automatically created under .deepface Directory structure
        # We just need to make sure the base directory exists
        self.deepface_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if the model needs to be migrated from the system default location
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
        migrate DeepFace Model files to project directory
        
        Args:
            source_dir: source directory (usually ~/.deepface)
            target_dir: target directory (in the project models/deepface)
        """
        try:
            if not source_dir.exists():
                return
            
            # Check if there is a model file in the source directory
            model_files = []
            for pattern in ["*.h5", "*.pb", "*.onnx", "*.pth", "*.bin"]:
                model_files.extend(source_dir.rglob(pattern))
            
            if not model_files:
                logger.info("No need to migrate found DeepFace model file")
                return
            
            logger.info(f"Discover {len(model_files)} indivual DeepFace model file，Start migration...")
            
            for model_file in model_files:
                # Maintain relative path structure
                relative_path = model_file.relative_to(source_dir)
                target_file = target_dir / relative_path
                
                # Make sure the target directory exists
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy files（If it does not exist or the source file is updated）
                if not target_file.exists() or model_file.stat().st_mtime > target_file.stat().st_mtime:
                    import shutil
                    shutil.copy2(model_file, target_file)
                    logger.info(f"Migrate model files: {model_file} -> {target_file}")
                
        except Exception as e:
            logger.error(f"DeepFace Model migration failed: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get model management statistics
        
        Returns:
            Statistics Dictionary
        """
        stats = {
            'models_root': str(self.models_root),
            'total_size_mb': 0,
            'directories': {},
            'model_counts': {}
        }
        
        try:
            # Traverse model directory statistics
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
            
            # Statistics of various model files
            for ext in ['.onnx', '.h5', '.pb', '.pth', '.bin']:
                count = len(list(self.models_root.rglob(f"*{ext}")))
                if count > 0:
                    stats['model_counts'][ext] = count
            
        except Exception as e:
            logger.error(f"Statistical model information failed: {e}")
        
        return stats
    
    def _get_directory_size(self, directory: Path) -> int:
        """
        Calculate directory size（byte）
        
        Args:
            directory: directory path
            
        Returns:
            Directory size（byte）
        """
        total = 0
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total += file_path.stat().st_size
        except Exception as e:
            logger.warning(f"Calculating directory size failed {directory}: {e}")
        
        return total
    
    def clean_unused_models(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up unused model files
        
        Args:
            dry_run: Whether to just preview without actually deleting
            
        Returns:
            Clean result information
        """
        result = {
            'files_to_remove': [],
            'space_to_free_mb': 0,
            'dry_run': dry_run,
            'removed_files': []
        }
        
        try:
            # Find possible duplicate or outdated files
            # Specific cleanup logic can be added here
            
            # Example：Find empty directories
            for directory in self.models_root.rglob("*"):
                if directory.is_dir() and not any(directory.iterdir()):
                    result['files_to_remove'].append({
                        'path': str(directory),
                        'type': 'empty_directory',
                        'size_mb': 0
                    })
            
            if not dry_run:
                # actually perform the cleanup
                for item in result['files_to_remove']:
                    path = Path(item['path'])
                    if path.exists():
                        if path.is_dir():
                            path.rmdir()
                        else:
                            path.unlink()
                        result['removed_files'].append(item['path'])
                        logger.info(f"Deleted: {path}")
            
        except Exception as e:
            logger.error(f"Cleaning model file failed: {e}")
        
        return result

# Global model manager instance
_model_manager = None

def get_model_manager() -> ModelManager:
    """Get global model manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager

def setup_model_environment():
    """Set up the model environment（Called when the app starts）"""
    manager = get_model_manager()
    logger.info("Model environment setup completed")
    return manager

"""
线程安全的人脸识别服务单例
为多线程部署优化，共享模型实例和缓存
"""
import threading
import logging
from typing import Dict, Any, Optional
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.advanced_face_service import AdvancedFaceRecognitionService

logger = logging.getLogger(__name__)


class ThreadSafeFaceService:
    """
    线程安全的人脸识别服务单例
    
    特性:
    - 单例模式，进程内共享模型实例
    - 线程安全的缓存操作
    - 避免模型重复加载
    - 适用于多线程部署
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # 初始化线程锁
        self._cache_lock = threading.RLock()  # 支持重入锁
        self._service_lock = threading.RLock()
        
        # 初始化核心服务
        with self._service_lock:
            self._service = AdvancedFaceRecognitionService()
            
        logger.info("线程安全人脸识别服务初始化完成")
        self._initialized = True
    
    def detect_faces(self, image, **kwargs):
        """线程安全的人脸检测"""
        with self._service_lock:
            return self._service.detect_faces(image, **kwargs)
    
    def enroll_person(self, name: str, image_path: str, description: Optional[str] = None, 
                     original_filename: Optional[str] = None) -> Dict[str, Any]:
        """线程安全的人员入库"""
        with self._service_lock:
            with self._cache_lock:
                return self._service.enroll_person(name, image_path, description, original_filename)
    
    def recognize_face(self, image, **kwargs) -> Dict[str, Any]:
        """线程安全的人脸识别"""
        with self._cache_lock:
            return self._service.recognize_face(image, **kwargs)
    
    def analyze_face_attributes(self, image, **kwargs) -> list:
        """线程安全的人脸属性分析"""
        with self._service_lock:
            return self._service.analyze_face_attributes(image, **kwargs)
    
    def get_statistics(self) -> Dict[str, Any]:
        """线程安全的统计信息获取"""
        with self._cache_lock:
            return self._service.get_statistics()
    
    def get_all_persons(self) -> list:
        """线程安全的获取所有人员"""
        with self._cache_lock:
            return self._service.db_manager.get_all_persons()
    
    def recognize_face_with_threshold(self, image, threshold: float = 0.25) -> Dict[str, Any]:
        """线程安全的带阈值人脸识别"""
        with self._cache_lock:
            return self._service.recognize_face_with_threshold(image, threshold)
    
    def visualize_face_detection(self, image_path: str) -> Dict[str, Any]:
        """线程安全的人脸检测可视化"""
        with self._service_lock:
            return self._service.visualize_face_detection(image_path)
    
    @property
    def _face_cache(self) -> Dict[str, Any]:
        """线程安全的缓存访问"""
        with self._cache_lock:
            return self._service._face_cache


# 全局单例实例
_thread_safe_service = None
_service_init_lock = threading.Lock()


def get_thread_safe_face_service() -> ThreadSafeFaceService:
    """
    获取线程安全的人脸识别服务实例
    
    Returns:
        ThreadSafeFaceService: 线程安全的人脸识别服务单例
    """
    global _thread_safe_service
    
    if _thread_safe_service is None:
        with _service_init_lock:
            if _thread_safe_service is None:
                _thread_safe_service = ThreadSafeFaceService()
    
    return _thread_safe_service

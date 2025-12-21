"""
Thread-safe face recognition service singleton
Optimized for multi-threaded deployments，Sharing model instances and caches
"""
import threading
import logging
from typing import Dict, Any, Optional
import sys
import os
from pathlib import Path

# Add the project root directory toPythonpath
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.advanced_face_service import AdvancedFaceRecognitionService

logger = logging.getLogger(__name__)


class ThreadSafeFaceService:
    """
    Thread-safe face recognition service singleton
    
    characteristic:
    - Singleton pattern，In-process shared model instance
    - Thread-safe cache operations
    - Avoid repeated loading of models
    - Suitable for multi-threaded deployment
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
            
        # Initialize thread lock
        self._cache_lock = threading.RLock()  # Support reentrancy lock
        self._service_lock = threading.RLock()
        
        # Initialize core services
        with self._service_lock:
            self._service = AdvancedFaceRecognitionService()
            
        logger.info("Thread-safe face recognition service initialization completed")
        self._initialized = True
    
    def detect_faces(self, image, **kwargs):
        """Thread-safe face detection"""
        with self._service_lock:
            return self._service.detect_faces(image, **kwargs)
    
    def enroll_person(self, name: str, image_path: str, region: str, emp_id: str, emp_rank: str, 
                     description: Optional[str] = None, original_filename: Optional[str] = None, 
                     client_id: Optional[str] = None) -> Dict[str, Any]:
        """Thread-safe personnel warehousing"""
        with self._service_lock:
            with self._cache_lock:
                return self._service.enroll_person(name, image_path, region, emp_id, emp_rank, description, original_filename, client_id)
    
    def recognize_face(self, image, **kwargs) -> Dict[str, Any]:
        """Thread-safe face recognition"""
        with self._cache_lock:
            return self._service.recognize_face(image, **kwargs)
    
    def analyze_face_attributes(self, image, **kwargs) -> list:
        """Thread-safe face attribute analysis"""
        with self._service_lock:
            return self._service.analyze_face_attributes(image, **kwargs)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Thread-safe statistics acquisition"""
        with self._cache_lock:
            return self._service.get_statistics()
    
    def get_all_persons(self, region: Optional[str] = None, client_id: Optional[str] = None) -> list:
        """Thread-safe retrieval of all persons"""
        with self._cache_lock:
            return self._service.db_manager.get_all_persons(region=region, client_id=client_id)
    
    def recognize_face_with_threshold(self, image, region: str, threshold: float = 0.25, emp_id: Optional[str] = None, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Thread-safe face recognition with threshold"""
        with self._cache_lock:
            return self._service.recognize_face_with_threshold(image, region, threshold, emp_id, client_id)
    
    def visualize_face_detection(self, image_path: str) -> Dict[str, Any]:
        """Thread-safe face detection visualization"""
        with self._service_lock:
            return self._service.visualize_face_detection(image_path)
    
    @property
    def db_manager(self):
        """Access to database manager"""
        return self._service.db_manager


# Global singleton instance
_thread_safe_service = None
_service_init_lock = threading.Lock()


def get_thread_safe_face_service() -> ThreadSafeFaceService:
    """
    Get a thread-safe face recognition service instance
    
    Returns:
        ThreadSafeFaceService: Thread-safe face recognition service singleton
    """
    global _thread_safe_service
    
    if _thread_safe_service is None:
        with _service_init_lock:
            if _thread_safe_service is None:
                _thread_safe_service = ThreadSafeFaceService()
    
    return _thread_safe_service

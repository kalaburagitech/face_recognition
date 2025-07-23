"""
基于 InsightFace 和 DeepFace 的先进人脸识别服务
采用最新的深度学习技术，提供更高的准确率和性能
"""
import os
import cv2
import numpy as np
import logging
from typing import List, Tuple, Dict, Any, Optional, Union
from datetime import datetime
import sys
import base64

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.enhanced_visualization import EnhancedFaceVisualizer
import pickle
import base64
from pathlib import Path

# 先进的人脸识别库
import insightface
from deepface import DeepFace
import onnxruntime

# 本地模块
from ..models.database import DatabaseManager, Person, FaceEncoding
from ..utils.config import config

logger = logging.getLogger(__name__)

class AdvancedFaceRecognitionService:
    """
    先进的人脸识别服务
    
    特性:
    - 使用 InsightFace 进行高精度人脸检测和特征提取
    - 支持多种预训练模型 (ArcFace, CosFace, SphereFace)
    - DeepFace 作为备选方案，支持多种后端
    - 更高的识别准确率 (99.83% on LFW)
    - 更快的推理速度
    - 支持年龄、性别、情绪等属性分析
    """
    
    def __init__(self, model_name: str = 'buffalo_l'):
        """
        初始化先进人脸识别服务
        
        Args:
            model_name: InsightFace 模型名称
                - buffalo_l: 大型模型，最高精度
                - buffalo_m: 中型模型，平衡精度和速度
                - buffalo_s: 小型模型，最快速度
        """
        self.db_manager = DatabaseManager()
        self.model_name = model_name
        
        # 初始化增强可视化器
        self.visualizer = EnhancedFaceVisualizer()
        
        # 初始化 InsightFace
        self._init_insightface()
        
        # 设置 DeepFace 配置
        self._init_deepface()
        
        # 人脸特征缓存
        self._face_cache = {}
        self._load_face_cache()
        
        logger.info(f"先进人脸识别服务初始化完成，使用模型: {model_name}")
    
    def _init_insightface(self):
        """初始化 InsightFace"""
        try:
            # 设置模型路径
            model_path = Path("models/insightface")
            model_path.mkdir(parents=True, exist_ok=True)
            
            # 初始化应用
            self.app = insightface.app.FaceAnalysis(
                name=self.model_name,
                root=str(model_path),
                providers=['CPUExecutionProvider']  # 使用 CPU，GPU 可改为 CUDAExecutionProvider
            )
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            
            logger.info("InsightFace 初始化成功")
            
        except Exception as e:
            logger.error(f"InsightFace 初始化失败: {str(e)}")
            self.app = None
    
    def _init_deepface(self):
        """初始化 DeepFace 配置"""
        self.deepface_models = [
            'ArcFace',      # 最新的 ArcFace 模型
            'Facenet512',   # 高维特征 FaceNet
            'VGG-Face',     # 经典 VGG-Face
            'OpenFace',     # 轻量级模型
        ]
        self.current_deepface_model = 'ArcFace'
        
        logger.info("DeepFace 配置完成")
    
    def detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        高精度人脸检测
        
        Args:
            image: 输入图像 (BGR 格式)
            
        Returns:
            检测到的人脸信息列表，包含位置、关键点、质量评分等
        """
        faces = []
        
        try:
            if self.app:
                # 使用 InsightFace 检测
                results = self.app.get(image)
                
                for face in results:
                    face_info = {
                        'bbox': face.bbox.astype(int).tolist(),  # [x1, y1, x2, y2]
                        'landmarks': face.kps.astype(int).tolist(),  # 5个关键点
                        'det_score': float(face.det_score),  # 检测置信度
                        'embedding': face.embedding,  # 512维特征向量
                        'age': getattr(face, 'age', None),
                        'gender': getattr(face, 'gender', None),
                        'quality': self._calculate_face_quality(face)
                    }
                    faces.append(face_info)
            
            else:
                # 备选方案：使用 OpenCV 检测
                faces = self._detect_faces_opencv(image)
            
            logger.info(f"检测到 {len(faces)} 个人脸")
            return faces
            
        except Exception as e:
            logger.error(f"人脸检测失败: {str(e)}")
            return []
    
    def _detect_faces_opencv(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """使用 OpenCV 进行人脸检测（备选方案）"""
        try:
            # 加载 Haar 级联分类器
            cascade_path = os.path.join(cv2.__path__[0], 'data', 'haarcascade_frontalface_default.xml')
            if not os.path.exists(cascade_path):
                # 使用默认路径
                cascade_path = 'haarcascade_frontalface_default.xml'
            
            face_cascade = cv2.CascadeClassifier(cascade_path)
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces_cv = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
        except Exception as e:
            logger.warning(f"OpenCV人脸检测失败: {e}")
            return []
        
        faces = []
        for (x, y, w, h) in faces_cv:
            face_info = {
                'bbox': [x, y, x+w, y+h],
                'landmarks': None,
                'det_score': 0.8,  # 假设的置信度
                'embedding': None,
                'age': None,
                'gender': None,
                'quality': 0.7
            }
            faces.append(face_info)
        
        return faces
    
    def _calculate_face_quality(self, face) -> float:
        """计算人脸质量评分"""
        quality_score = 1.0
        
        # 基于检测置信度
        quality_score *= face.det_score
        
        # 基于人脸大小（面积）
        bbox = face.bbox
        face_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        if face_area < 2500:  # 50x50 像素
            quality_score *= 0.5
        elif face_area < 10000:  # 100x100 像素
            quality_score *= 0.8
        
        return float(quality_score)
    
    def extract_features(self, image: np.ndarray, face_info: Dict[str, Any]) -> Optional[np.ndarray]:
        """
        提取人脸特征向量
        
        Args:
            image: 原始图像
            face_info: 人脸信息（包含边界框）
            
        Returns:
            512维特征向量，如果提取失败返回 None
        """
        try:
            if face_info.get('embedding') is not None:
                # 如果已经有特征向量，直接返回
                return face_info['embedding']
            
            # 裁剪人脸区域
            bbox = face_info['bbox']
            face_crop = image[bbox[1]:bbox[3], bbox[0]:bbox[2]]
            
            if face_crop.size == 0:
                return None
            
            # 使用 DeepFace 提取特征
            try:
                embedding = DeepFace.represent(
                    img_path=face_crop,
                    model_name=self.current_deepface_model,
                    enforce_detection=False
                )[0]['embedding']
                
                return np.array(embedding, dtype=np.float32)
                
            except Exception as e:
                logger.warning(f"DeepFace 特征提取失败: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"特征提取失败: {str(e)}")
            return None
    
    def enroll_person(self, name: str, image_path: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        高精度人员入库
        
        Args:
            name: 人员姓名
            image_path: 图像路径
            description: 人员描述
            
        Returns:
            入库结果信息
        """
        try:
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                return {'success': False, 'error': '无法读取图像文件'}
            
            # 检测人脸
            faces = self.detect_faces(image)
            
            if not faces:
                return {'success': False, 'error': '未检测到人脸'}
            
            if len(faces) > 1:
                return {'success': False, 'error': '检测到多个人脸，请使用只包含一个人脸的图像'}
            
            face = faces[0]
            
            # 质量检查
            if face['quality'] < 0.5:
                return {'success': False, 'error': '人脸质量不足，请使用更清晰的图像'}
            
            # 提取特征
            features = self.extract_features(image, face)
            if features is None:
                return {'success': False, 'error': '特征提取失败'}
            
            # 检查是否已存在相似人脸
            duplicate_threshold_value = config.get('face_recognition.duplicate_threshold', 0.95)
            if isinstance(duplicate_threshold_value, (int, float)):
                duplicate_threshold = float(duplicate_threshold_value)
            else:
                duplicate_threshold = 0.95  # 默认值
                
            existing_match = self.recognize_face(image)
            if existing_match['matches']:
                best_match = existing_match['matches'][0]
                # 将相似度阈值转换为百分比进行比较
                similarity_threshold_percent = duplicate_threshold * 100
                if best_match['match_score'] > similarity_threshold_percent:
                    return {
                        'success': False, 
                        'error': f'相似人脸已存在：{best_match["name"]} (匹配度: {best_match["match_score"]:.1f}%，阈值: {similarity_threshold_percent:.1f}%)'
                    }
            
            # 保存到数据库
            try:
                # 检查同名人员是否已存在
                existing_person = self.db_manager.get_person_by_name(name)
                
                if existing_person:
                    # 同名人员已存在，为其添加新的人脸特征
                    person_id = existing_person.id
                    logger.info(f"为现有人员 {name} (ID: {person_id}) 添加新的人脸特征")
                else:
                    # 创建新人员记录
                    person = self.db_manager.create_person(name, description)
                    person_id = person.id
                    logger.info(f"创建新人员: {name} (ID: {person_id})")
                
                # 读取图片二进制数据
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                # 保存特征向量和图片数据
                bbox = face['bbox']
                face_bbox_str = f"[{int(bbox[0])},{int(bbox[1])},{int(bbox[2])},{int(bbox[3])}]"
                
                face_encoding = self.db_manager.add_face_encoding(
                    person_id=person_id,
                    encoding=features,
                    image_path=image_path,
                    image_data=image_data,
                    face_bbox=face_bbox_str,
                    confidence=face['quality'],
                    quality_score=face['quality']
                )
                
                # 更新缓存
                if person_id not in self._face_cache:
                    self._face_cache[person_id] = {
                        'name': name,
                        'embeddings': [],
                        'model': f"advanced_{self.model_name}"
                    }
                
                self._face_cache[person_id]['embeddings'].append(features)
                
                logger.info(f"成功入库人脸特征: {name} (人员ID: {person_id}, 特征ID: {face_encoding.id})")
                
                return {
                    'success': True,
                    'person_id': person_id,
                    'face_encoding_id': face_encoding.id,
                    'quality_score': face['quality'],
                    'feature_dim': len(features),
                    'faces_detected': 1
                }
            except Exception as db_error:
                logger.error(f"数据库操作失败: {str(db_error)}")
                return {'success': False, 'error': f'数据库保存失败: {str(db_error)}'}
        
        except Exception as e:
            logger.error(f"人员入库失败: {str(e)}")
            return {'success': False, 'error': f'入库失败: {str(e)}'}
    
    def recognize_face(self, image: Union[np.ndarray, str]) -> Dict[str, Any]:
        """
        高精度人脸识别
        
        Args:
            image: 图像数组或图像路径
            
        Returns:
            识别结果，包含匹配的人员信息和置信度
        """
        try:
            # 处理输入图像
            if isinstance(image, str):
                img = cv2.imread(image)
            else:
                img = image.copy()
            
            if img is None:
                return {'success': False, 'matches': [], 'error': '无法读取图像'}
            
            # 检测人脸
            faces = self.detect_faces(img)
            
            if not faces:
                return {'success': True, 'matches': [], 'message': '未检测到人脸'}
            
            all_matches = []
            
            for i, face in enumerate(faces):
                # 提取特征
                features = self.extract_features(img, face)
                if features is None:
                    continue
                
                # 与数据库中的特征比较
                matches = self._match_features(features)
                
                # 添加人脸位置信息
                for match in matches:
                    match['face_index'] = i
                    match['bbox'] = face['bbox']
                    match['quality'] = face['quality']
                
                all_matches.extend(matches)
            
            # 按匹配度排序
            all_matches.sort(key=lambda x: x['match_score'], reverse=True)
            
            return {
                'success': True,
                'matches': all_matches,
                'total_faces': len(faces)
            }
        
        except Exception as e:
            logger.error(f"人脸识别失败: {str(e)}")
            return {'success': False, 'matches': [], 'error': f'识别失败: {str(e)}'}
    
    def _match_features(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """
        特征匹配
        
        Args:
            features: 待匹配的特征向量
            
        Returns:
            匹配结果列表
        """
        matches = []
        threshold = getattr(config, 'RECOGNITION_THRESHOLD', 0.6)
        
        try:
            for person_id, cached_data in self._face_cache.items():
                cached_embeddings = cached_data['embeddings']
                
                # 遍历该人员的所有特征向量
                for cached_features in cached_embeddings:
                    # 计算余弦相似度 (范围: -1 到 1, 越接近1越相似)
                    similarity = self._cosine_similarity(features, cached_features)
                    
                    # 计算欧氏距离 (范围: 0到无穷, 越小越相似)
                    distance = np.linalg.norm(features - cached_features)
                    
                    # 将相似度转换为百分比形式的匹配度
                    # 对于人脸特征，余弦相似度通常在0.3-1.0之间，直接转换为百分比
                    match_score = max(0, similarity) * 100  # 确保非负并转换为0-100%
                    
                    # 使用相似度作为判断标准
                    if similarity > threshold:
                        matches.append({
                            'person_id': person_id,
                            'name': cached_data['name'],
                            'match_score': float(match_score),  # 匹配度百分比
                            'distance': float(distance),        # 欧氏距离
                            'model': cached_data['model']
                        })
            
            # 按匹配度排序
            matches.sort(key=lambda x: x['match_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"特征匹配失败: {str(e)}")
        
        return matches
    
    def _cosine_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """计算余弦相似度"""
        # 归一化
        features1_norm = features1 / np.linalg.norm(features1)
        features2_norm = features2 / np.linalg.norm(features2)
        
        # 计算余弦相似度
        similarity = np.dot(features1_norm, features2_norm)
        
        return float(similarity)
    
    def _load_face_cache(self):
        """从数据库加载人脸特征缓存"""
        try:
            with self.db_manager.get_session() as session:
                # 查询所有编码和对应的人员信息
                encodings = session.query(FaceEncoding, Person).join(Person, FaceEncoding.person_id == Person.id).all()
                
                for encoding, person in encodings:
                    features = encoding.get_encoding()
                    
                    if person.id not in self._face_cache:
                        self._face_cache[person.id] = {
                            'name': person.name,
                            'embeddings': [],  # 初始化为空列表
                            'model': 'advanced_buffalo_l'
                        }
                    
                    # 将特征向量添加到列表中
                    self._face_cache[person.id]['embeddings'].append(features)
                
                logger.info(f"加载了 {len(self._face_cache)} 个人员的人脸特征缓存")
        
        except Exception as e:
            logger.error(f"加载人脸缓存失败: {str(e)}")
    
    def analyze_face_attributes(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        分析人脸属性（年龄、性别、情绪等）
        
        Args:
            image: 输入图像
            
        Returns:
            人脸属性分析结果
        """
        try:
            results = []
            
            # 检测人脸
            faces = self.detect_faces(image)
            
            for face in faces:
                bbox = face['bbox']
                face_crop = image[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                
                if face_crop.size == 0:
                    continue
                
                try:
                    # 使用 DeepFace 分析属性
                    analysis = DeepFace.analyze(
                        img_path=face_crop,
                        actions=['age', 'gender', 'emotion', 'race'],
                        enforce_detection=False
                    )[0]
                    
                    attributes = {
                        'bbox': bbox,
                        'age': analysis.get('age'),
                        'gender': analysis.get('dominant_gender'),
                        'gender_confidence': analysis.get('gender', {}).get(analysis.get('dominant_gender', ''), 0),
                        'emotion': analysis.get('dominant_emotion'),
                        'emotion_scores': analysis.get('emotion', {}),
                        'race': analysis.get('dominant_race'),
                        'race_scores': analysis.get('race', {})
                    }
                    
                    results.append(attributes)
                    
                except Exception as e:
                    logger.warning(f"属性分析失败: {str(e)}")
                    continue
            
            return results
        
        except Exception as e:
            logger.error(f"人脸属性分析失败: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            with self.db_manager.get_session() as session:
                total_persons = session.query(Person).count()
                total_encodings = session.query(FaceEncoding).count()
                
                # 获取最近7天的人员统计
                from datetime import timedelta
                recent_date = datetime.now() - timedelta(days=7)
                recent_persons = session.query(Person).filter(Person.created_at >= recent_date).count()
                
                return {
                    'total_persons': total_persons,
                    'total_encodings': total_encodings,
                    'recent_persons': recent_persons,
                    'cache_size': len(self._face_cache),
                    'current_model': f"InsightFace_{self.model_name}",
                    'deepface_model': self.current_deepface_model,
                    'supported_models': self.deepface_models,
                    'recognition_threshold': config.RECOGNITION_THRESHOLD
                }
        
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}

    def recognize_face_with_threshold(self, image: np.ndarray, threshold: float = 0.6) -> Dict[str, Any]:
        """
        使用自定义阈值进行人脸识别
        
        Args:
            image: 输入图像
            threshold: 识别阈值
            
        Returns:
            识别结果字典
        """
        try:
            start_time = datetime.now()
            
            # 检测人脸
            faces = self.detect_faces(image)
            logger.info(f"检测到 {len(faces)} 个人脸")
            
            if not faces:
                return {
                    'success': True,
                    'matches': [],
                    'total_faces': 0,
                    'message': '未检测到人脸'
                }

            matches = []
            
            # 对每个检测到的人脸进行识别
            for face in faces:
                bbox = face['bbox']
                face_embedding = face.get('embedding')
                
                if face_embedding is None:
                    continue
                
                # 在已知人脸中查找匹配
                best_match = None
                best_similarity = 0
                
                for person_id, cached_data in self._face_cache.items():
                    for cached_embedding in cached_data['embeddings']:
                        # 计算余弦相似度
                        similarity = float(np.dot(face_embedding, cached_embedding) / 
                                         (np.linalg.norm(face_embedding) * np.linalg.norm(cached_embedding)))
                        
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = {
                                'person_id': person_id,
                                'name': cached_data['name'],
                                'match_score': similarity * 100,  # 转换为百分比
                                'distance': 1 - similarity,
                                'model': f"InsightFace_{self.model_name}",
                                'bbox': bbox,
                                'quality': face.get('det_score', 0.9)
                            }
                
                # 只返回超过阈值的匹配
                if best_match and best_similarity >= threshold:
                    matches.append(best_match)
                else:
                    # 添加未识别的人脸信息
                    matches.append({
                        'person_id': -1,
                        'name': '未知人员',
                        'match_score': (best_similarity if best_match else 0.0) * 100,  # 转换为百分比
                        'distance': 1 - (best_similarity if best_match else 0.0),
                        'model': f"InsightFace_{self.model_name}",
                        'bbox': bbox,
                        'quality': face.get('det_score', 0.9)
                    })
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'matches': matches,
                'total_faces': len(faces),
                'processing_time': processing_time,
                'threshold_used': threshold,
                'message': f'识别完成，检测到 {len(faces)} 个人脸，识别出 {len([m for m in matches if m["person_id"] != -1])} 个已知人员'
            }
            
        except Exception as e:
            logger.error(f"人脸识别失败: {str(e)}")
            return {
                'success': False,
                'matches': [],
                'total_faces': 0,
                'error': str(e)
            }
    
    def visualize_face_detection(self, image_path: str) -> Dict[str, Any]:
        """
        生成人脸检测可视化图像（使用增强可视化器）
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            Dict: 包含可视化结果的字典
        """
        try:
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                return {
                    'success': False,
                    'error': '无法读取图像文件'
                }
            
            # 检测人脸
            faces_data = []
            if self.app:
                faces = self.app.get(image)
                for i, face in enumerate(faces):
                    bbox = face.bbox.astype(int)
                    face_info = {
                        'bbox': bbox.tolist(),
                        'quality': float(face.det_score),
                        'det_score': float(face.det_score),
                        'name': f'人脸 {i+1}'
                    }
                    faces_data.append(face_info)
            
            # 使用增强可视化器生成图像
            result = self.visualizer.visualize_face_detection(image, faces_data)
            
            if result['success']:
                return {
                    'success': True,
                    'image_base64': result['image_base64'],
                    'faces': result['face_details'],
                    'total_faces': result['total_faces'],
                    'message': f'检测到 {result["total_faces"]} 个人脸'
                }
            else:
                return result
            
        except Exception as e:
            logger.error(f"人脸检测可视化失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# 全局服务实例
advanced_face_service = None

def get_advanced_face_service() -> AdvancedFaceRecognitionService:
    """获取先进人脸识别服务实例"""
    global advanced_face_service
    if advanced_face_service is None:
        advanced_face_service = AdvancedFaceRecognitionService()
    return advanced_face_service

"""
based on InsightFace and DeepFace Advanced facial recognition services
Using the latest deep learning technology，Provides higher accuracy and performance
"""
import os
import cv2
import numpy as np
import logging
from typing import List, Tuple, Dict, Any, Optional, Union
from datetime import datetime
import sys
import base64

# Add the project root directory toPythonpath
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.enhanced_visualization import EnhancedFaceVisualizer
import pickle
import base64
from pathlib import Path

# Advanced face recognition library
import insightface
from deepface import DeepFace
import onnxruntime

# local module
from ..models.database import DatabaseManager, Person, FaceEncoding
from ..utils.config import config
from ..utils.model_manager import get_model_manager

logger = logging.getLogger(__name__)

class AdvancedFaceRecognitionService:
    """
    Advanced facial recognition service
    
    characteristic:
    - use InsightFace Perform high-precision face detection and feature extraction
    - Supports multiple pre-trained models (ArcFace, CosFace, SphereFace)
    - DeepFace as an alternative，Supports multiple backends
    - Higher recognition accuracy (99.83% on LFW)
    - Faster inference speed
    - Support age、gender、Analysis of attributes such as emotions
    """
    
    def __init__(self, model_name: str = 'buffalo_l'):
        """
        Initialize advanced face recognition service
        
        Args:
            model_name: InsightFace Model name
                - buffalo_l: large model，Highest accuracy
                - buffalo_m: medium model，Balancing precision and speed
                - buffalo_s: small model，fastest speed
        """
        # Initialize model manager
        self.model_manager = get_model_manager()
        
        self.db_manager = DatabaseManager()
        self.model_name = model_name
        
        # Initialize the enhanced visualizer
        self.visualizer = EnhancedFaceVisualizer()
        
        # initialization InsightFace
        self._init_insightface()
        
        # set up DeepFace Configuration
        self._init_deepface()
        
        # PostgreSQL + pgvector handles all caching and search
        logger.info("📝 Using PostgreSQL + pgvector for face search")
        
        logger.info(f"Advanced face recognition service initialization completed，Use model: {model_name}")
    
    def _init_insightface(self):
        """initialization InsightFace"""
        try:
            # Configure using the model manager InsightFace path
            model_root = self.model_manager.configure_insightface(self.model_name)
            
            # Initialize application
            self.app = insightface.app.FaceAnalysis(
                name=self.model_name,
                root=model_root,
                providers=['CPUExecutionProvider']  # use CPU，GPU Can be changed to CUDAExecutionProvider
            )
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            
            logger.info(f"InsightFace Initialization successful，model path: {model_root}")
            
        except Exception as e:
            logger.error(f"InsightFace Initialization failed: {str(e)}")
            self.app = None
    
    def _init_deepface(self):
        """initialization DeepFace Configuration"""
        # Configuration DeepFace model path
        deepface_config = self.model_manager.configure_deepface()
        logger.info(f"DeepFace Configuration path: {deepface_config['deepface_home']}")
        
        self.deepface_models = [
            'ArcFace',      # latest ArcFace Model
            'Facenet512',   # High dimensional features FaceNet
            'VGG-Face',     # classic VGG-Face
            'OpenFace',     # lightweight model
        ]
        self.current_deepface_model = 'ArcFace'
        
        logger.info("DeepFace Configuration completed")
    
    def detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        High-precision face detection
        
        Args:
            image: input image (BGR Format)
            
        Returns:
            List of detected face information，Contains location、Key points、Quality score and more
        """
        faces = []
        
        # Get face detection threshold
        detection_threshold = getattr(config, 'DETECTION_THRESHOLD', 0.5)
        
        try:
            if self.app:
                # use InsightFace Detection
                results = self.app.get(image)
                
                for face in results:
                    # Apply detection threshold filtering
                    if face.det_score < detection_threshold:
                        logger.debug(f"Face detection confidence is too low: {face.det_score:.3f} < {detection_threshold}")
                        continue
                        
                    face_info = {
                        'bbox': face.bbox.astype(int).tolist(),  # [x1, y1, x2, y2]
                        'landmarks': face.kps.astype(int).tolist(),  # 5key points
                        'det_score': float(face.det_score),  # Detection confidence
                        'embedding': face.embedding,  # 512dimensional eigenvector
                        'age': getattr(face, 'age', None),
                        'gender': getattr(face, 'gender', None),
                        'quality': self._calculate_face_quality(face)
                    }
                    faces.append(face_info)
            
            else:
                # Alternatives：use OpenCV Detection
                faces = self._detect_faces_opencv(image)
            
            logger.info(f"detected {len(faces)} personal face")
            return faces
            
        except Exception as e:
            logger.error(f"Face detection failed: {str(e)}")
            return []
    
    def _detect_faces_opencv(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """use OpenCV Perform face detection（Alternatives）"""
        try:
            # load Haar Cascade classifier
            cascade_path = os.path.join(cv2.__path__[0], 'data', 'haarcascade_frontalface_default.xml')
            if not os.path.exists(cascade_path):
                # Use default path
                cascade_path = 'haarcascade_frontalface_default.xml'
            
            face_cascade = cv2.CascadeClassifier(cascade_path)
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces_cv = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
        except Exception as e:
            logger.warning(f"OpenCVFace detection failed: {e}")
            return []
        
        faces = []
        for (x, y, w, h) in faces_cv:
            face_info = {
                'bbox': [x, y, x+w, y+h],
                'landmarks': None,
                'det_score': 0.8,  # Hypothesis confidence
                'embedding': None,
                'age': None,
                'gender': None,
                'quality': 0.7
            }
            faces.append(face_info)
        
        return faces
    
    def _calculate_face_quality(self, face) -> float:
        """Calculate face quality score"""
        quality_score = 1.0
        
        # Based on detection confidence
        quality_score *= face.det_score
        
        # Based on face size（area）
        bbox = face.bbox
        face_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        if face_area < 2500:  # 50x50 Pixel
            quality_score *= 0.5
        elif face_area < 10000:  # 100x100 Pixel
            quality_score *= 0.8
        
        return float(quality_score)
    
    def extract_features(self, image: np.ndarray, face_info: Dict[str, Any]) -> Optional[np.ndarray]:
        """
        Extract facial feature vector
        
        Args:
            image: original image
            face_info: Face information（Contains bounding box）
            
        Returns:
            512dimensional eigenvector，If the extraction fails return None
        """
        try:
            if face_info.get('embedding') is not None:
                # If there is already a feature vector，Return directly
                return face_info['embedding']
            
            # Crop face area
            bbox = face_info['bbox']
            face_crop = image[bbox[1]:bbox[3], bbox[0]:bbox[2]]
            
            if face_crop.size == 0:
                return None
            
            # use DeepFace Extract features
            try:
                embedding = DeepFace.represent(
                    img_path=face_crop,
                    model_name=self.current_deepface_model,
                    enforce_detection=False
                )[0]['embedding']
                
                return np.array(embedding, dtype=np.float32)
                
            except Exception as e:
                logger.warning(f"DeepFace Feature extraction failed: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            return None
    
    def enroll_person(self, name: str, image_path: str, region: str, emp_id: str, emp_rank: str, description: Optional[str] = None, original_filename: Optional[str] = None, client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        High-precision personnel warehousing
        
        Args:
            name: Personnel name
            image_path: image path（Temporary file path）
            region: Region (ka/ap/tn)
            emp_id: Employee ID
            emp_rank: Employee Rank
            description: Personnel description
            original_filename: original file name（for database storage）
            
        Returns:
            Storage result information
        """
        try:
            # read image
            image = cv2.imread(image_path)
            if image is None:
                return {'success': False, 'error': 'Unable to read image file'}
            
            # Detect faces
            faces = self.detect_faces(image)
            
            if not faces:
                return {'success': False, 'error': 'No face detected'}
            
            if len(faces) > 1:
                return {'success': False, 'error': 'Multiple faces detected，Please use an image containing only one face'}
            
            face = faces[0]
            
            # Quality check
            if face['quality'] < 0.5:
                return {'success': False, 'error': 'Insufficient face quality，Please use a clearer image'}
            
            # Extract features
            features = self.extract_features(image, face)
            if features is None:
                return {'success': False, 'error': 'Feature extraction failed'}
            
            # Check if similar faces already exist（Enhanced duplicate detection logic）
            duplicate_check = self._check_duplicate_faces(features, name)
            if not duplicate_check['success']:
                return duplicate_check  # Returns the result of duplicate detection failure
            
            # Save to database
            try:
                # Check if a person with the same name already exists
                existing_person = self.db_manager.get_person_by_name(name, region=region, client_id=client_id)
                
                if existing_person:
                    # A person with the same name already exists，Add new facial features to it
                    person_id = getattr(existing_person, "id", None)
                    if not isinstance(person_id, int):
                        logger.error(f"existing_person.id nointtype，Unable to store。actual type: {type(person_id)}")
                        return {'success': False, 'error': 'Database PersonnelIDabnormal，Unable to store'}
                    logger.info(f"for existing staff {name} (ID: {person_id}) Add new facial features")
                else:
                    # Create new person record with region, emp_id, and emp_rank
                    person = self.db_manager.create_person(name, region=region, emp_id=emp_id, emp_rank=emp_rank, description=description, client_id=client_id)
                    person_id = person.id
                    logger.info(f"Create new person: {name} in region {region} with emp_id {emp_id} and rank {emp_rank} (ID: {person_id})")
                
                # Read image binary data
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                # Save feature vectors and image data
                bbox = face['bbox']
                face_bbox_str = f"[{int(bbox[0])},{int(bbox[1])},{int(bbox[2])},{int(bbox[3])}]"
                
                # Use the original filename asimage_pathstorage，instead of a temporary path
                stored_image_path = original_filename if original_filename else os.path.basename(image_path)
                
                face_encoding = self.db_manager.add_face_encoding(
                    person_id=person_id,
                    encoding=features,
                    image_path=stored_image_path,  # Store original file name
                    image_data=image_data,
                    face_bbox=face_bbox_str,
                    confidence=face['quality'],
                    quality_score=face['quality']
                )
                
                # No cache needed - PostgreSQL handles everything
                
                logger.info(f"Successfully stored facial features: {name} (personnelID: {person_id}, featureID: {face_encoding.id})")
                
                return {
                    'success': True,
                    'person_id': person_id,
                    'face_encoding_id': face_encoding.id,
                    'quality_score': face['quality'],
                    'feature_dim': len(features),
                    'faces_detected': 1,
                    'face_encoding': features.tolist()  # Willnumpyarray converted toPythonlist
                }
            except Exception as db_error:
                logger.error(f"Database operation failed: {str(db_error)}")
                return {'success': False, 'error': f'Database save failed: {str(db_error)}'}
        
        except Exception as e:
            logger.error(f"Personnel entry failed: {str(e)}")
            return {'success': False, 'error': f'Storage failed: {str(e)}'}
    
    def enroll_person_no_duplicate_check(self, name: str, image_path: str, region: str, emp_id: str, emp_rank: str, description: Optional[str] = None, original_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Personnel warehousing（Skip duplicate detection）
        For bulk registration that has been pre-checked
        
        Args:
            name: Personnel name
            image_path: image path（Temporary file path）
            region: Region (ka/ap/tn)
            emp_id: Employee ID
            emp_rank: Employee Rank
            description: Personnel description
            original_filename: original file name（for database storage）
            
        Returns:
            Storage result information
        """
        try:
            # read image
            image = cv2.imread(image_path)
            if image is None:
                return {'success': False, 'error': 'Unable to read image file'}
            
            # Detect faces
            faces = self.detect_faces(image)
            
            if not faces:
                return {'success': False, 'error': 'No face detected'}
            
            if len(faces) > 1:
                return {'success': False, 'error': 'Multiple faces detected，Please use an image containing only one face'}
            
            face = faces[0]
            
            # Quality check
            if face['quality'] < 0.5:
                return {'success': False, 'error': 'Insufficient face quality，Please use a clearer image'}
            
            # Extract features
            features = self.extract_features(image, face)
            if features is None:
                return {'success': False, 'error': 'Feature extraction failed'}
            
            # Skip duplicate detection，Save directly to database
            try:
                # Check if a person with the same name already exists
                existing_person = self.db_manager.get_person_by_name(name)
                
                if existing_person:
                    # A person with the same name already exists，Add new facial features to it
                    person_id = getattr(existing_person, "id", None)
                    if not isinstance(person_id, int):
                        logger.error(f"existing_person.id nointtype，Unable to store。actual type: {type(person_id)}")
                        return {'success': False, 'error': 'Database PersonnelIDabnormal，Unable to store'}
                    logger.info(f"for existing staff {name} (ID: {person_id}) Add new facial features")
                else:
                    # Create new person record with region, emp_id, and emp_rank
                    person = self.db_manager.create_person(name, region=region, emp_id=emp_id, emp_rank=emp_rank, description=description)
                    person_id = person.id
                    logger.info(f"Create new person: {name} in region {region} with emp_id {emp_id} and rank {emp_rank} (ID: {person_id})")
                
                # Read image binary data
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                # Save feature vectors and image data
                bbox = face['bbox']
                face_bbox_str = f"[{int(bbox[0])},{int(bbox[1])},{int(bbox[2])},{int(bbox[3])}]"
                
                # Use the original filename asimage_pathstorage，instead of a temporary path
                stored_image_path = original_filename if original_filename else os.path.basename(image_path)
                
                face_encoding = self.db_manager.add_face_encoding(
                    person_id=person_id,
                    encoding=features,
                    image_path=stored_image_path,  # Store original file name
                    image_data=image_data,
                    face_bbox=face_bbox_str,
                    confidence=face['quality'],
                    quality_score=face['quality']
                )
                
                # No cache needed - PostgreSQL handles everything
                
                logger.info(f"Successfully stored facial features: {name} (personnelID: {person_id}, featureID: {face_encoding.id})")
                
                return {
                    'success': True,
                    'person_id': person_id,
                    'face_encoding_id': face_encoding.id,
                    'quality_score': face['quality'],
                    'feature_dim': len(features),
                    'faces_detected': 1,
                    'face_encoding': features.tolist()  # Willnumpyarray converted toPythonlist
                }
            except Exception as db_error:
                logger.error(f"Database operation failed: {str(db_error)}")
                return {'success': False, 'error': f'Database save failed: {str(db_error)}'}
        
        except Exception as e:
            logger.error(f"Personnel entry failed: {str(e)}")
            return {'success': False, 'error': f'Storage failed: {str(e)}'}
    
    def _check_duplicate_faces(self, features: np.ndarray, name: str, exclude_session_frames: List[np.ndarray] = None) -> Dict[str, Any]:
        """
        Strict duplicate face detection logic - Prevent the same face from being registered as different people
        
        Args:
            features: Current face feature vector
            name: Personnel name
            exclude_session_frames: Frame data within the same registration session that needs to be excluded（for video registration）
            
        Returns:
            Check results dictionary
        """
        try:
            # Get duplicate detection threshold - Use stricter thresholds to prevent duplication across people
            duplicate_threshold_value = config.get('face_recognition.duplicate_threshold', 0.60)
            if isinstance(duplicate_threshold_value, (int, float)):
                duplicate_threshold = float(duplicate_threshold_value)
            else:
                duplicate_threshold = 0.60  # Strict default threshold (60% similarity)

            similarity_threshold_percent = duplicate_threshold * 100
            logger.info(f"🔍 Starting duplicate face check - Name: '{name}', Threshold: {duplicate_threshold} ({similarity_threshold_percent}%)")

            # key changes：Check all faces in entire database，regardless of name
            # This ensures that the same face cannot be registered under different names
            try:
                with self.db_manager.get_session() as session:
                    from ..models import FaceEncoding as FaceEncodingModel
                    from ..models import Person
                    
                    # Get all face codes in the database
                    all_faces = session.query(FaceEncodingModel, Person).join(
                        Person, FaceEncodingModel.person_id == Person.id
                    ).all()
                    
                    logger.info(f"Checking against {len(all_faces)} registered faces in database")
                    
                    max_similarity = 0.0
                    most_similar_person = None
                    
                    for face_encoding, person in all_faces:
                        db_enc = face_encoding.embedding
                        if db_enc is None:
                            continue
                            
                        # Process encoded data
                        db_feature = self._parse_face_encoding(db_enc)
                        if db_feature is None:
                            logger.warning(f"Failed to parse encoding for person: {person.name}")
                            continue
                        
                        # Calculate similarity
                        similarity_result = self._calculate_enhanced_similarity(features, db_feature)
                        
                        # Track highest similarity for logging
                        if similarity_result['combined_score'] > max_similarity:
                            max_similarity = similarity_result['combined_score']
                            most_similar_person = person.name
                        
                        # Log each comparison for debugging
                        logger.debug(f"Comparing with {person.name}: {similarity_result['combined_score']:.2f}%")
                        
                        # Strict inspection：If the similarity exceeds the threshold，Reject regardless of whether the names are the same or not.
                        if similarity_result['combined_score'] > similarity_threshold_percent:
                            logger.warning(f"🚫 DUPLICATE DETECTED! New: '{name}' vs Existing: '{person.name}' | Similarity: {similarity_result['combined_score']:.2f}% (Threshold: {similarity_threshold_percent}%)")
                            
                            if person.name == name:
                                # Duplicate faces of people with the same name
                                return {
                                    'success': False,
                                    'error': f'Similar faces already exist for this person (Matching degree: {similarity_result["combined_score"]:.1f}%，threshold: {similarity_threshold_percent:.1f}%)'
                                }
                            else:
                                # Duplicate faces of different people - This is the key fix
                                return {
                                    'success': False,
                                    'error': f'This face has been registered as：{person.name}。The same face cannot be registered as different people。(Matching degree: {similarity_result["combined_score"]:.1f}%，threshold: {similarity_threshold_percent:.1f}%)'
                                }
                            
            except Exception as e:
                logger.error(f"Repeat check failed: {e}")
                # if check fails，for safety reasons，Deny registration
                return {
                    'success': False,
                    'error': 'Face repeatability check failed，For data security，Please try registration again'
                }
            
            # 3. If exclude frame data is provided，Check if it is too similar to other frames in the same session（Interframe check for video registration only）
            if exclude_session_frames:
                session_duplicate_threshold = 0.98  # Frames within the same session use a higher threshold
                session_threshold_percent = session_duplicate_threshold * 100
                
                for i, session_frame in enumerate(exclude_session_frames):
                    if session_frame is None:
                        continue
                        
                    similarity_result = self._calculate_enhanced_similarity(features, session_frame)
                    if similarity_result['combined_score'] > session_threshold_percent:
                        logger.info(f"Skip session frames{i+1}frames that are too similar，Similarity: {similarity_result['combined_score']:.2f}%")
                        return {
                            'success': False,
                            'skip_frame': True,  # Mark as skipped frame，instead of error
                            'similarity_score': similarity_result['combined_score']
                        }
            
            logger.info(f"✅ Duplicate check passed for '{name}' | Highest similarity: {max_similarity:.2f}% with '{most_similar_person}' (below threshold {similarity_threshold_percent}%)")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Duplicate detection failed: {str(e)}")
            # Deny registration when detection fails for security
            return {
                'success': False,
                'error': 'Face repeatability check failed，Please try registration again'
            }
    
    def _parse_face_encoding(self, db_enc) -> Optional[np.ndarray]:
        """
        Parse face encoding data in different formats
        
        Args:
            db_enc: Encoded data in database
            
        Returns:
            parsednumpyarray orNone
        """
        try:
            if isinstance(db_enc, bytes):
                return pickle.loads(db_enc)
            elif isinstance(db_enc, np.ndarray):
                return db_enc
            elif isinstance(db_enc, (list, tuple)):
                return np.array(db_enc, dtype=np.float32)
            else:
                logger.warning(f"Unknown encoding format: {type(db_enc)}")
                return None
        except Exception as e:
            logger.warning(f"Feature parsing failed: {e}")
            return None
    
    def _calculate_enhanced_similarity(self, features1: np.ndarray, features2: np.ndarray) -> Dict[str, float]:
        """
        Compute enhanced similarity，Combining cosine similarity and Euclidean distance
        Adapt to different lighting and angle changes
        
        Args:
            features1: first eigenvector
            features2: second eigenvector
            
        Returns:
            A dictionary containing various similarity metrics
        """
        try:
            # Make sure the feature vectors are normalized
            features1_norm = features1 / np.linalg.norm(features1)
            features2_norm = features2 / np.linalg.norm(features2)
            
            # cosine similarity（More suitable for handling lighting changes）
            cosine_sim = float(np.dot(features1_norm, features2_norm))
            
            # Euclidean distance（More suitable for handling angle changes）
            euclidean_dist = float(np.linalg.norm(features1_norm - features2_norm))
            
            # Overall rating：Cosine similarity is given higher weight
            # For facial features，Cosine similarity is usually 0.3-1.0 between
            # Euclidean distance is usually 0-2.0 between
            combined_similarity = (cosine_sim * 0.8) + ((2.0 - euclidean_dist) / 2.0 * 0.2)
            combined_score = combined_similarity * 100
            
            return {
                'cosine_similarity': cosine_sim,
                'euclidean_distance': euclidean_dist,
                'combined_similarity': combined_similarity,
                'combined_score': combined_score
            }
            
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}")
            return {
                'cosine_similarity': 0.0,
                'euclidean_distance': 2.0,
                'combined_similarity': 0.0,
                'combined_score': 0.0
            }
    
    def _extract_features_for_comparison(self, image_path: str) -> Optional[np.ndarray]:
        """
        Extract facial features for comparison purposes，No repeated testing
        
        Args:
            image_path: image path
            
        Returns:
            eigenvector orNone
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            faces = self.detect_faces(image)
            if not faces:
                return None
            
            face = faces[0]  # Only take the first face
            features = self.extract_features(image, face)
            return features
            
        except Exception as e:
            logger.warning(f"Feature extraction failed: {e}")
            return None
    
    def _check_frame_similarity(self, current_features: np.ndarray, session_features: List[np.ndarray]) -> Dict[str, Any]:
        """
        Check the similarity of the current frame with other frames in the session
        
        Args:
            current_features: Feature vector of the current frame
            session_features: List of features of processed frames in the session
            
        Returns:
            Check results
        """
        try:
            # Frames within the same session use a higher similarity threshold，Avoid frames that are too similar
            frame_similarity_threshold = 0.98
            threshold_percent = frame_similarity_threshold * 100
            
            for i, session_frame in enumerate(session_features):
                if session_frame is None:
                    continue
                    
                similarity_result = self._calculate_enhanced_similarity(current_features, session_frame)
                if similarity_result['combined_score'] > threshold_percent:
                    logger.info(f"Frame similarity is too high: with frame{i+1}Similarity {similarity_result['combined_score']:.2f}% > {threshold_percent}%")
                    return {
                        'success': False,
                        'similar_frame_index': i + 1,
                        'similarity_score': similarity_result['combined_score']
                    }
            
            return {'success': True}
            
        except Exception as e:
            logger.warning(f"Frame similarity check failed: {e}")
            return {'success': True}  # Allow continuation if check fails
    
    def pre_check_duplicate_for_batch(self, image_paths: List[str], name: str) -> Dict[str, Any]:
        """
        Duplicate detection before batch registration - Check all frames for conflicts with existing database
        This ensures that all frames are checked before any database operations
        
        Args:
            image_paths: and large image path list
            name: Personnel name
            
        Returns:
            Check results dictionary
        """
        try:
            logger.info(f"Repeat checks before starting batch registration，Name: {name}, Frames: {len(image_paths)}")
            
            # Get duplicate detection threshold
            duplicate_threshold_value = config.get('face_recognition.duplicate_threshold', 0.75)
            if isinstance(duplicate_threshold_value, (int, float)):
                duplicate_threshold = float(duplicate_threshold_value)
            else:
                duplicate_threshold = 0.75
            
            similarity_threshold_percent = duplicate_threshold * 100
            
            # First extract the features of all frames
            frame_features = []
            for i, image_path in enumerate(image_paths):
                try:
                    image = cv2.imread(image_path)
                    if image is None:
                        continue
                    
                    faces = self.detect_faces(image)
                    if not faces:
                        continue
                    
                    face = faces[0]  # Only take the first face
                    features = self.extract_features(image, face)
                    if features is not None:
                        frame_features.append((i, features, image_path))
                        
                except Exception as e:
                    logger.warning(f"Extract frames {i+1} Feature failed: {e}")
                    continue
            
            if not frame_features:
                return {
                    'success': False,
                    'error': 'Unable to extract valid facial features from any frame'
                }
            
            logger.info(f"Extracted successfully {len(frame_features)} Characteristics of frames")
            
            # Check each frame to see if it conflicts with an existing face in the database
            try:
                with self.db_manager.get_session() as session:
                    from ..models import FaceEncoding as FaceEncodingModel
                    from ..models import Person
                    
                    # Get all face codes in the database
                    all_faces = session.query(FaceEncodingModel, Person).join(
                        Person, FaceEncodingModel.person_id == Person.id
                    ).all()
                    
                    logger.info(f"Compare in database {len(all_faces)} registered faces")
                    
                    # Check every frame
                    for frame_idx, frame_features_vec, frame_path in frame_features:
                        for face_encoding, person in all_faces:
                            db_enc = face_encoding.embedding
                            if db_enc is None:
                                continue
                                
                            # Process encoded data
                            db_feature = self._parse_face_encoding(db_enc)
                            if db_feature is None:
                                continue
                            
                            # Calculate similarity
                            similarity_result = self._calculate_enhanced_similarity(frame_features_vec, db_feature)
                            
                            # If the similarity exceeds the threshold，Immediately reject the entire batch registration
                            if similarity_result['combined_score'] > similarity_threshold_percent:
                                logger.warning(f"Duplicate faces detected in batch registration! frame{frame_idx+1}: '{name}' vs Already exists: '{person.name}', Similarity: {similarity_result['combined_score']:.2f}%")
                                
                                if person.name == name:
                                    # Duplicate faces of people with the same name
                                    return {
                                        'success': False,
                                        'error': f'Similar faces already exist for this person (Matching degree: {similarity_result["combined_score"]:.1f}%，threshold: {similarity_threshold_percent:.1f}%)',
                                        'frame_index': frame_idx + 1,
                                        'existing_person': person.name
                                    }
                                else:
                                    # Duplicate faces of different people
                                    return {
                                        'success': False,
                                        'error': f'This face has been registered as：{person.name}。The same face cannot be registered as different people。(Matching degree: {similarity_result["combined_score"]:.1f}%，threshold: {similarity_threshold_percent:.1f}%)',
                                        'frame_index': frame_idx + 1,
                                        'existing_person': person.name
                                    }
                    
            except Exception as e:
                logger.error(f"Check before batch registration failed: {e}")
                return {
                    'success': False,
                    'error': 'Face repeatability check failed，For data security，Please try again'
                }
            
            logger.info(f"Pass the check before batch registration，all {len(frame_features)} No duplicates found in frames")
            return {'success': True, 'valid_frames': len(frame_features)}
            
        except Exception as e:
            logger.error(f"Check before batch registration failed: {str(e)}")
            return {
                'success': False,
                'error': 'Face repeatability check failed，Please try registration again'
            }
    
    def extract_face_embeddings(self, image: Union[np.ndarray, str]) -> Dict[str, Any]:
        """
        A method specifically used to extract facial feature vectors，No identification
        
        Args:
            image: image array or image path
            
        Returns:
            Results containing face feature vectors
        """
        try:
            # Process the input image
            if isinstance(image, str):
                img = cv2.imread(image)
                if img is None:
                    return {'success': False, 'error': 'Unable to read image file'}
            else:
                img = image.copy()
            
            if img is None:
                return {'success': False, 'error': 'Invalid image data'}
            
            # Get image size
            height, width = img.shape[:2]
            
            face_embeddings = []
            
            # Use directlyInsightFaceGet faces and features
            try:
                if self.app is not None:
                    logger.info("Get startedInsightFacePerform face detection and feature extraction")
                    # Get all faces and features directly
                    faces_with_features = self.app.get(img)
                    logger.info(f"InsightFacedetected {len(faces_with_features)} personal face")
                    
                    for i, face_result in enumerate(faces_with_features):
                        logger.info(f"processing section {i+1} personal face")
                        # Apply detection threshold filtering
                        detection_threshold = getattr(config, 'DETECTION_THRESHOLD', 0.5)
                        logger.info(f"Detection confidence: {face_result.det_score}, threshold: {detection_threshold}")
                        
                        if face_result.det_score < detection_threshold:
                            logger.info(f"human face {i+1} Confidence too low，jump over")
                            continue
                        
                        # Construct face information
                        try:
                            bbox = face_result.bbox.astype(int).tolist()
                            confidence = float(face_result.det_score)
                            embedding = face_result.normed_embedding.tolist()
                            
                            logger.info(f"human face {i+1}: bbox={bbox}, confidence={confidence}, embedding_len={len(embedding)}")
                            
                            face_info = {
                                'bbox': bbox,
                                'confidence': confidence,
                                'quality': confidence,  # Use detection confidence as quality score
                                'embedding': embedding  # Use standardized feature vectors
                            }
                            
                            face_embeddings.append(face_info)
                            logger.info(f"Face added successfully {i+1} feature information")
                            
                        except Exception as inner_e:
                            logger.error(f"Failed to construct face information: {inner_e}")
                            import traceback
                            logger.error(f"Error details: {traceback.format_exc()}")
                            continue
                        
                else:
                    return {'success': False, 'error': 'InsightFaceModel is not initialized'}
            
            except Exception as e:
                logger.error(f"Face detection and feature extraction failed: {str(e)}")
                import traceback
                logger.error(f"Error details: {traceback.format_exc()}")
                return {'success': False, 'error': f'Feature extraction failed: {str(e)}'}
            
            return {
                'success': True,
                'faces': face_embeddings,
                'total_faces': len(face_embeddings),
                'model_info': f"InsightFace-{self.model_name}" if self.app else f"DeepFace-{self.current_deepface_model}",
                'image_size': [width, height]
            }
            
        except Exception as e:
            logger.error(f"Facial feature extraction failed: {str(e)}")
            return {'success': False, 'error': f'Feature extraction failed: {str(e)}'}
    
    def recognize_face(self, image: Union[np.ndarray, str]) -> Dict[str, Any]:
        """
        High-precision face recognition
        
        Args:
            image: image array or image path
            
        Returns:
            Recognition results，Contains matching person information and confidence
        """
        try:
            # Process the input image
            if isinstance(image, str):
                img = cv2.imread(image)
            else:
                img = image.copy()
            
            if img is None:
                return {'success': False, 'matches': [], 'error': 'Unable to read image'}
            
            # Detect faces
            faces = self.detect_faces(img)
            
            if not faces:
                return {'success': True, 'matches': [], 'message': 'No face detected'}
            
            all_matches = []
            
            for i, face in enumerate(faces):
                # Extract features
                features = self.extract_features(img, face)
                if features is None:
                    continue
                
                # Compare with features in database (use region from method parameter)
                matches = self._match_features(features, region=region)
                
                # Add face location information
                for match in matches:
                    match['face_index'] = i
                    match['bbox'] = face['bbox']
                    match['quality'] = face['quality']
                
                all_matches.extend(matches)
            
            # Sort by match
            all_matches.sort(key=lambda x: x['match_score'], reverse=True)
            
            return {
                'success': True,
                'matches': all_matches,
                'total_faces': len(faces)
            }
        
        except Exception as e:
            logger.error(f"Face recognition failed: {str(e)}")
            return {'success': False, 'matches': [], 'error': f'Recognition failed: {str(e)}'}
    
    def _match_features(self, features: np.ndarray, region: str = 'default') -> List[Dict[str, Any]]:
        """
        Feature matching using PostgreSQL + pgvector
        
        Args:
            features: Feature vector to be matched
            region: Region to search in
            
        Returns:
            List of matching results
        """
        # Read the current recognition threshold from the configuration file
        import json
        try:
            with open('config.json', 'r') as f:
                config_data = json.load(f)
                threshold = config_data.get('face_recognition', {}).get('recognition_threshold', 0.3)
        except:
            threshold = 0.3  # default value
        
        try:
            # Use database search with region filter
            results = self.db_manager.find_similar_faces(
                embedding=features,
                region=region,
                threshold=threshold,
                limit=10
            )
            
            matches = []
            for result in results:
                # Convert distance to similarity score (0-100%)
                # pgvector returns cosine distance, convert to similarity
                similarity = 1.0 - result['distance']
                match_score = max(0, similarity) * 100
                
                matches.append({
                    'person_id': result['person_id'],
                    'name': result['name'],
                    'match_score': float(match_score),
                    'distance': float(result['distance']),
                    'model': f"advanced_{self.model_name}",
                    'face_encoding_id': result.get('face_encoding_id')
                })
            
            # Sort by match score
            matches.sort(key=lambda x: x['match_score'], reverse=True)
            
            logger.info(f"Found {len(matches)} matches in region '{region}'")
            return matches
            
        except Exception as e:
            logger.error(f"Feature matching failed: {str(e)}")
            return []
    
    def _cosine_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """Calculate cosine similarity"""
        # normalization
        features1_norm = features1 / np.linalg.norm(features1)
        features2_norm = features2 / np.linalg.norm(features2)
        
        # Calculate cosine similarity
        similarity = np.dot(features1_norm, features2_norm)
        
        return float(similarity)
    
    def analyze_face_attributes(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Analyze facial attributes（age、gender、Emotions etc.）
        
        Args:
            image: input image
            
        Returns:
            Face attribute analysis results
        """
        try:
            results = []
            
            # Detect faces
            faces = self.detect_faces(image)
            
            for face in faces:
                bbox = face['bbox']
                face_crop = image[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                
                if face_crop.size == 0:
                    continue
                
                try:
                    # use DeepFace Analyze properties
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
                    logger.warning(f"Attribute analysis failed: {str(e)}")
                    continue
            
            return results
        
        except Exception as e:
            logger.error(f"Facial attribute analysis failed: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            with self.db_manager.get_session() as session:
                total_persons = session.query(Person).count()
                total_encodings = session.query(FaceEncoding).count()
                
                # Calculate the average number of photos per person
                avg_photos_per_person = 0.0
                if total_persons > 0:
                    avg_photos_per_person = round(total_encodings / total_persons, 1)
                
                # Get the latest7Day’s headcount
                from datetime import timedelta
                recent_date = datetime.now() - timedelta(days=7)
                recent_persons = session.query(Person).filter(Person.created_at >= recent_date).count()
                
                return {
                    'total_persons': total_persons,
                    'total_encodings': total_encodings,
                    'avg_photos_per_person': avg_photos_per_person,
                    'recent_persons': recent_persons,
                    'current_model': f"InsightFace_{self.model_name}",
                    'deepface_model': self.current_deepface_model,
                    'supported_models': self.deepface_models,
                    'recognition_threshold': config.RECOGNITION_THRESHOLD,
                    'detection_threshold': getattr(config, 'DETECTION_THRESHOLD', 0.5),
                    'duplicate_threshold': config.get('face_recognition.duplicate_threshold', 0.95)
                }
        
        except Exception as e:
            logger.error(f"Failed to obtain statistics: {str(e)}")
            return {}

    def recognize_face_with_threshold(self, image: np.ndarray, region: str, threshold: float = 0.25, client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Face recognition using custom thresholds and region filtering
        **Now uses PostgreSQL + pgvector for fast similarity search**
        
        Args:
            image: input image
            region: Region to search in (A, B, C, etc.)
            threshold: recognition threshold
            client_id: Optional client ID for multi-tenant
            
        Returns:
            Recognition result dictionary
        """
        try:
            start_time = datetime.now()
            
            # Detect faces
            faces = self.detect_faces(image)
            logger.info(f"detected {len(faces)} personal face")
            
            if not faces:
                return {
                    'success': True,
                    'matches': [],
                    'total_faces': 0,
                    'message': 'No face detected'
                }

            matches = []
            
            # Recognize each detected face using vector search
            for face in faces:
                bbox = face['bbox']
                face_embedding = face.get('embedding')
                
                if face_embedding is None:
                    continue
                
                # Use pgvector to find matches in the specified region
                similar_faces = self.db_manager.find_similar_faces(
                    embedding=face_embedding,
                    region=region,
                    client_id=client_id,
                    threshold=threshold,
                    limit=5  # Get top 5 matches
                )
                
                if similar_faces:
                    # Take the best match
                    best_match = similar_faces[0]
                    logger.info(f"Recognition successful: {best_match['name']}, Similarity: {best_match['match_score']:.1f}% in region {region}")
                    
                    matches.append({
                        'person_id': best_match['person_id'],
                        'name': best_match['name'],
                        'region': best_match['region'],
                        'match_score': best_match['match_score'],
                        'distance': best_match['distance'],
                        'model': f"InsightFace_{self.model_name}",
                        'bbox': bbox,
                        'quality': face.get('det_score', 0.9),
                        'face_encoding_id': best_match['face_encoding_id']
                    })
                else:
                    # No match found
                    logger.info(f"Recognition failed: No matching faces found in region {region}")
                    matches.append({
                        'person_id': -1,
                        'name': 'Unknown',
                        'region': region,
                        'match_score': 0.0,
                        'distance': 2.0,
                        'model': f"InsightFace_{self.model_name}",
                        'bbox': bbox,
                        'quality': face.get('det_score', 0.9),
                        'face_encoding_id': None
                    })
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            recognized_count = len([m for m in matches if m["person_id"] != -1])
            
            return {
                'success': True,
                'matches': matches,
                'total_faces': len(faces),
                'processing_time': processing_time,
                'threshold_used': threshold,
                'region': region,
                'message': f'Recognition completed in region {region}, detected {len(faces)} faces, recognized {recognized_count} known persons'
            }
            
        except Exception as e:
            logger.error(f"Face recognition failed: {str(e)}")
            return {
                'success': False,
                'matches': [],
                'total_faces': 0,
                'error': str(e)
            }
    
    def visualize_face_detection(self, image_path: str) -> Dict[str, Any]:
        """
        Generate face detection visualization images（Use augmented visualizer）
        
        Args:
            image_path: Image file path
            
        Returns:
            Dict: Dictionary containing visualization results
        """
        try:
            # read image
            image = cv2.imread(image_path)
            if image is None:
                return {
                    'success': False,
                    'error': 'Unable to read image file'
                }
            
            # Detect faces
            faces_data = []
            if self.app:
                faces = self.app.get(image)
                for i, face in enumerate(faces):
                    bbox = face.bbox.astype(int)
                    face_info = {
                        'bbox': bbox.tolist(),
                        'quality': float(face.det_score),
                        'det_score': float(face.det_score),
                        'name': f'human face {i+1}'
                    }
                    faces_data.append(face_info)
            
            # Generate images using augmented visualizer
            result = self.visualizer.visualize_face_detection(image, faces_data)
            
            if result['success']:
                return {
                    'success': True,
                    'image_base64': result['image_base64'],
                    'faces': result['face_details'],
                    'total_faces': result['total_faces'],
                    'message': f'detected {result["total_faces"]} personal face'
                }
            else:
                return result
            
        except Exception as e:
            logger.error(f"Face detection visualization failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Global service instance
advanced_face_service = None

def get_advanced_face_service() -> AdvancedFaceRecognitionService:
    """Get an example of advanced facial recognition service"""
    global advanced_face_service
    if advanced_face_service is None:
        advanced_face_service = AdvancedFaceRecognitionService()
    return advanced_face_service

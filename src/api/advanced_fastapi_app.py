"""
based on FastAPI advanced facial recognition API interface
support InsightFace and DeepFace Wait for the latest technology
"""
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import cv2
import numpy as np
import uuid
import logging
import asyncio
import base64
import pickle
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import sys

# Add the project root directory toPythonpath
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ..services.advanced_face_service import get_advanced_face_service
from ..utils.config import config, get_upload_config
from src.utils.enhanced_visualization import EnhancedFaceVisualizer
from src.utils.font_manager import get_font_manager

# Create service aliases to maintain compatibility
def get_face_service():
    """Get face recognition service instance"""
    return get_advanced_face_service()

logger = logging.getLogger(__name__)

# Pydantic Model
class PersonCreate(BaseModel):
    name: str = Field(..., description="Personnel name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Personnel description", max_length=500)

class PersonUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Personnel name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Personnel description", max_length=500)

class FaceMatch(BaseModel):
    person_id: int
    name: str
    match_score: float = Field(description="match percentage (0-100%)")
    distance: float = Field(description="Euclidean distance，The smaller, the more similar")
    model: str
    bbox: List[int] = Field(description="face bounding box [x1, y1, x2, y2]")
    quality: float
    face_encoding_id: Optional[int] = Field(None, description="Matching facial featuresID")  # Add new field
    age: Optional[int] = None
    gender: Optional[str] = None
    emotion: Optional[str] = None

class RecognitionResponse(BaseModel):
    success: bool
    matches: List[FaceMatch]
    total_faces: int
    message: Optional[str] = None
    error: Optional[str] = None

class EnrollmentResponse(BaseModel):
    success: bool
    person_id: Optional[int] = None
    face_encoding_id: Optional[int] = None  # facial featuresID
    person_name: Optional[str] = None
    description: Optional[str] = None
    faces_detected: Optional[int] = None
    face_quality: Optional[float] = None
    processing_time: Optional[float] = None
    feature_dim: Optional[int] = None
    embeddings_count: Optional[int] = None
    face_encoding: Optional[List[float]] = None  # Face encoding vector
    visualized_image: Optional[str] = None  # Base64 Encoded detection visualization images
    face_details: Optional[List[Dict]] = None  # List of face details
    error: Optional[str] = None

class FaceAttribute(BaseModel):
    bbox: List[int]
    age: Optional[int]
    gender: Optional[str]
    gender_confidence: Optional[float]
    emotion: Optional[str]
    emotion_scores: Optional[Dict[str, float]]
    race: Optional[str]
    race_scores: Optional[Dict[str, float]]

class AttributeAnalysisResponse(BaseModel):
    success: bool
    faces: List[FaceAttribute]
    total_faces: int
    error: Optional[str] = None

class FaceEmbedding(BaseModel):
    """Facial feature vector model"""
    bbox: List[int] = Field(description="face bounding box [x1, y1, x2, y2]")
    confidence: float = Field(description="Face detection confidence")
    quality: float = Field(description="Face quality score")
    embedding: List[float] = Field(description="512dimensional face feature vector")

class EmbeddingExtractionResponse(BaseModel):
    """Facial feature extraction response model"""
    success: bool
    faces: Optional[List[FaceEmbedding]] = None
    total_faces: Optional[int] = None
    processing_time: Optional[float] = None
    model_info: Optional[str] = None
    image_size: Optional[List[int]] = None  # [width, height]
    error: Optional[str] = None

def create_app() -> FastAPI:
    """create FastAPI application"""
    app = FastAPI(
        title="Advanced facial recognition system API",
        description="based on InsightFace and DeepFace High-precision face recognition system",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Add to CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    web_dir = Path(__file__).parent.parent.parent / "web"
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")
        # mount newassetsTable of contents
        assets_dir = web_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Get service instance
    def get_face_service_instance():
        return get_advanced_face_service()
    
    # Create a global visualizer instance
    visualizer = EnhancedFaceVisualizer()

    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Home page"""
        web_file = Path(__file__).parent.parent.parent / "web" / "index.html"
        if web_file.exists():
            return FileResponse(str(web_file))
        else:
            return HTMLResponse("""
            <html>
                <head><title>Advanced facial recognition system</title></head>
                <body style="font-family: Arial, sans-serif; margin: 40px;">
                    <h1>🚀 Advanced facial recognition system API</h1>
                    <p>based on <strong>InsightFace</strong> and <strong>DeepFace</strong> High-precision face recognition</p>
                    <p><a href="/docs">📋 CheckAPIdocument</a></p>
                </body>
            </html>
            """)

    @app.get("/{file_path}.html", response_class=HTMLResponse)
    async def serve_html(file_path: str):
        """ServeHTMLdocument"""
        web_file = Path(__file__).parent.parent.parent / "web" / f"{file_path}.html"
        if web_file.exists():
            return FileResponse(str(web_file))
        else:
            raise HTTPException(status_code=404, detail="Page not found")

    @app.post("/api/enroll", response_model=EnrollmentResponse)
    async def enroll_person(
        file: UploadFile = File(..., description="Face image file"),
        name: str = Form(..., description="Personnel name"),
        region: str = Form(..., description="Region (ka/ap/tn)"),
        emp_id: str = Form(..., description="Employee ID"),
        emp_rank: str = Form(..., description="Employee Rank"),
        description: Optional[str] = Form(None, description="Personnel description"),
        service = Depends(get_face_service)
    ):
        """
        🔐 Personnel warehousing interface
        
        Upload face images for personnel registration and database
        """
        try:
            # Verify file type
            if file.content_type and not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Only supports image files")

            # Save temporary files
            upload_config = get_upload_config()
            
            # Check file size
            content = await file.read()
            file_size = len(content)
            
            max_size = 10 * 1024 * 1024  # 10MB default value
            if upload_config and isinstance(upload_config, dict):
                max_size = upload_config.get('MAX_FILE_SIZE', max_size)
            
            # make sure max_size is an integer
            if isinstance(max_size, (int, float)):
                if file_size > max_size:
                    raise HTTPException(status_code=400, detail="File too large")
            else:
                # If there is a problem with the configuration，Use default value
                if file_size > 10 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail="File too large")

            # Save temporary files
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(content)
            temp_file.close()

            try:
                # Call the service for storage
                import time
                start_time = time.time()
                result = service.enroll_person(name, temp_file.name, region, emp_id, emp_rank, description, file.filename)
                processing_time = time.time() - start_time
                
                if result['success']:
                    # Generate face detection visualization images
                    visualized_image = None
                    face_details = None
                    
                    try:
                        # Call the visualization interface to generate detection images
                        visual_result = service.visualize_face_detection(temp_file.name)
                        if visual_result['success'] and 'image_base64' in visual_result:
                            visualized_image = visual_result['image_base64']
                            face_details = visual_result.get('faces', [])
                    except Exception as e:
                        print(f"Failed to generate visualization image: {e}")
                    
                    return EnrollmentResponse(
                        success=True,
                        person_id=int(result['person_id']),
                        face_encoding_id=int(result.get('face_encoding_id', 0)) if result.get('face_encoding_id') else None,
                        person_name=name,
                        description=description,
                        faces_detected=int(result.get('faces_detected', 1)),
                        face_quality=float(result.get('quality_score', 0.0)) if result.get('quality_score') else None,
                        processing_time=float(processing_time),
                        feature_dim=int(result.get('feature_dim', 0)) if result.get('feature_dim') else None,
                        embeddings_count=1,
                        visualized_image=visualized_image,
                        face_details=face_details
                    )
                else:
                    return EnrollmentResponse(
                        success=False,
                        error=result['error']
                    )
            finally:
                # Clean temporary files
                os.unlink(temp_file.name)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Inbound interface error: {str(e)}")
            return EnrollmentResponse(
                success=False,
                error=f"Server internal error: {str(e)}"
            )

    @app.post("/api/enroll_simple", response_model=EnrollmentResponse)
    async def enroll_person_simple(
        file: UploadFile = File(..., description="Face image file"),
        name: str = Form(..., description="Personnel name"),
        region: str = Form(..., description="Region (ka/ap/tn)"),
        emp_id: str = Form(..., description="Employee ID"),
        emp_rank: str = Form(..., description="Employee Rank"),
        description: Optional[str] = Form(None, description="Personnel description"),
        service = Depends(get_face_service)
    ):
        """
        🔐 Personnel warehousing interface (Simplified version)
        
        Upload face images for personnel registration and database，Do not return image data to save bandwidth
        """
        try:
            # Verify file type
            if file.content_type and not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Only supports image files")

            # Save temporary files
            upload_config = get_upload_config()
            
            # Check file size
            content = await file.read()
            file_size = len(content)
            
            max_size = 10 * 1024 * 1024  # 10MB default value
            if upload_config and isinstance(upload_config, dict):
                max_size = upload_config.get('MAX_FILE_SIZE', max_size)
            
            # make sure max_size is an integer
            if isinstance(max_size, (int, float)):
                if file_size > max_size:
                    raise HTTPException(status_code=400, detail="File too large")
            else:
                # If there is a problem with the configuration，Use default value
                if file_size > 10 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail="File too large")

            # Save temporary files
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(content)
            temp_file.close()

            try:
                # Call the service for storage
                import time
                start_time = time.time()
                result = service.enroll_person(name, temp_file.name, region, emp_id, emp_rank, description, file.filename)
                processing_time = time.time() - start_time
                
                if result['success']:
                    return EnrollmentResponse(
                        success=True,
                        person_id=int(result['person_id']),
                        face_encoding_id=int(result.get('face_encoding_id', 0)) if result.get('face_encoding_id') else None,
                        person_name=name,
                        description=description,
                        faces_detected=int(result.get('faces_detected', 1)),
                        face_quality=float(result.get('quality_score', 0.0)) if result.get('quality_score') else None,
                        processing_time=float(processing_time),
                        feature_dim=int(result.get('feature_dim', 0)) if result.get('feature_dim') else None,
                        embeddings_count=1,
                        # face_encoding=result.get('face_encoding'),  # Returns the face encoding vector
                        # The simplified version does not return image data
                        visualized_image=None,
                        face_details=None
                    )
                else:
                    return EnrollmentResponse(
                        success=False,
                        error=result['error']
                    )
            finally:
                # Clean temporary files
                os.unlink(temp_file.name)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Inbound interface error: {str(e)}")
            return EnrollmentResponse(
                success=False,
                error=f"Server internal error: {str(e)}"
            )

    @app.post("/api/extract_embeddings", response_model=EmbeddingExtractionResponse)
    async def extract_face_embeddings(
        file: UploadFile = File(..., description="Face image file"),
        service = Depends(get_face_service)
    ):
        """
        🔍 Face feature vector extraction interface
        
        Specifically used to extract facial feature vectors，No identification
        Returns all detected faces in the image512dimensional eigenvector
        Suitable for external systems for similarity calculation or other machine learning tasks
        """
        try:
            # Verify file type
            if file.content_type and not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Only supports image files")

            # Save temporary files
            upload_config = get_upload_config()
            
            # Check file size
            content = await file.read()
            file_size = len(content)
            
            max_size = 10 * 1024 * 1024  # 10MB default value
            if upload_config and isinstance(upload_config, dict):
                max_size = upload_config.get('MAX_FILE_SIZE', max_size)
            
            # make sure max_size is an integer
            if isinstance(max_size, (int, float)):
                if file_size > max_size:
                    raise HTTPException(status_code=400, detail="File too large")
            else:
                # If there is a problem with the configuration，Use default value
                if file_size > 10 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail="File too large")

            # Save temporary files
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(content)
            temp_file.close()

            try:
                # Call the service for feature extraction
                import time
                start_time = time.time()
                result = service.extract_face_embeddings(temp_file.name)
                processing_time = time.time() - start_time
                
                if result['success']:
                    return EmbeddingExtractionResponse(
                        success=True,
                        faces=result.get('faces', []),
                        total_faces=result.get('total_faces', 0),
                        processing_time=float(processing_time),
                        model_info=result.get('model_info'),
                        image_size=result.get('image_size')
                    )
                else:
                    return EmbeddingExtractionResponse(
                        success=False,
                        error=result.get('error', 'unknown error')
                    )
            finally:
                # Clean temporary files
                os.unlink(temp_file.name)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Facial feature extraction interface error: {str(e)}")
            return EmbeddingExtractionResponse(
                success=False,
                error=f"Server internal error: {str(e)}"
            )

    @app.post("/api/batch_enroll")
    async def batch_enroll_persons(
        files: List[UploadFile] = File(..., description="Face image file list"),
        names: Optional[List[str]] = Form(None, description="Person name list（Optional，If not provided, extract from filename）"),
        region: Optional[str] = Form(None, description="Region (ka/ap/tn)"),
        emp_id: Optional[str] = Form(None, description="Employee ID"),
        emp_rank: Optional[str] = Form(None, description="Employee Rank"),
        descriptions: Optional[List[str]] = Form(None, description="Person description list（Optional）"),
        sort_by_filename: bool = Form(True, description="Whether to sort processing by file name"),
        service = Depends(get_face_service)
    ):
        """
        🔐 Batch personnel warehousing interface
        
        Upload facial images in batches for personnel registration and database
        Supports automatic extraction of person names from file names
        Sort by file name by default，Ensure processing order consistency
        Enhanced duplicate detection logic，Especially suitable for video registration
        """
        try:
            if not files:
                raise HTTPException(status_code=400, detail="Please upload at least one file")
            
            # If filename sorting is enabled，Sort files by file name
            file_items = []
            for i, file in enumerate(files):
                file_items.append({
                    'file': file,
                    'original_index': i,
                    'filename': file.filename or f"unnamed_file_{i+1}"
                })
            
            if sort_by_filename:
                # Sort by file name，Ensure numbered files are processed in the correct order
                file_items.sort(key=lambda x: x['filename'])
                logger.info(f"Batch storage：Sort by file name，Processing order: {[item['filename'] for item in file_items]}")
            
            results = []
            success_count = 0
            error_count = 0
            
            # Process name list - Supports flexible name assignment
            names_list: List[Optional[str]] = []
            if names:
                # If name provided，Use the name provided first，The missing parts will be supplemented later with the file name.
                names_list = list(names)
                logger.info(f"Batch storage：receive {len(names)} name，common {len(files)} files")
            else:
                # If no name is provided，All use file names
                names_list = []
                logger.info(f"Batch storage：No name provided，will use the file name as the name")
            
            # Expand description list to match number of files
            desc_list: List[Optional[str]] = []
            if descriptions:
                desc_list = list(descriptions)
                while len(desc_list) < len(files):
                    desc_list.append(None)
            else:
                desc_list = [None] * len(files)
            
            # Detect if there are multiple photos of the same person/frame（Video registration）
            is_single_person_batch = False
            target_name = None
            
            if names_list and len(names_list) > 0 and names_list[0]:
                # If name provided，All documents use this name，This may be a video registration
                target_name = names_list[0].strip()
                is_single_person_batch = True
                logger.info(f"Single-person batch registration mode detected，target name: {target_name}")
            
            # Prepare session characteristics data for video registration
            session_features = []  # Store all features from the same session，Used to avoid inter-frame repeat detection
            
            # critical fix：before processing any file，First pre-check all files for conflicts with the database
            file_contents = {}  # Store file content，Avoid repeated reads
            if is_single_person_batch and target_name:
                logger.info(f"Video registration mode：right {len(file_items)} frame pre-check")
                
                # First save all files as temporary files
                temp_files = []
                try:
                    for i, item in enumerate(file_items):
                        file = item['file']
                        content = await file.read()
                        file_contents[i] = content  # Store content for later use
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                        temp_file.write(content)
                        temp_file.close()
                        temp_files.append(temp_file.name)
                    
                    # Perform pre-check
                    pre_check_result = service.pre_check_duplicate_for_batch(temp_files, target_name)
                    
                    if not pre_check_result['success']:
                        # Precheck failed，Return error immediately，No registration required
                        logger.warning(f"Video registration pre-check failed: {pre_check_result['error']}")
                        return {
                            'success': False,
                            'total_files': len(files),
                            'success_count': 0,
                            'error_count': len(files),
                            'results': [{
                                'file_name': file_items[pre_check_result.get('frame_index', 1) - 1]['filename'] if 'frame_index' in pre_check_result else file_items[0]['filename'],
                                'name': target_name,
                                'success': False,
                                'error': pre_check_result['error']
                            }],
                            'message': f'Video registration failed: {pre_check_result["error"]}',
                            'duplicate_detected': True,
                            'is_video_registration': True
                        }
                    
                    logger.info(f"Video registration pre-check passed，It's safe to register")
                    
                finally:
                    # Clean temporary files
                    for temp_file_path in temp_files:
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
            else:
                # Not in video registration mode，No pre-check required，But needs to be initializedfile_contents
                file_contents = {}
            
            for i, item in enumerate(file_items):
                file = item['file']
                original_index = item['original_index']
                # Save filename immediately when processing starts，Avoid subsequent status changes
                original_filename = item['filename']
                name = "unknown"  # Initialize default value
                
                logger.info(f"Process files {i+1}/{len(file_items)}: {original_filename}")
                
                try:
                    # Verify file type
                    if file.content_type and not file.content_type.startswith('image/'):
                        results.append({
                            'file_name': original_filename,
                            'success': False,
                            'error': 'Unsupported file types'
                        })
                        error_count += 1
                        continue

                    # Get person name - Flexible handling of name assignments
                    if is_single_person_batch and target_name:
                        # Video registration mode：All files use the same name
                        name = target_name
                    elif names_list and len(names_list) > 0 and names_list[0]:
                        # If name provided，All documents use this name
                        name = names_list[0].strip()
                    else:
                        # If no name is provided，Extract names from filename（Remove extension）
                        name = os.path.splitext(original_filename)[0]
                        # Clean filename as name
                        name = name.replace('_', ' ').replace('-', ' ').strip()
                        if not name or name.startswith("unnamed_file_"):
                            name = f"person_{i+1}"
                    
                    # Get description
                    description = desc_list[original_index] if original_index < len(desc_list) else None

                    # Check file size
                    if i in file_contents:
                        # Use what has been read（pre-inspection phase）
                        content = file_contents[i]
                    else:
                        # Non-video registration mode，Now read the file
                        content = await file.read()
                    file_size = len(content)
                    
                    max_size = 10 * 1024 * 1024  # 10MB
                    if file_size > max_size:
                        results.append({
                            'file_name': original_filename,
                            'name': name,
                            'success': False,
                            'error': 'File too large'
                        })
                        error_count += 1
                        continue

                    # Save temporary files
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    temp_file.write(content)
                    temp_file.close()

                    try:
                        # Validate required fields
                        if not region or not emp_id or not emp_rank:
                            results.append({
                                'file_name': original_filename,
                                'name': name,
                                'success': False,
                                'error': 'Missing required fields: region, emp_id, or emp_rank'
                            })
                            error_count += 1
                            continue
                        
                        # Call the service for storage，Pass in the original file name for correct storage
                        # If it is a video registration that has been pre-checked，Use a duplicate-free version
                        if is_single_person_batch and target_name:
                            result = service.enroll_person_no_duplicate_check(name, temp_file.name, region, emp_id, emp_rank, description, original_filename)
                        else:
                            result = service.enroll_person(name, temp_file.name, region, emp_id, emp_rank, description, original_filename)
                        
                        if result['success']:
                            # successfully processed，Add features to session list（If it is single-player batch mode）
                            if is_single_person_batch:
                                if 'face_encoding' in result and result['face_encoding']:
                                    session_features.append(np.array(result['face_encoding']))
                            
                            results.append({
                                'file_name': original_filename,
                                'name': name,
                                'person_id': result.get('person_id'),
                                'face_encoding_id': result.get('face_encoding_id'),  # Add facial featuresID
                                'success': True,
                                'quality_score': result.get('quality_score', 0)
                            })
                            success_count += 1
                        else:
                            # Failure handling - Strict duplication testing will immediately stop all registrations
                            error_msg = result.get('error', 'Storage failed')
                            
                            # Check if it is a duplicate face error
                            if ('Similar faces' in error_msg or 'Already exists' in error_msg or 
                                'Already registered' in error_msg or 'Cannot register as a different person' in error_msg):
                                
                                # Duplicate faces detected，Stop the entire batch immediately
                                logger.warning(f"Duplicate faces detected，Stop all registrations immediately: {error_msg}")
                                
                                if is_single_person_batch:
                                    # Error message in video registration mode
                                    return {
                                        'success': False,
                                        'total_files': len(files),
                                        'success_count': success_count,
                                        'error_count': 1,
                                        'results': [{
                                            'file_name': original_filename,
                                            'name': name,
                                            'success': False,
                                            'error': error_msg
                                        }],
                                        'message': f'Video registration failed: {error_msg}',
                                        'duplicate_detected': True,
                                        'is_video_registration': True
                                    }
                                else:
                                    # General batch registration error message
                                    return {
                                        'success': False,
                                        'total_files': len(files),
                                        'success_count': success_count,
                                        'error_count': 1,
                                        'results': [{
                                            'file_name': original_filename,
                                            'name': name,
                                            'success': False,
                                            'error': error_msg
                                        }],
                                        'message': f'Registration failed: {error_msg}',
                                        'duplicate_detected': True
                                    }
                            else:
                                # Other errors，Log but continue processing
                                results.append({
                                    'file_name': original_filename,
                                    'name': name,
                                    'success': False,
                                    'error': error_msg
                                })
                                error_count += 1
                            
                    finally:
                        # Delete temporary files
                        if os.path.exists(temp_file.name):
                            os.unlink(temp_file.name)
                            
                except Exception as file_error:
                    results.append({
                        'file_name': original_filename,
                        'name': name,
                        'success': False,
                        'error': f"Processing file failed: {str(file_error)}"
                    })
                    error_count += 1

            # Build final response
            final_message = f"Batch storage completed：success {success_count} indivual，fail {error_count} indivual"
            if is_single_person_batch:
                final_message = f"Video registration completed：successfully processed {success_count} frame，fail {error_count} frame"
            
            return {
                'success': True,
                'total_files': len(files),
                'success_count': success_count,
                'error_count': error_count,
                'results': results,
                'message': final_message,
                'is_video_registration': is_single_person_batch  # Whether the logo is a video registration
            }
            
        except Exception as e:
            logger.error(f"Batch warehousing interface error: {str(e)}")
            return {
                'success': False,
                'error': f"Batch storage failed: {str(e)}",
                'total_files': len(files) if files else 0,
                'success_count': 0,
                'error_count': len(files) if files else 0,
                'results': []
            }

    @app.post("/api/recognize", response_model=RecognitionResponse)
    async def recognize_face(
        file: UploadFile = File(..., description="Image file to be recognized"),
        region: str = Form(..., description="Region to search in (ka/ap/tn)"),
        service = Depends(get_face_service)
    ):
        """
        🔍 Face recognition interface
        
        Upload images for face recognition，Return matching person information
        """
        try:
            # Read recognition thresholds from configuration file
            import json
            try:
                with open('config.json', 'r') as f:
                    config_data = json.load(f)
                    threshold = config_data.get('face_recognition', {}).get('recognition_threshold', 0.3)
            except:
                threshold = 0.3  # default value
            
            # Verify file type
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Only supports image files")

            # Save temporary files
            content = await file.read()
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(content)
            temp_file.close()

            try:
                # read image
                image = cv2.imread(temp_file.name)
                if image is None:
                    raise HTTPException(status_code=400, detail="Unable to parse image")
                
                # Call service for identification（Use dynamic thresholds and region filtering）
                result = service.recognize_face_with_threshold(image, region=region, threshold=threshold)
                
                if result['success']:
                    matches = [
                        FaceMatch(
                            person_id=match['person_id'],
                            name=match['name'],
                            match_score=match['match_score'],
                            distance=match['distance'],
                            model=match['model'],
                            bbox=match['bbox'],
                            quality=match['quality'],
                            face_encoding_id=match.get('face_encoding_id')  # Add faceIDField
                        )
                        for match in result['matches']
                    ]
                    
                    return RecognitionResponse(
                        success=True,
                        matches=matches,
                        total_faces=result['total_faces'],
                        message=result.get('message')
                    )
                else:
                    return RecognitionResponse(
                        success=False,
                        matches=[],
                        total_faces=0,
                        error=result['error']
                    )
            finally:
                # Clean temporary files
                os.unlink(temp_file.name)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Identify interface errors: {str(e)}")
            return RecognitionResponse(
                success=False,
                matches=[],
                total_faces=0,
                error=f"Server internal error: {str(e)}"
            )

    @app.post("/api/recognize_visual", summary="face recognition（with visualization）")
    async def recognize_face_with_visualization(
        file: UploadFile = File(..., description="Image file to be recognized"),
        region: str = Form(..., description="Region to search in (ka/ap/tn)"),
        threshold: Optional[float] = None,
        service = Depends(get_face_service)
    ):
        """
        🔍 Face recognition interface（with visualization）
        
        Upload images for face recognition，Returns an image labeled with detection boxes and matching information
        If no threshold parameter is provided，The recognition threshold in the configuration file will be used
        """
        try:
            # If no threshold is provided，Read from configuration file
            if threshold is None:
                import json
                try:
                    with open('config.json', 'r') as f:
                        config_data = json.load(f)
                        threshold = config_data.get('face_recognition', {}).get('recognition_threshold', 0.25)
                except:
                    threshold = 0.25  # default value，Consistent with configuration file
            # Verify file type
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Only supports image files")

            # read image
            content = await file.read()
            nparr = np.frombuffer(content, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise HTTPException(status_code=400, detail="Unable to parse image")

            # Call service for identification（Use dynamic thresholds and region filtering）
            result = service.recognize_face_with_threshold(image, region=region, threshold=threshold)
            
            if result['success']:
                # make surethresholdNot forNone（has been assigned a value at this time）
                assert threshold is not None, "threshold should not be None at this point"
                
                # Generate visualization images using augmented visualizer
                visual_result = visualizer.visualize_recognition_results(
                    image, result['matches'], threshold
                )
                
                if visual_result['success']:
                    # Willbase64Convert image to temporary file
                    import base64
                    image_data = base64.b64decode(visual_result['image_base64'])
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    temp_file.write(image_data)
                    temp_file.close()
                    
                    try:
                        return FileResponse(
                            temp_file.name, 
                            media_type="image/jpeg",
                            filename=f"recognition_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        )
                    finally:
                        # Clean temporary files（delayed deletion）
                        asyncio.create_task(cleanup_temp_file(temp_file.name))
                else:
                    raise HTTPException(status_code=500, detail="Visualization generation failed")
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'Recognition failed'))

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Visually identify interface errors: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Server internal error: {str(e)}")

    async def cleanup_temp_file(file_path: str):
        """Delay cleaning of temporary files"""
        await asyncio.sleep(1)  # wait1Seconds to ensure the file has been downloaded
        try:
            os.unlink(file_path)
        except:
            pass

    @app.post("/api/analyze", response_model=AttributeAnalysisResponse)
    async def analyze_face_attributes(
        file: UploadFile = File(..., description="Image file to be analyzed"),
        service = Depends(get_face_service)
    ):
        """
        🎭 Face attribute analysis interface
        
        Analyze the age of a face、gender、mood、Attributes such as race
        """
        try:
            # Verify file type
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Only supports image files")

            # read image
            content = await file.read()
            nparr = np.frombuffer(content, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise HTTPException(status_code=400, detail="Unable to parse image")

            # Call service analysis properties
            attributes = service.analyze_face_attributes(image)
            
            faces = [
                FaceAttribute(
                    bbox=attr['bbox'],
                    age=attr.get('age'),
                    gender=attr.get('gender'),
                    gender_confidence=attr.get('gender_confidence'),
                    emotion=attr.get('emotion'),
                    emotion_scores=attr.get('emotion_scores'),
                    race=attr.get('race'),
                    race_scores=attr.get('race_scores')
                )
                for attr in attributes
            ]
            
            return AttributeAnalysisResponse(
                success=True,
                faces=faces,
                total_faces=len(faces)
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Property analysis interface error: {str(e)}")
            return AttributeAnalysisResponse(
                success=False,
                faces=[],
                total_faces=0,
                error=f"Server internal error: {str(e)}"
            )

    @app.get("/api/statistics")
    async def get_statistics(service = Depends(get_face_service)):
        """
        📊 Get system statistics
        
        Number of people returning to the system、Model distribution and other statistical data and system configuration
        """
        try:
            stats = service.get_statistics()
            
            # Add system configuration information
            from ..utils.config import config
            stats['system_config'] = {
                'recognition_threshold': {
                    'current': getattr(config, 'RECOGNITION_THRESHOLD', 0.6),
                    'min': 0.0,
                    'max': 0.9,
                    'step': 0.05,
                    'description': 'recognition threshold：Control the strictness of facial recognition，The higher the value, the stricter the identification.'
                },
                'detection_threshold': {
                    'current': getattr(config, 'DETECTION_THRESHOLD', 0.5),
                    'min': 0.1,
                    'max': 0.9,
                    'step': 0.05,
                    'description': 'Detection threshold：Controlling the sensitivity of face detection，The higher the value, the more stringent the detection'
                },
                'duplicate_threshold': {
                    'current': config.get('face_recognition.duplicate_threshold', 0.95),
                    'min': 0.8,
                    'max': 0.99,
                    'step': 0.01,
                    'description': 'Duplicate warehousing threshold：Faces whose similarity exceeds this value will be rejected from the database，prevent duplication'
                },
                'model_info': {
                    'primary': 'InsightFace Buffalo-L',
                    'accuracy': '99.83% (LFW)',
                    'backend': 'ONNX Runtime'
                },
                'performance': {
                    'detection_speed': '~50ms/frame',
                    'recognition_speed': '~10ms/face',
                    'max_face_size': '640x640'
                }
            }
            
            return JSONResponse(content=stats)
        except Exception as e:
            logger.error(f"Failed to obtain statistics: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to obtain statistics")

    @app.post("/api/config/threshold")
    async def update_threshold(threshold: float = Form(...)):
        """
        🔧 Update recognition threshold configuration
        
        Args:
            threshold: New recognition threshold (0.0-0.9)
        """
        try:
            if not 0.0 <= threshold <= 0.9:
                raise HTTPException(status_code=400, detail="The threshold must be within0.0-0.9between")
            
            # Update configuration
            from ..utils.config import config
            config.RECOGNITION_THRESHOLD = threshold
            
            return JSONResponse(content={
                "success": True,
                "message": f"The recognition threshold has been updated to {threshold}",
                "new_threshold": threshold
            })
        except Exception as e:
            logger.error(f"Update threshold failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Update threshold failed")

    @app.post("/api/config/duplicate_threshold")
    async def update_duplicate_threshold(threshold: float = Form(...)):
        """
        🔧 Update duplicate warehousing threshold configuration
        
        Args:
            threshold: New duplicate entry threshold (0.8-0.99)
        """
        try:
            if not 0.8 <= threshold <= 0.99:
                raise HTTPException(status_code=400, detail="The duplicate warehousing threshold must be within0.8-0.99between")
            
            # Update configuration
            from ..utils.config import config
            config.set('face_recognition.duplicate_threshold', threshold)
            
            return JSONResponse(content={
                "success": True,
                "message": f"The duplicate warehousing threshold has been updated to {threshold:.2f}",
                "new_threshold": threshold
            })
        except Exception as e:
            logger.error(f"Failed to update duplicate warehousing threshold: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update duplicate warehousing threshold")

    @app.get("/api/persons")
    async def get_persons(include_image_info: bool = Query(False, description="Whether to include picture information"), service = Depends(get_face_service)):
        """
        👥 Get a list of all people
        
        Return all entered personnel information in the system，Optionally include image information such as original file name
        """
        try:
            with service.db_manager.get_session() as session:
                from ..models import Person
                persons = session.query(Person).all()
                
                persons_data = []
                for person in persons:
                    # Get the number of codes for this person
                    from ..models import FaceEncoding
                    encodings = session.query(FaceEncoding).filter(
                        FaceEncoding.person_id == person.id
                    ).all()
                    
                    encoding_count = len(encodings)
                    
                    # Get the first face code as avatar
                    first_encoding = encodings[0] if encodings else None
                    
                    face_image_url = None
                    if first_encoding:
                        face_image_url = f"/api/face/{first_encoding.id}/image"
                    
                    person_data = {
                        "id": person.id,
                        "name": person.name,
                        "description": person.description,
                        "created_at": person.created_at.isoformat() if person.created_at else None,
                        "encodings_count": encoding_count,
                        "face_count": encoding_count,  # Compatible fields
                        "face_image_url": face_image_url
                    }
                    
                    # If the request contains image information，Add detailed image file name information
                    if include_image_info and encodings:
                        person_data["image_files"] = []
                        for encoding in encodings:
                            person_data["image_files"].append({
                                "encoding_id": encoding.id,
                                "original_filename": encoding.image_path,  # Now the original file name is stored
                                "quality_score": encoding.quality_score,
                                "created_at": encoding.created_at.isoformat() if encoding.created_at else None,
                                "image_size": len(encoding.image_data) if encoding.image_data else 0
                            })
                    
                    persons_data.append(person_data)
                
                response_data = {
                    "success": True,
                    "persons": persons_data,
                    "total": len(persons_data)
                }
                
                # If image information is included，Add statistical summary
                if include_image_info:
                    total_images = sum(len(p.get("image_files", [])) for p in persons_data)
                    response_data["image_summary"] = {
                        "total_images": total_images,
                        "persons_with_multiple_images": len([p for p in persons_data if len(p.get("image_files", [])) > 1])
                    }
                
                return JSONResponse(content=response_data)
        except Exception as e:
            logger.error(f"Failed to get personnel list: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get personnel list")

    @app.get("/api/person/{person_id}")
    async def get_person(person_id: int, service = Depends(get_face_service)):
        """
        👤 Get designated person details
        
        Returns the detailed information and face encoding number of the specified person
        """
        try:
            with service.db_manager.get_session() as session:
                from ..models import Person, FaceEncoding
                person = session.query(Person).filter(Person.id == person_id).first()
                
                if not person:
                    raise HTTPException(status_code=404, detail="Personnel does not exist")
                
                # Get the number of face codes
                encoding_count = session.query(FaceEncoding).filter(FaceEncoding.person_id == person_id).count()
                
                return JSONResponse(content={
                    "success": True,
                    "id": person.id,
                    "name": person.name,
                    "region": person.region,
                    "emp_id": person.emp_id,
                    "emp_rank": person.emp_rank,
                    "description": person.description,
                    "created_at": person.created_at.isoformat() if person.created_at else None,
                    "updated_at": person.updated_at.isoformat() if person.updated_at else None,
                    "encoding_count": encoding_count
                })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to obtain person details: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to obtain person details")

    @app.get("/api/person/{person_id}/faces")
    async def get_person_faces(person_id: int, service = Depends(get_face_service)):
        """
        👤 Get all face codes of the specified person
        
        Returns all facial feature vector information of the specified person
        """
        try:
            face_encodings = service.db_manager.get_face_encodings_by_person(person_id)
            
            face_list = []
            for encoding in face_encodings:
                face_info = encoding.to_dict()
                face_list.append(face_info)
            
            return JSONResponse(content={
                "success": True,
                "person_id": person_id,
                "face_encodings": face_list,
                "total_faces": len(face_list)
            })
        except Exception as e:
            logger.error(f"Failed to obtain the person's face list: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to obtain the person's face list")

    @app.api_route("/api/face/{face_encoding_id}/image", methods=["GET", "HEAD"])
    async def get_face_image(face_encoding_id: int, request: Request, service = Depends(get_face_service)):
        """
        🖼️ Get face pictures
        
        Returns the image data of the specified face encoding
        """
        try:
            # Use the database manager method directly
            encoding = service.db_manager.get_face_encoding_by_id(face_encoding_id)
            if not encoding:
                raise HTTPException(status_code=404, detail="The specified face code was not found")
            
            image_data = encoding.get_image_data()
            if not image_data:
                raise HTTPException(status_code=404, detail="This face code has no associated image data")
            
            # forHEADask，Return onlyheaders，No content returned
            if request.method == "HEAD":
                return Response(
                    content="",
                    media_type="image/jpeg",
                    headers={
                        "Cache-Control": "max-age=3600",
                        "Content-Length": str(len(image_data))
                    }
                )
            
            # forGETask，Return image data
            return Response(
                content=image_data,
                media_type="image/jpeg",
                headers={"Cache-Control": "max-age=3600"}
            )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to obtain face image: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to obtain face image")

    @app.put("/api/person/{person_id}")
    async def update_person(person_id: int, person_data: PersonUpdate, service = Depends(get_face_service)):
        """
        ✏️ Update designated person information
        
        Update the basic information of the person（Name、department、Position、Remarks, etc.）
        """
        try:
            with service.db_manager.get_session() as session:
                from ..models import Person
                
                # Find people
                person = session.query(Person).filter(Person.id == person_id).first()
                if not person:
                    raise HTTPException(status_code=404, detail="Specified person not found")
                
                # Update field（Only update non-Nonefields）
                update_data = person_data.dict(exclude_unset=True)
                for field, value in update_data.items():
                    if hasattr(person, field):
                        setattr(person, field, value)
                
                person.updated_at = datetime.utcnow()
                session.commit()
                
                # Return updated personnel information
                return JSONResponse(content={
                    "success": True,
                    "message": "Personnel information updated successfully",
                    "person": {
                        "id": person.id,
                        "name": person.name,
                        "description": person.description,
                        "created_at": person.created_at.isoformat() if person.created_at else None,
                        "updated_at": person.updated_at.isoformat() if person.updated_at else None
                    }
                })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update personnel information: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update personnel information")

    @app.delete("/api/person/{person_id}")
    async def delete_person(person_id: int, service = Depends(get_face_service)):
        """
        🗑️ Delete specified person
        
        Delete the specified person and all their face codes
        """
        try:
            # Get person name before deletion
            person = service.db_manager.get_person_by_id(person_id)
            if not person:
                raise HTTPException(status_code=404, detail="Personnel does not exist")
            
            person_name = person.name
            
            # Use the database manager's delete method which handles everything properly
            success = service.db_manager.delete_person(person_id)
            
            if success:
                return JSONResponse(content={
                    "success": True,
                    "message": f"personnel {person_name} Deleted"
                })
            else:
                raise HTTPException(status_code=404, detail="Personnel does not exist")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete person: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete person")

    @app.get("/api/config")
    async def get_config():
        """
        ⚙️ Get system configuration
        
        Return system configuration information
        """
        try:
            from ..utils.config import config
            return JSONResponse(content={
                "success": True,
                "recognition_threshold": getattr(config, 'RECOGNITION_THRESHOLD', 0.24),
                "detection_threshold": getattr(config, 'DETECTION_THRESHOLD', 0.31),
                "duplicate_threshold": config.get('face_recognition.duplicate_threshold', 0.95),
                "max_file_size": getattr(config, 'MAX_FILE_SIZE', 16777216),
                "supported_formats": config.ALLOWED_EXTENSIONS,
                "model": getattr(config, 'MODEL', 'buffalo_l'),
                "providers": getattr(config, 'PROVIDERS', ["CPUExecutionProvider"]),
                "host": getattr(config, 'HOST', '0.0.0.0'),
                "port": getattr(config, 'PORT', 8000),
                "debug": getattr(config, 'DEBUG', False),
                "upload_folder": getattr(config, 'UPLOAD_FOLDER', 'data/uploads'),
                "database_path": getattr(config, 'DATABASE_PATH', 'data/database/face_recognition.db'),
                "models_root": getattr(config, 'MODELS_INSIGHTFACE_ROOT', 'models/insightface'),
                "cache_dir": getattr(config, 'MODELS_CACHE_DIR', 'models/cache')
            })
        except Exception as e:
            logger.error(f"Failed to get configuration: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get configuration")

    @app.post("/api/config")
    async def update_config(request: Request):
        """
        ⚙️ Update system configuration
        
        Update configurations such as face recognition thresholds，Supports multiple parameter name compatibility
        """
        try:
            from ..utils.config import config
            data = await request.json()
            
            success_messages = []
            
            # Handling recognition thresholds
            if "recognition_threshold" in data:
                threshold_value = float(data["recognition_threshold"])
                if not 0.0 <= threshold_value <= 0.9:
                    raise HTTPException(status_code=400, detail="The recognition threshold must be within0.0-0.9between")
                
                config.RECOGNITION_THRESHOLD = threshold_value
                config.set('face_recognition.recognition_threshold', threshold_value)
                success_messages.append(f"The recognition threshold has been updated to: {threshold_value}")
                logger.info(f"Update the face recognition threshold to: {threshold_value}")
            
            # Handling detection thresholds
            if "detection_threshold" in data:
                threshold_value = float(data["detection_threshold"])
                if not 0.1 <= threshold_value <= 0.9:
                    raise HTTPException(status_code=400, detail="The detection threshold must be within0.1-0.9between")
                
                config.DETECTION_THRESHOLD = threshold_value
                config.set('face_recognition.detection_threshold', threshold_value)
                success_messages.append(f"The detection threshold has been updated to: {threshold_value}")
                logger.info(f"Update the face detection threshold to: {threshold_value}")
            
            # Handling duplicate thresholds
            if "duplicate_threshold" in data:
                threshold_value = float(data["duplicate_threshold"])
                if not 0.8 <= threshold_value <= 0.99:
                    raise HTTPException(status_code=400, detail="Repeat threshold must be within0.8-0.99between")
                
                config.set('face_recognition.duplicate_threshold', threshold_value)
                success_messages.append(f"The duplicate threshold has been updated to: {threshold_value}")
                logger.info(f"Update the duplicate determination threshold to: {threshold_value}")
            
            # Save configuration to file
            if success_messages:
                try:
                    config.save()
                    logger.info("Configuration saved toconfig.jsondocument")
                except Exception as e:
                    logger.warning(f"Failed to save configuration file: {str(e)}")
                    # Don't throw an exception，Because the configuration in memory has been updated
            
            # Compatible with older version parameter names
            if "tolerance" in data and "recognition_threshold" not in data:
                threshold_value = float(data["tolerance"])
                if not 0.0 <= threshold_value <= 0.9:
                    raise HTTPException(status_code=400, detail="The recognition threshold must be within0.0-0.9between")
                
                config.RECOGNITION_THRESHOLD = threshold_value
                config.set('face_recognition.recognition_threshold', threshold_value)
                success_messages.append(f"The recognition threshold has been updated to: {threshold_value}")
                logger.info(f"Update the face recognition threshold to: {threshold_value}")
            
            if not success_messages:
                raise HTTPException(status_code=400, detail="No valid configuration parameter provided")
            
            return JSONResponse(content={
                "success": True,
                "message": "; ".join(success_messages),
                "recognition_threshold": getattr(config, 'RECOGNITION_THRESHOLD', 0.2),
                "detection_threshold": getattr(config, 'DETECTION_THRESHOLD', 0.5),
                "duplicate_threshold": config.get('face_recognition.duplicate_threshold', 0.95)
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update configuration: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update configuration")

    @app.delete("/api/face_encoding/{encoding_id}")
    async def delete_face_encoding(encoding_id: int, service = Depends(get_face_service)):
        """
        🗑️ Delete specified face code
        
        Delete the specified face feature vector，Supports separate deletion of multiple faces of the same person
        """
        try:
            success = service.db_manager.delete_face_encoding(encoding_id)
            if not success:
                raise HTTPException(status_code=404, detail="Face encoding does not exist")
            
            # No cache to clear - PostgreSQL handles everything
            
            return JSONResponse(content={
                "success": True,
                "message": "Face coding deleted successfully"
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete face encoding: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete face encoding")

    @app.delete("/api/person/{person_id}/faces/{face_encoding_id}")
    async def delete_person_face(person_id: int, face_encoding_id: int, service = Depends(get_face_service)):
        """
        🗑️ Delete the specified face of the specified person
        
        Delete a face photo of a specified person
        """
        try:
            with service.db_manager.get_session() as session:
                from ..models import Person, FaceEncoding
                
                # Verify whether the person exists
                person = session.query(Person).filter(Person.id == person_id).first()
                if not person:
                    raise HTTPException(status_code=404, detail="Personnel does not exist")
                
                # Get person name，Avoid subsequent session issues
                person_name = person.name
                
                # Verify whether the face code exists and belongs to that person
                face_encoding = session.query(FaceEncoding).filter(
                    FaceEncoding.id == face_encoding_id,
                    FaceEncoding.person_id == person_id
                ).first()
                
                if not face_encoding:
                    raise HTTPException(status_code=404, detail="The specified face does not exist or does not belong to the person")
                
                # Delete face code
                session.delete(face_encoding)
                session.commit()
            
            # No cache to clear - PostgreSQL handles everything
            
            return JSONResponse(content={
                "success": True,
                "message": f"Deleted {person_name} face photos"
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete person's face: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete person's face")

    @app.post("/api/person/{person_id}/faces")
    async def add_person_faces(
        person_id: int,
        faces: List[UploadFile] = File(..., description="Face image file list"),
        service = Depends(get_face_service)
    ):
        """
        📸 Add more face photos for specified people
        
        Add multiple face photos for existing people
        """
        try:
            person_name = ""  # Initialize person name variable
            
            with service.db_manager.get_session() as session:
                from ..models import Person
                
                # Verify whether the person exists
                person = session.query(Person).filter(Person.id == person_id).first()
                if not person:
                    raise HTTPException(status_code=404, detail="Personnel does not exist")
                
                # Save person name，Avoid session issues
                person_name = person.name
            
            success_count = 0
            error_count = 0
            results = []
            
            for i, face_file in enumerate(faces):
                try:
                    # Verify file type
                    if face_file.content_type and not face_file.content_type.startswith('image/'):
                        results.append({
                            'file_name': face_file.filename,
                            'success': False,
                            'error': 'Unsupported file types'
                        })
                        error_count += 1
                        continue
                    
                    # Save temporary files
                    content = await face_file.read()
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    temp_file.write(content)
                    temp_file.close()
                    
                    try:
                        # Use a facial recognition service to process the image and extract the encoding
                        # read image
                        image = cv2.imread(temp_file.name)
                        if image is None:
                            results.append({
                                'file_name': face_file.filename,
                                'success': False,
                                'error': 'Unable to read image file'
                            })
                            error_count += 1
                            continue
                        
                        # Detect faces and extract features
                        detected_faces = service.detect_faces(image)
                        if not detected_faces:
                            results.append({
                                'file_name': face_file.filename,
                                'success': False,
                                'error': 'No face detected'
                            })
                            error_count += 1
                            continue
                        
                        # Check if multiple faces are detected
                        if len(detected_faces) > 1:
                            results.append({
                                'file_name': face_file.filename,
                                'success': False,
                                'error': f'Multiple faces detected({len(detected_faces)}open)，Please provide a photo containing only one face'
                            })
                            error_count += 1
                            continue
                        
                        # Use detected faces
                        detected_face = detected_faces[0]
                        encoding = detected_face.get('embedding')
                        if encoding is None:
                            results.append({
                                'file_name': face_file.filename,
                                'success': False,
                                'error': 'Unable to extract facial features'
                            })
                            error_count += 1
                            continue
                        
                        # Check similarity - Avoid adding similar faces repeatedly
                        try:
                            # Check for similarity with existing faces of the current person
                            with service.db_manager.get_session() as check_session:
                                from ..models import FaceEncoding as FaceEncodingModel
                                existing_faces = check_session.query(FaceEncodingModel).filter(
                                    FaceEncodingModel.person_id == person_id
                                ).all()
                                
                                duplicate_threshold = config.get('face_recognition.duplicate_threshold', 0.85)
                                
                                for existing_face in existing_faces:
                                    if existing_face.embedding is not None:
                                        # Handle encoded data in different formats
                                        existing_encoding = None
                                        if isinstance(existing_face.embedding, bytes):
                                            try:
                                                existing_encoding = pickle.loads(existing_face.embedding)
                                            except Exception as e:
                                                logger.warning(f"Trait deserialization failed: {e}")
                                                continue
                                        elif isinstance(existing_face.embedding, np.ndarray):
                                            existing_encoding = existing_face.embedding
                                        elif isinstance(existing_face.embedding, (list, tuple)):
                                            existing_encoding = np.array(existing_face.embedding, dtype=np.float32)
                                        elif isinstance(existing_face.embedding, str):
                                            try:
                                                existing_encoding = np.frombuffer(
                                                    base64.b64decode(existing_face.embedding), 
                                                    dtype=np.float32
                                                )
                                            except Exception as e:
                                                logger.warning(f"Base64Decoding failed: {e}")
                                                continue
                                        else:
                                            logger.warning(f"Unknown encoding format: {type(existing_face.embedding)}")
                                            continue
                                        
                                        if existing_encoding is None or len(existing_encoding) == 0:
                                            continue
                                        
                                        # Calculate cosine similarity
                                        try:
                                            similarity = float(np.dot(encoding, existing_encoding) / 
                                                             (np.linalg.norm(encoding) * np.linalg.norm(existing_encoding)))
                                            
                                            if similarity > duplicate_threshold:
                                                results.append({
                                                    'file_name': face_file.filename,
                                                    'success': False,
                                                    'error': f'The face is too similar to an existing face (Similarity: {similarity*100:.1f}%，threshold: {duplicate_threshold*100:.1f}%)'
                                                })
                                                error_count += 1
                                                raise Exception("Duplicate faces")  # Jump out of current file processing
                                        except ValueError as ve:
                                            logger.warning(f"Similarity calculation failed: {ve}")
                                            continue
                                        except Exception as similarity_error:
                                            if "Duplicate faces" in str(similarity_error):
                                                raise  # Rethrow duplicate face error
                                            logger.warning(f"Similarity detection failed: {str(similarity_error)}")
                                            continue
                                
                                # Check similarities to other people’s faces
                                other_faces = check_session.query(FaceEncodingModel, Person).join(
                                    Person, FaceEncodingModel.person_id == Person.id
                                ).filter(
                                    FaceEncodingModel.person_id != person_id
                                ).all()
                                
                                for face_encoding, other_person in other_faces:
                                    if face_encoding.embedding is not None:
                                        # Handle encoded data in different formats
                                        other_encoding = None
                                        if isinstance(face_encoding.embedding, bytes):
                                            try:
                                                other_encoding = pickle.loads(face_encoding.embedding)
                                            except Exception as e:
                                                logger.warning(f"Trait deserialization failed: {e}")
                                                continue
                                        elif isinstance(face_encoding.embedding, np.ndarray):
                                            other_encoding = face_encoding.embedding
                                        elif isinstance(face_encoding.embedding, (list, tuple)):
                                            other_encoding = np.array(face_encoding.embedding, dtype=np.float32)
                                        elif isinstance(face_encoding.embedding, str):
                                            try:
                                                other_encoding = np.frombuffer(
                                                    base64.b64decode(face_encoding.embedding), 
                                                    dtype=np.float32
                                                )
                                            except Exception as e:
                                                logger.warning(f"Base64Decoding failed: {e}")
                                                continue
                                        else:
                                            logger.warning(f"Unknown encoding format: {type(face_encoding.embedding)}")
                                            continue
                                        
                                        if other_encoding is None or len(other_encoding) == 0:
                                            continue
                                        
                                        # Calculate cosine similarity
                                        try:
                                            similarity = float(np.dot(encoding, other_encoding) / 
                                                             (np.linalg.norm(encoding) * np.linalg.norm(other_encoding)))
                                            
                                            if similarity > duplicate_threshold:
                                                results.append({
                                                    'file_name': face_file.filename,
                                                    'success': False,
                                                    'error': f'The face is too similar to other people：{other_person.name} (Similarity: {similarity*100:.1f}%，threshold: {duplicate_threshold*100:.1f}%)'
                                                })
                                                error_count += 1
                                                raise Exception("Duplicate faces")  # Jump out of current file processing
                                        except ValueError as ve:
                                            logger.warning(f"Similarity calculation failed: {ve}")
                                            continue
                                        except Exception as similarity_error:
                                            if "Duplicate faces" in str(similarity_error):
                                                raise  # Rethrow duplicate face error
                                            logger.warning(f"Cross-person similarity detection failed: {str(similarity_error)}")
                                            continue
                        
                        except Exception as check_error:
                            if "Duplicate faces" in str(check_error):
                                # Duplicate face errors，Stop the entire batch immediately
                                logger.warning(f"Add face to person Duplicate detected，Stop processing: {str(check_error)}")
                                
                                # Get the last error result
                                last_error = results[-1] if results else {
                                    'file_name': face_file.filename,
                                    'success': False,
                                    'error': 'Duplicate faces detected'
                                }
                                
                                return JSONResponse(content={
                                    "success": False,
                                    "person_id": person_id,
                                    "person_name": person_name,
                                    "total_files": len(faces),
                                    "success_count": success_count,
                                    "error_count": 1,
                                    "count": success_count,
                                    "results": [last_error],
                                    "message": f"for {person_name} Failed to add face: {last_error.get('error', 'Duplicate faces detected')}. Please try again with a different face image。",
                                    "duplicate_detected": True
                                })
                            logger.warning(f"Similarity check failed: {str(check_error)}")
                        
                        # Read image data for storage
                        with open(temp_file.name, 'rb') as img_file:
                            image_data = img_file.read()
                        
                        # Add to database
                        face_encoding = service.db_manager.add_face_encoding(
                            person_id=person_id,
                            encoding=encoding,
                            image_path=face_file.filename,  # Store original file name
                            image_data=image_data,
                            face_bbox=str(detected_face.get('bbox', [])),
                            confidence=detected_face.get('det_score', 1.0),
                            quality_score=detected_face.get('quality', 1.0)
                        )
                        
                        results.append({
                            'file_name': face_file.filename,
                            'success': True,
                            'face_encoding_id': face_encoding.id,  # Use uniformlyface_encoding_idField name
                            'quality_score': detected_face.get('quality', 0),
                            'confidence': detected_face.get('det_score', 1.0),
                            'bbox': detected_face.get('bbox', [])
                        })
                        success_count += 1
                    finally:
                        # Clean temporary files
                        if os.path.exists(temp_file.name):
                            os.unlink(temp_file.name)
                
                except Exception as file_error:
                    results.append({
                        'file_name': face_file.filename,
                        'success': False,
                        'error': f"Processing file failed: {str(file_error)}"
                    })
                    error_count += 1
            
            return JSONResponse(content={
                "success": True,
                "person_id": person_id,
                "person_name": person_name,
                "total_files": len(faces),
                "success_count": success_count,
                "error_count": error_count,
                "count": success_count,  # Compatible with front-end
                "results": results,
                "message": f"for {person_name} Completed adding face：success {success_count} indivual，fail {error_count} indivual"
            })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to add person's face: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to add person's face")

    @app.post("/api/detect_faces")
    async def detect_faces(
        file: UploadFile = File(...),
        include_landmarks: bool = Query(default=False, description="Whether to include key point information"),
        include_attributes: bool = Query(default=False, description="Whether to include face attributes(age、gender)"),
        min_face_size: int = Query(default=20, description="Minimum face size(Pixel)")
    ):
        """
        🔍 Pure face detection interface
        
        Only perform face detection，No identification and warehousing operations are performed
        
        Args:
            file: Uploaded image file
            include_landmarks: Whether to return facial key point coordinates
            include_attributes: Whether to analyze facial attributes(age、gender)
            min_face_size: Minimum face size detected
            
        Returns:
            All detected facial information
        """
        try:
            # Verify file type - Read from configuration file
            allowed_extensions = config.get_allowed_extensions_with_dot()
            if file.filename and not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
                raise HTTPException(status_code=400, detail=f"Unsupported file format。Supported formats: {', '.join(allowed_extensions)}")
            
            # Read pictures
            image_data = await file.read()
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise HTTPException(status_code=400, detail="Unable to parse image file")
            
            # Get face detection service
            face_service = get_advanced_face_service()
            
            # Perform face detection
            faces = face_service.detect_faces(image)
            
            # Filter faces smaller than minimum size
            if min_face_size > 0:
                filtered_faces = []
                for face in faces:
                    bbox = face.get('bbox', [0, 0, 0, 0])
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    if width >= min_face_size and height >= min_face_size:
                        filtered_faces.append(face)
                faces = filtered_faces
            
            # Build return data
            result_faces = []
            for i, face in enumerate(faces):
                face_data = {
                    "face_id": i + 1,
                    "bbox": face.get('bbox', []),
                    "confidence": face.get('det_score', 0.0),
                    "quality_score": face.get('quality', 0.0)
                }
                
                # Add key point information
                if include_landmarks and 'landmarks' in face:
                    face_data["landmarks"] = face['landmarks']
                
                # Add attribute information
                if include_attributes:
                    if 'age' in face and face['age'] is not None:
                        face_data["age"] = int(face['age'])
                    if 'gender' in face and face['gender'] is not None:
                        face_data["gender"] = "male" if face['gender'] == 1 else "female"
                
                result_faces.append(face_data)
            
            return JSONResponse(content={
                "success": True,
                "message": f"detected {len(result_faces)} personal face",
                "total_faces": len(result_faces),
                "faces": result_faces,
                "image_info": {
                    "width": image.shape[1],
                    "height": image.shape[0],
                    "channels": image.shape[2] if len(image.shape) > 2 else 1
                },
                "detection_config": {
                    "detection_threshold": getattr(config, 'DETECTION_THRESHOLD', 0.5),
                    "min_face_size": min_face_size,
                    "model": "InsightFace Buffalo-L"
                }
            })
            
        except Exception as e:
            logger.error(f"Face detection failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Face detection failed: {str(e)}")

    @app.get("/health")
    @app.head("/health")
    async def health_check_docker():
        """Docker Health check interface"""
        try:
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

    @app.get("/api/health")
    @app.head("/api/health")
    async def health_check():
        """
        ❤️ Health check interface
        
        Check system operating status
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Advanced facial recognition system",
            "version": "2.0.0",
            "features": [
                "InsightFace High-precision detection",
                "DeepFace Multiple model support", 
                "Face attribute analysis",
                "RESTful API"
            ]
        }

    @app.get("/api/sync/status")
    async def sync_status():
        """
        🔄 Get moreWorkerSync status
        
        Display cache synchronization status and version information
        """
        try:
            face_service = get_face_service_instance()
            
            # Check if sync status is supported
            if hasattr(face_service, 'get_sync_status'):
                sync_info = face_service.get_sync_status()
                return {
                    "success": True,
                    "sync_enabled": True,
                    "sync_info": sync_info
                }
            else:
                return {
                    "success": True,
                    "sync_enabled": False,
                    "message": "The current service mode does not support multipleWorkersynchronous",
                    "service_type": type(face_service).__name__
                }
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")

    @app.post("/api/sync/refresh")
    async def force_sync_refresh():
        """
        🔄 Force refresh cache sync
        
        Manually trigger cache refresh，for debugging or emergency situations
        """
        try:
            face_service = get_face_service_instance()
            
            # Check if forced refresh is supported
            if hasattr(face_service, 'force_cache_refresh'):
                result = face_service.force_cache_refresh()
                return result
            else:
                return {
                    "success": False,
                    "error": "The current service mode does not support forced cache refresh",
                    "service_type": type(face_service).__name__
                }
        except Exception as e:
            logger.error(f"Forced cache refresh failed: {e}")
            raise HTTPException(status_code=500, detail=f"Forced cache refresh failed: {str(e)}")

    @app.get("/api/cache/info")
    async def cache_info():
        """
        📊 Get cache information
        
        Show current cache status and statistics
        """
        try:
            face_service = get_face_service_instance()
            
            # Get database statistics instead of cache
            db_stats = face_service.db_manager.get_statistics()
            
            cache_data = {
                "success": True,
                "cache_type": "PostgreSQL + pgvector",
                "service_type": type(face_service).__name__,
                "timestamp": datetime.now().isoformat(),
                "total_persons": db_stats.get('total_persons', 0),
                "total_encodings": db_stats.get('total_encodings', 0),
                "avg_photos_per_person": db_stats.get('avg_photos_per_person', 0),
                "region_counts": db_stats.get('region_counts', {})
            }
            
            return cache_data
            
        except Exception as e:
            logger.error(f"Failed to obtain cache information: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to obtain cache information: {str(e)}")

    # ==================== Attendance Endpoints ====================
    
    @app.post("/api/attendance/mark")
    async def mark_attendance(
        person_id: Optional[int] = Form(None, description="Person ID"),
        emp_id: Optional[str] = Form(None, description="Employee ID"),
        name: Optional[str] = Form(None, description="Person name"),
        date: Optional[str] = Form(None, description="Date (YYYY-MM-DD), defaults to today"),
        status: str = Form('present', description="Status: present or absent"),
        service = Depends(get_face_service)
    ):
        """
        📋 Mark attendance for a person
        
        Checks if attendance is already marked for today.
        Can identify person by person_id, emp_id, or name.
        """
        try:
            from datetime import datetime
            
            # Parse date or use today (normalize to midnight UTC)
            if date:
                attendance_date = datetime.strptime(date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                # Get today's date at midnight
                now = datetime.utcnow()
                attendance_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
            
            logger.info(f"Attendance mark request - person_id={person_id}, emp_id={emp_id}, name={name}, date={attendance_date}")
            
            # Find person by person_id, emp_id, or name
            person = None
            if person_id:
                person = service.db_manager.get_person_by_id(person_id)
            elif emp_id:
                # Find person by emp_id
                with service.db_manager.get_session() as session:
                    from ..models.database import Person
                    person = session.query(Person).filter(Person.emp_id == emp_id).first()
                    if person:
                        session.expunge(person)
            elif name:
                person = service.db_manager.get_person_by_name(name)
            
            if not person:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "error": "Person not found",
                        "already_marked": False
                    }
                )
            
            # Check if attendance already marked for today
            with service.db_manager.get_session() as session:
                from ..models.database import Attendance
                existing_attendance = session.query(Attendance).filter(
                    Attendance.person_id == person.id,
                    Attendance.date == attendance_date
                ).first()
                
                logger.info(f"Attendance check result - person_id={person.id}, existing={existing_attendance is not None}")
                
                if existing_attendance:
                    # Capture data before session closes
                    attendance_data = {
                        "id": existing_attendance.id,
                        "status": existing_attendance.status,
                        "marked_at": existing_attendance.marked_at.isoformat() if existing_attendance.marked_at else None,
                        "date": existing_attendance.date.isoformat() if existing_attendance.date else None
                    }
                    
                    # Attendance already marked - return immediately
                    logger.warning(f"⚠️  DUPLICATE DETECTED: Attendance already marked for {person.name} (ID={person.id}) on {attendance_date.date()}")
                    return JSONResponse(content={
                        "success": True,
                        "already_marked": True,
                        "message": "Attendance already marked for today",
                        "person": {
                            "id": person.id,
                            "name": person.name,
                            "emp_id": person.emp_id,
                            "emp_rank": person.emp_rank
                        },
                        "attendance": attendance_data
                    })
            
            # If we reach here, no existing attendance found
            logger.info(f"No existing attendance found, creating new record for person_id={person.id}")
            
            # Mark new attendance
            attendance = service.db_manager.mark_attendance(person.id, attendance_date, status)
            
            return JSONResponse(content={
                "success": True,
                "already_marked": False,
                "message": "Attendance marked successfully",
                "person": {
                    "id": person.id,
                    "name": person.name,
                    "emp_id": person.emp_id,
                    "emp_rank": person.emp_rank
                },
                "attendance": attendance.to_dict()
            })
        except Exception as e:
            logger.error(f"Failed to mark attendance: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to mark attendance: {str(e)}")
    
    @app.get("/api/attendance/debug/{person_id}")
    async def debug_attendance(
        person_id: int,
        service = Depends(get_face_service)
    ):
        """
        🔍 Debug endpoint to check attendance status
        """
        try:
            from datetime import datetime
            
            today = datetime.utcnow()
            attendance_date = datetime(today.year, today.month, today.day, 0, 0, 0, 0)
            
            person = service.db_manager.get_person_by_id(person_id)
            if not person:
                return JSONResponse(content={"error": "Person not found"})
            
            with service.db_manager.get_session() as session:
                from ..models.database import Attendance
                existing = session.query(Attendance).filter(
                    Attendance.person_id == person_id,
                    Attendance.date == attendance_date
                ).first()
                
                return JSONResponse(content={
                    "person_id": person_id,
                    "person_name": person.name,
                    "today_date": attendance_date.isoformat(),
                    "has_attendance": existing is not None,
                    "attendance": {
                        "id": existing.id if existing else None,
                        "status": existing.status if existing else None,
                        "marked_at": existing.marked_at.isoformat() if existing and existing.marked_at else None,
                        "date": existing.date.isoformat() if existing and existing.date else None
                    } if existing else None
                })
        except Exception as e:
            return JSONResponse(content={"error": str(e)})
    
    @app.get("/api/attendance/check")
    async def check_attendance(
        person_id: Optional[int] = Query(None, description="Person ID"),
        emp_id: Optional[str] = Query(None, description="Employee ID"),
        name: Optional[str] = Query(None, description="Person name"),
        date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), defaults to today"),
        service = Depends(get_face_service)
    ):
        """
        🔍 Check if attendance is already marked for a person
        """
        try:
            from datetime import datetime
            
            # Parse date or use today
            if date:
                attendance_date = datetime.strptime(date, '%Y-%m-%d')
            else:
                attendance_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Find person by person_id, emp_id, or name
            person = None
            if person_id:
                person = service.db_manager.get_person_by_id(person_id)
            elif emp_id:
                with service.db_manager.get_session() as session:
                    from ..models.database import Person
                    person = session.query(Person).filter(Person.emp_id == emp_id).first()
                    if person:
                        session.expunge(person)
            elif name:
                person = service.db_manager.get_person_by_name(name)
            
            if not person:
                return JSONResponse(content={
                    "success": False,
                    "error": "Person not found",
                    "is_marked": False
                })
            
            # Check if attendance exists
            with service.db_manager.get_session() as session:
                from ..models.database import Attendance
                existing_attendance = session.query(Attendance).filter(
                    Attendance.person_id == person.id,
                    Attendance.date == attendance_date
                ).first()
                
                if existing_attendance:
                    return JSONResponse(content={
                        "success": True,
                        "is_marked": True,
                        "person": {
                            "id": person.id,
                            "name": person.name,
                            "emp_id": person.emp_id,
                            "emp_rank": person.emp_rank
                        },
                        "attendance": {
                            "id": existing_attendance.id,
                            "status": existing_attendance.status,
                            "marked_at": existing_attendance.marked_at.isoformat() if existing_attendance.marked_at else None,
                            "date": existing_attendance.date.isoformat() if existing_attendance.date else None
                        }
                    })
                else:
                    return JSONResponse(content={
                        "success": True,
                        "is_marked": False,
                        "person": {
                            "id": person.id,
                            "name": person.name,
                            "emp_id": person.emp_id,
                            "emp_rank": person.emp_rank
                        }
                    })
        except Exception as e:
            logger.error(f"Failed to check attendance: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to check attendance: {str(e)}")
    
    @app.get("/api/attendance")
    async def get_attendance(
        date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), defaults to today"),
        region: Optional[str] = Query(None, description="Region filter (ka/ap/tn)"),
        service = Depends(get_face_service)
    ):
        """
        📋 Get attendance records for a specific date
        """
        try:
            from datetime import datetime
            
            # Parse date or use today
            if date:
                attendance_date = datetime.strptime(date, '%Y-%m-%d')
            else:
                attendance_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get all persons with attendance status
            records = service.db_manager.get_all_persons_with_attendance(attendance_date, region)
            
            return JSONResponse(content={
                "success": True,
                "date": attendance_date.strftime('%Y-%m-%d'),
                "region": region or "all",
                "total": len(records),
                "present": len([r for r in records if r['status'] == 'present']),
                "absent": len([r for r in records if r['status'] == 'absent']),
                "records": records
            })
        except Exception as e:
            logger.error(f"Failed to get attendance: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get attendance: {str(e)}")

    return app

def draw_chinese_text(img, text, position, font_size=20, color=(255, 255, 255)):
    """
    Draw Chinese text on image，Use a unified font manager
    """
    try:
        # Convert toPILimage
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        # Get the font manager and load fonts
        font_manager = get_font_manager()
        font = font_manager.get_font(font_size)
        
        if font is None:
            # If the font manager cannot provide the font，useOpenCVdraw
            cv2.putText(img, str(text), position, cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            return img
        
        # Add text background to improve readability
        try:
            bbox = draw.textbbox(position, text, font=font)
            # Draw a semi-transparent background
            overlay = Image.new('RGBA', img_pil.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2], 
                                 fill=(0, 0, 0, 128))  # translucent black background
            img_pil = Image.alpha_composite(img_pil.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img_pil)
        except:
            pass  # If background drawing fails，Continue drawing text
        
        # Draw text
        draw.text(position, text, font=font, fill=color)
        
        # Convert backOpenCVFormat
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
    except Exception as e:
        # ifPILcomplete failure，useOpenCVdraw
        logger.error(f"Failed to draw Chinese text: {e}")
        try:
            # Try encoding asASCII，If failed, the English alternative will be displayed.
            display_text = text.encode('ascii', 'ignore').decode('ascii')
            if not display_text.strip():
                display_text = "Chinese Name"
        except:
            display_text = "Name"
        
        cv2.putText(img, display_text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        return img

# Create application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)

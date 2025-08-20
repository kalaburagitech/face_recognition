"""
基于 FastAPI 的先进人脸识别 API 接口
支持 InsightFace 和 DeepFace 等最新技术
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
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ..services.advanced_face_service import get_advanced_face_service
from ..utils.config import config, get_upload_config
from src.utils.enhanced_visualization import EnhancedFaceVisualizer
from src.utils.font_manager import get_font_manager

logger = logging.getLogger(__name__)

# Pydantic 模型
class PersonCreate(BaseModel):
    name: str = Field(..., description="人员姓名", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="人员描述", max_length=500)

class PersonUpdate(BaseModel):
    name: Optional[str] = Field(None, description="人员姓名", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="人员描述", max_length=500)

class FaceMatch(BaseModel):
    person_id: int
    name: str
    match_score: float = Field(description="匹配度百分比 (0-100%)")
    distance: float = Field(description="欧氏距离，越小越相似")
    model: str
    bbox: List[int] = Field(description="人脸边界框 [x1, y1, x2, y2]")
    quality: float
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
    person_name: Optional[str] = None
    description: Optional[str] = None
    faces_detected: Optional[int] = None
    face_quality: Optional[float] = None
    processing_time: Optional[float] = None
    feature_dim: Optional[int] = None
    embeddings_count: Optional[int] = None
    visualized_image: Optional[str] = None  # Base64 编码的检测可视化图像
    face_details: Optional[List[Dict]] = None  # 人脸详细信息列表
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

def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="先进人脸识别系统 API",
        description="基于 InsightFace 和 DeepFace 的高精度人脸识别系统",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 挂载静态文件
    web_dir = Path(__file__).parent.parent.parent / "web"
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")
        # 挂载新的assets目录
        assets_dir = web_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # 获取服务实例
    def get_face_service():
        return get_advanced_face_service()
    
    # 创建全局可视化器实例
    visualizer = EnhancedFaceVisualizer()

    @app.get("/", response_class=HTMLResponse)
    async def root():
        """主页"""
        web_file = Path(__file__).parent.parent.parent / "web" / "index.html"
        if web_file.exists():
            return FileResponse(str(web_file))
        else:
            return HTMLResponse("""
            <html>
                <head><title>先进人脸识别系统</title></head>
                <body style="font-family: Arial, sans-serif; margin: 40px;">
                    <h1>🚀 先进人脸识别系统 API</h1>
                    <p>基于 <strong>InsightFace</strong> 和 <strong>DeepFace</strong> 的高精度人脸识别</p>
                    <p><a href="/docs">📋 查看API文档</a></p>
                </body>
            </html>
            """)

    @app.get("/{file_path}.html", response_class=HTMLResponse)
    async def serve_html(file_path: str):
        """服务HTML文件"""
        web_file = Path(__file__).parent.parent.parent / "web" / f"{file_path}.html"
        if web_file.exists():
            return FileResponse(str(web_file))
        else:
            raise HTTPException(status_code=404, detail="页面未找到")

    @app.post("/api/enroll", response_model=EnrollmentResponse)
    async def enroll_person(
        file: UploadFile = File(..., description="人脸图像文件"),
        name: str = Form(..., description="人员姓名"),
        description: Optional[str] = Form(None, description="人员描述"),
        service = Depends(get_face_service)
    ):
        """
        🔐 人员入库接口
        
        上传人脸图像进行人员注册入库
        """
        try:
            # 验证文件类型
            if file.content_type and not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="只支持图像文件")

            # 保存临时文件
            upload_config = get_upload_config()
            
            # 检查文件大小
            content = await file.read()
            file_size = len(content)
            
            max_size = 10 * 1024 * 1024  # 10MB 默认值
            if upload_config and isinstance(upload_config, dict):
                max_size = upload_config.get('MAX_FILE_SIZE', max_size)
            
            # 确保 max_size 是整数
            if isinstance(max_size, (int, float)):
                if file_size > max_size:
                    raise HTTPException(status_code=400, detail="文件太大")
            else:
                # 如果配置有问题，使用默认值
                if file_size > 10 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail="文件太大")

            # 保存临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(content)
            temp_file.close()

            try:
                # 调用服务进行入库
                import time
                start_time = time.time()
                result = service.enroll_person(name, temp_file.name, description, file.filename)
                processing_time = time.time() - start_time
                
                if result['success']:
                    # 生成人脸检测可视化图像
                    visualized_image = None
                    face_details = None
                    
                    try:
                        # 调用可视化接口生成检测图像
                        visual_result = service.visualize_face_detection(temp_file.name)
                        if visual_result['success'] and 'image_base64' in visual_result:
                            visualized_image = visual_result['image_base64']
                            face_details = visual_result.get('faces', [])
                    except Exception as e:
                        print(f"生成可视化图像失败: {e}")
                    
                    return EnrollmentResponse(
                        success=True,
                        person_id=int(result['person_id']),
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
                # 清理临时文件
                os.unlink(temp_file.name)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"入库接口错误: {str(e)}")
            return EnrollmentResponse(
                success=False,
                error=f"服务器内部错误: {str(e)}"
            )

    @app.post("/api/batch_enroll")
    async def batch_enroll_persons(
        files: List[UploadFile] = File(..., description="人脸图像文件列表"),
        names: Optional[List[str]] = Form(None, description="人员姓名列表（可选，如未提供则从文件名提取）"),
        descriptions: Optional[List[str]] = Form(None, description="人员描述列表（可选）"),
        sort_by_filename: bool = Form(True, description="是否按文件名排序处理"),
        service = Depends(get_face_service)
    ):
        """
        🔐 批量人员入库接口
        
        批量上传人脸图像进行人员注册入库
        支持从文件名自动提取人员姓名
        默认按文件名排序，确保处理顺序一致性
        """
        try:
            if not files:
                raise HTTPException(status_code=400, detail="请至少上传一个文件")
            
            # 如果启用文件名排序，按文件名对文件进行排序
            file_items = []
            for i, file in enumerate(files):
                file_items.append({
                    'file': file,
                    'original_index': i,
                    'filename': file.filename or f"unnamed_file_{i+1}"
                })
            
            if sort_by_filename:
                # 按文件名排序，确保数字编号文件按正确顺序处理
                file_items.sort(key=lambda x: x['filename'])
                logger.info(f"批量入库：按文件名排序，处理顺序: {[item['filename'] for item in file_items]}")
            
            results = []
            success_count = 0
            error_count = 0
            
            # 处理姓名列表 - 支持灵活的姓名分配
            names_list: List[Optional[str]] = []
            if names:
                # 如果提供了姓名，先使用提供的姓名，不足的部分后续用文件名补充
                names_list = list(names)
                logger.info(f"批量入库：收到 {len(names)} 个姓名，共 {len(files)} 个文件")
            else:
                # 如果没有提供姓名，全部使用文件名
                names_list = []
                logger.info(f"批量入库：未提供姓名，将使用文件名作为姓名")
            
            # 扩展描述列表以匹配文件数量
            desc_list: List[Optional[str]] = []
            if descriptions:
                desc_list = list(descriptions)
                while len(desc_list) < len(files):
                    desc_list.append(None)
            else:
                desc_list = [None] * len(files)
            
            for i, item in enumerate(file_items):
                file = item['file']
                original_index = item['original_index']
                # 在处理开始时立即保存文件名，避免后续状态变化
                original_filename = item['filename']
                name = "unknown"  # 初始化默认值
                
                logger.info(f"处理文件 {i+1}/{len(file_items)}: {original_filename}")
                
                try:
                    # 验证文件类型
                    if file.content_type and not file.content_type.startswith('image/'):
                        results.append({
                            'file_name': original_filename,
                            'success': False,
                            'error': '不支持的文件类型'
                        })
                        error_count += 1
                        continue

                    # 获取人员姓名 - 灵活处理姓名分配
                    if names_list and len(names_list) > 0 and names_list[0]:
                        # 如果提供了姓名，所有文件都使用这个姓名
                        name = names_list[0].strip()
                    else:
                        # 如果没有提供姓名，从文件名提取姓名（去除扩展名）
                        name = os.path.splitext(original_filename)[0]
                        # 清理文件名作为姓名
                        name = name.replace('_', ' ').replace('-', ' ').strip()
                        if not name or name.startswith("unnamed_file_"):
                            name = f"person_{i+1}"
                    
                    # 获取描述
                    description = desc_list[original_index] if original_index < len(desc_list) else None

                    # 检查文件大小
                    content = await file.read()
                    file_size = len(content)
                    
                    max_size = 10 * 1024 * 1024  # 10MB
                    if file_size > max_size:
                        results.append({
                            'file_name': original_filename,
                            'name': name,
                            'success': False,
                            'error': '文件太大'
                        })
                        error_count += 1
                        continue

                    # 保存临时文件
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    temp_file.write(content)
                    temp_file.close()

                    try:
                        # 调用服务进行入库，传入原始文件名以便正确存储
                        result = service.enroll_person(name, temp_file.name, description, original_filename)
                        
                        if result['success']:
                            results.append({
                                'file_name': original_filename,
                                'name': name,
                                'person_id': result.get('person_id'),
                                'success': True,
                                'quality_score': result.get('quality_score', 0)
                            })
                            success_count += 1
                        else:
                            results.append({
                                'file_name': original_filename,
                                'name': name,
                                'success': False,
                                'error': result.get('error', '入库失败')
                            })
                            error_count += 1
                            
                    finally:
                        # 删除临时文件
                        if os.path.exists(temp_file.name):
                            os.unlink(temp_file.name)
                            
                except Exception as file_error:
                    results.append({
                        'file_name': original_filename,
                        'name': name,
                        'success': False,
                        'error': f"处理文件失败: {str(file_error)}"
                    })
                    error_count += 1

            return {
                'success': True,
                'total_files': len(files),
                'success_count': success_count,
                'error_count': error_count,
                'results': results,
                'message': f"批量入库完成：成功 {success_count} 个，失败 {error_count} 个"
            }
            
        except Exception as e:
            logger.error(f"批量入库接口错误: {str(e)}")
            return {
                'success': False,
                'error': f"批量入库失败: {str(e)}",
                'total_files': len(files) if files else 0,
                'success_count': 0,
                'error_count': len(files) if files else 0,
                'results': []
            }

    @app.post("/api/recognize", response_model=RecognitionResponse)
    async def recognize_face(
        file: UploadFile = File(..., description="待识别的图像文件"),
        service = Depends(get_face_service)
    ):
        """
        🔍 人脸识别接口
        
        上传图像进行人脸识别，返回匹配的人员信息
        """
        try:
            # 从配置文件读取识别阈值
            import json
            try:
                with open('config.json', 'r') as f:
                    config_data = json.load(f)
                    threshold = config_data.get('face_recognition', {}).get('recognition_threshold', 0.3)
            except:
                threshold = 0.3  # 默认值
            
            # 验证文件类型
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="只支持图像文件")

            # 保存临时文件
            content = await file.read()
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(content)
            temp_file.close()

            try:
                # 读取图像
                image = cv2.imread(temp_file.name)
                if image is None:
                    raise HTTPException(status_code=400, detail="无法解析图像")
                
                # 调用服务进行识别（使用动态阈值）
                result = service.recognize_face_with_threshold(image, threshold)
                
                if result['success']:
                    matches = [
                        FaceMatch(
                            person_id=match['person_id'],
                            name=match['name'],
                            match_score=match['match_score'],
                            distance=match['distance'],
                            model=match['model'],
                            bbox=match['bbox'],
                            quality=match['quality']
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
                # 清理临时文件
                os.unlink(temp_file.name)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"识别接口错误: {str(e)}")
            return RecognitionResponse(
                success=False,
                matches=[],
                total_faces=0,
                error=f"服务器内部错误: {str(e)}"
            )

    @app.post("/api/recognize_visual", summary="人脸识别（带可视化）")
    async def recognize_face_with_visualization(
        file: UploadFile = File(..., description="待识别的图像文件"),
        threshold: Optional[float] = None,
        service = Depends(get_face_service)
    ):
        """
        🔍 人脸识别接口（带可视化）
        
        上传图像进行人脸识别，返回标注了检测框和匹配信息的图像
        如果不提供阈值参数，将使用配置文件中的识别阈值
        """
        try:
            # 如果没有提供阈值，从配置文件读取
            if threshold is None:
                import json
                try:
                    with open('config.json', 'r') as f:
                        config_data = json.load(f)
                        threshold = config_data.get('face_recognition', {}).get('recognition_threshold', 0.25)
                except:
                    threshold = 0.25  # 默认值，与配置文件一致
            # 验证文件类型
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="只支持图像文件")

            # 读取图像
            content = await file.read()
            nparr = np.frombuffer(content, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise HTTPException(status_code=400, detail="无法解析图像")

            # 调用服务进行识别（使用动态阈值）
            result = service.recognize_face_with_threshold(image, threshold)
            
            if result['success']:
                # 确保threshold不为None（此时已经被赋值）
                assert threshold is not None, "threshold should not be None at this point"
                
                # 使用增强可视化器生成可视化图像
                visual_result = visualizer.visualize_recognition_results(
                    image, result['matches'], threshold
                )
                
                if visual_result['success']:
                    # 将base64图像转换为临时文件
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
                        # 清理临时文件（延迟删除）
                        asyncio.create_task(cleanup_temp_file(temp_file.name))
                else:
                    raise HTTPException(status_code=500, detail="可视化生成失败")
            else:
                raise HTTPException(status_code=400, detail=result.get('error', '识别失败'))

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"可视化识别接口错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

    async def cleanup_temp_file(file_path: str):
        """延迟清理临时文件"""
        await asyncio.sleep(1)  # 等待1秒确保文件已被下载
        try:
            os.unlink(file_path)
        except:
            pass

    @app.post("/api/analyze", response_model=AttributeAnalysisResponse)
    async def analyze_face_attributes(
        file: UploadFile = File(..., description="待分析的图像文件"),
        service = Depends(get_face_service)
    ):
        """
        🎭 人脸属性分析接口
        
        分析人脸的年龄、性别、情绪、种族等属性
        """
        try:
            # 验证文件类型
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="只支持图像文件")

            # 读取图像
            content = await file.read()
            nparr = np.frombuffer(content, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise HTTPException(status_code=400, detail="无法解析图像")

            # 调用服务分析属性
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
            logger.error(f"属性分析接口错误: {str(e)}")
            return AttributeAnalysisResponse(
                success=False,
                faces=[],
                total_faces=0,
                error=f"服务器内部错误: {str(e)}"
            )

    @app.get("/api/statistics")
    async def get_statistics(service = Depends(get_face_service)):
        """
        📊 获取系统统计信息
        
        返回系统的人员数量、模型分布等统计数据及系统配置
        """
        try:
            stats = service.get_statistics()
            
            # 添加系统配置信息
            from ..utils.config import config
            stats['system_config'] = {
                'recognition_threshold': {
                    'current': getattr(config, 'RECOGNITION_THRESHOLD', 0.6),
                    'min': 0.0,
                    'max': 0.9,
                    'step': 0.05,
                    'description': '识别阈值：控制人脸识别的严格程度，值越高识别越严格'
                },
                'detection_threshold': {
                    'current': getattr(config, 'DETECTION_THRESHOLD', 0.5),
                    'min': 0.1,
                    'max': 0.9,
                    'step': 0.05,
                    'description': '检测阈值：控制人脸检测的敏感度，值越高检测越严格'
                },
                'duplicate_threshold': {
                    'current': config.get('face_recognition.duplicate_threshold', 0.95),
                    'min': 0.8,
                    'max': 0.99,
                    'step': 0.01,
                    'description': '重复入库阈值：相似度超过此值的人脸将被拒绝入库，防止重复'
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
            logger.error(f"获取统计信息失败: {str(e)}")
            raise HTTPException(status_code=500, detail="获取统计信息失败")

    @app.post("/api/config/threshold")
    async def update_threshold(threshold: float = Form(...)):
        """
        🔧 更新识别阈值配置
        
        Args:
            threshold: 新的识别阈值 (0.0-0.9)
        """
        try:
            if not 0.0 <= threshold <= 0.9:
                raise HTTPException(status_code=400, detail="阈值必须在0.0-0.9之间")
            
            # 更新配置
            from ..utils.config import config
            config.RECOGNITION_THRESHOLD = threshold
            
            return JSONResponse(content={
                "success": True,
                "message": f"识别阈值已更新为 {threshold}",
                "new_threshold": threshold
            })
        except Exception as e:
            logger.error(f"更新阈值失败: {str(e)}")
            raise HTTPException(status_code=500, detail="更新阈值失败")

    @app.post("/api/config/duplicate_threshold")
    async def update_duplicate_threshold(threshold: float = Form(...)):
        """
        🔧 更新重复入库阈值配置
        
        Args:
            threshold: 新的重复入库阈值 (0.8-0.99)
        """
        try:
            if not 0.8 <= threshold <= 0.99:
                raise HTTPException(status_code=400, detail="重复入库阈值必须在0.8-0.99之间")
            
            # 更新配置
            from ..utils.config import config
            config.set('face_recognition.duplicate_threshold', threshold)
            
            return JSONResponse(content={
                "success": True,
                "message": f"重复入库阈值已更新为 {threshold:.2f}",
                "new_threshold": threshold
            })
        except Exception as e:
            logger.error(f"更新重复入库阈值失败: {str(e)}")
            raise HTTPException(status_code=500, detail="更新重复入库阈值失败")

    @app.get("/api/persons")
    async def get_persons(include_image_info: bool = Query(False, description="是否包含图片信息"), service = Depends(get_face_service)):
        """
        👥 获取所有人员列表
        
        返回系统中所有已录入的人员信息，可选择包含原始文件名等图片信息
        """
        try:
            with service.db_manager.get_session() as session:
                from ..models import Person
                persons = session.query(Person).all()
                
                persons_data = []
                for person in persons:
                    # 获取该人员的编码数量
                    from ..models import FaceEncoding
                    encodings = session.query(FaceEncoding).filter(
                        FaceEncoding.person_id == person.id
                    ).all()
                    
                    encoding_count = len(encodings)
                    
                    # 获取第一个人脸编码作为头像
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
                        "face_count": encoding_count,  # 兼容字段
                        "face_image_url": face_image_url
                    }
                    
                    # 如果请求包含图片信息，添加详细的图片文件名信息
                    if include_image_info and encodings:
                        person_data["image_files"] = []
                        for encoding in encodings:
                            person_data["image_files"].append({
                                "encoding_id": encoding.id,
                                "original_filename": encoding.image_path,  # 现在存储的是原始文件名
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
                
                # 如果包含图片信息，添加统计摘要
                if include_image_info:
                    total_images = sum(len(p.get("image_files", [])) for p in persons_data)
                    response_data["image_summary"] = {
                        "total_images": total_images,
                        "persons_with_multiple_images": len([p for p in persons_data if len(p.get("image_files", [])) > 1])
                    }
                
                return JSONResponse(content=response_data)
        except Exception as e:
            logger.error(f"获取人员列表失败: {str(e)}")
            raise HTTPException(status_code=500, detail="获取人员列表失败")

    @app.get("/api/person/{person_id}")
    async def get_person(person_id: int, service = Depends(get_face_service)):
        """
        👤 获取指定人员详情
        
        返回指定人员的详细信息和人脸编码数量
        """
        try:
            with service.db_manager.get_session() as session:
                from ..models import Person, FaceEncoding
                person = session.query(Person).filter(Person.id == person_id).first()
                
                if not person:
                    raise HTTPException(status_code=404, detail="人员不存在")
                
                # 获取人脸编码数量
                encoding_count = session.query(FaceEncoding).filter(FaceEncoding.person_id == person_id).count()
                
                return JSONResponse(content={
                    "success": True,
                    "person": {
                        "id": person.id,
                        "name": person.name,
                        "description": person.description,
                        "created_at": person.created_at.isoformat() if person.created_at else None,
                        "updated_at": person.updated_at.isoformat() if person.updated_at else None,
                        "encoding_count": encoding_count
                    }
                })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取人员详情失败: {str(e)}")
            raise HTTPException(status_code=500, detail="获取人员详情失败")

    @app.get("/api/person/{person_id}/faces")
    async def get_person_faces(person_id: int, service = Depends(get_face_service)):
        """
        👤 获取指定人员的所有人脸编码
        
        返回指定人员的所有人脸特征向量信息
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
            logger.error(f"获取人员人脸列表失败: {str(e)}")
            raise HTTPException(status_code=500, detail="获取人员人脸列表失败")

    @app.api_route("/api/face/{face_id}/image", methods=["GET", "HEAD"])
    async def get_face_image(face_id: int, request: Request, service = Depends(get_face_service)):
        """
        🖼️ 获取人脸图片
        
        返回指定人脸编码的图片数据
        """
        try:
            with service.db_manager.get_session() as session:
                repo = service.db_manager.get_face_encoding_repository(session)
                encoding = repo.get_by_id(face_id)
                if not encoding:
                    raise HTTPException(status_code=404, detail="未找到指定人脸编码")
                
                image_data = encoding.get_image_data()
                if not image_data:
                    raise HTTPException(status_code=404, detail="该人脸编码没有关联的图片数据")
                
                # 对于HEAD请求，只返回headers，不返回内容
                if request.method == "HEAD":
                    return Response(
                        content="",
                        media_type="image/jpeg",
                        headers={
                            "Cache-Control": "max-age=3600",
                            "Content-Length": str(len(image_data))
                        }
                    )
                
                # 对于GET请求，返回图片数据
                return Response(
                    content=image_data,
                    media_type="image/jpeg",
                    headers={"Cache-Control": "max-age=3600"}
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取人脸图片失败: {str(e)}")
            raise HTTPException(status_code=500, detail="获取人脸图片失败")
    
    @app.get("/api/face_image/{face_id}")
    async def get_face_image_legacy(face_id: int, service = Depends(get_face_service)):
        """
        🖼️ 获取人脸图片（兼容接口）
        
        返回指定人脸编码的图片数据
        """
        return await get_face_image(face_id, service)

    @app.put("/api/person/{person_id}")
    async def update_person(person_id: int, person_data: PersonUpdate, service = Depends(get_face_service)):
        """
        ✏️ 更新指定人员信息
        
        更新人员的基本信息（姓名、部门、职位、备注等）
        """
        try:
            with service.db_manager.get_session() as session:
                from ..models import Person
                
                # 查找人员
                person = session.query(Person).filter(Person.id == person_id).first()
                if not person:
                    raise HTTPException(status_code=404, detail="未找到指定人员")
                
                # 更新字段（只更新非None的字段）
                update_data = person_data.dict(exclude_unset=True)
                for field, value in update_data.items():
                    if hasattr(person, field):
                        setattr(person, field, value)
                
                person.updated_at = datetime.utcnow()
                session.commit()
                
                # 返回更新后的人员信息
                return JSONResponse(content={
                    "success": True,
                    "message": "人员信息更新成功",
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
            logger.error(f"更新人员信息失败: {str(e)}")
            raise HTTPException(status_code=500, detail="更新人员信息失败")

    @app.delete("/api/person/{person_id}")
    async def delete_person(person_id: int, service = Depends(get_face_service)):
        """
        🗑️ 删除指定人员
        
        删除指定人员及其所有人脸编码
        """
        try:
            with service.db_manager.get_session() as session:
                from ..models import Person, FaceEncoding
                
                # 检查人员是否存在
                person = session.query(Person).filter(Person.id == person_id).first()
                if not person:
                    raise HTTPException(status_code=404, detail="人员不存在")
                
                # 删除人脸编码
                session.query(FaceEncoding).filter(FaceEncoding.person_id == person_id).delete()
                
                # 删除人员
                session.delete(person)
                session.commit()
                
                # 从缓存中移除
                if person_id in service._face_cache:
                    del service._face_cache[person_id]
                
                return JSONResponse(content={
                    "success": True,
                    "message": f"人员 {person.name} 已删除"
                })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除人员失败: {str(e)}")
            raise HTTPException(status_code=500, detail="删除人员失败")

    @app.get("/api/config")
    async def get_config():
        """
        ⚙️ 获取系统配置
        
        返回系统配置信息
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
            logger.error(f"获取配置失败: {str(e)}")
            raise HTTPException(status_code=500, detail="获取配置失败")

    @app.post("/api/config")
    async def update_config(request: Request):
        """
        ⚙️ 更新系统配置
        
        更新人脸识别阈值等配置，支持多种参数名称兼容
        """
        try:
            from ..utils.config import config
            data = await request.json()
            
            success_messages = []
            
            # 处理识别阈值
            if "recognition_threshold" in data:
                threshold_value = float(data["recognition_threshold"])
                if not 0.0 <= threshold_value <= 0.9:
                    raise HTTPException(status_code=400, detail="识别阈值必须在0.0-0.9之间")
                
                config.RECOGNITION_THRESHOLD = threshold_value
                config.set('face_recognition.recognition_threshold', threshold_value)
                success_messages.append(f"识别阈值已更新为: {threshold_value}")
                logger.info(f"更新人脸识别阈值为: {threshold_value}")
            
            # 处理检测阈值
            if "detection_threshold" in data:
                threshold_value = float(data["detection_threshold"])
                if not 0.1 <= threshold_value <= 0.9:
                    raise HTTPException(status_code=400, detail="检测阈值必须在0.1-0.9之间")
                
                config.DETECTION_THRESHOLD = threshold_value
                config.set('face_recognition.detection_threshold', threshold_value)
                success_messages.append(f"检测阈值已更新为: {threshold_value}")
                logger.info(f"更新人脸检测阈值为: {threshold_value}")
            
            # 处理重复阈值
            if "duplicate_threshold" in data:
                threshold_value = float(data["duplicate_threshold"])
                if not 0.8 <= threshold_value <= 0.99:
                    raise HTTPException(status_code=400, detail="重复阈值必须在0.8-0.99之间")
                
                config.set('face_recognition.duplicate_threshold', threshold_value)
                success_messages.append(f"重复阈值已更新为: {threshold_value}")
                logger.info(f"更新重复判定阈值为: {threshold_value}")
            
            # 保存配置到文件
            if success_messages:
                try:
                    config.save()
                    logger.info("配置已保存到config.json文件")
                except Exception as e:
                    logger.warning(f"保存配置文件失败: {str(e)}")
                    # 不抛出异常，因为内存中的配置已更新
            
            # 兼容旧版参数名
            if "tolerance" in data and "recognition_threshold" not in data:
                threshold_value = float(data["tolerance"])
                if not 0.0 <= threshold_value <= 0.9:
                    raise HTTPException(status_code=400, detail="识别阈值必须在0.0-0.9之间")
                
                config.RECOGNITION_THRESHOLD = threshold_value
                config.set('face_recognition.recognition_threshold', threshold_value)
                success_messages.append(f"识别阈值已更新为: {threshold_value}")
                logger.info(f"更新人脸识别阈值为: {threshold_value}")
            
            if not success_messages:
                raise HTTPException(status_code=400, detail="未提供有效的配置参数")
            
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
            logger.error(f"更新配置失败: {str(e)}")
            raise HTTPException(status_code=500, detail="更新配置失败")

    @app.delete("/api/face_encoding/{encoding_id}")
    async def delete_face_encoding(encoding_id: int, service = Depends(get_face_service)):
        """
        🗑️ 删除指定人脸编码
        
        删除指定的人脸特征向量，支持同一人员多张人脸的单独删除
        """
        try:
            success = service.db_manager.delete_face_encoding(encoding_id)
            if not success:
                raise HTTPException(status_code=404, detail="人脸编码不存在")
            
            # 清除缓存并重新加载
            service._face_cache.clear()
            service._load_face_cache()
            
            return JSONResponse(content={
                "success": True,
                "message": "人脸编码删除成功"
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除人脸编码失败: {str(e)}")
            raise HTTPException(status_code=500, detail="删除人脸编码失败")

    @app.delete("/api/person/{person_id}/faces/{face_id}")
    async def delete_person_face(person_id: int, face_id: int, service = Depends(get_face_service)):
        """
        🗑️ 删除指定人员的指定人脸
        
        删除指定人员的某张人脸照片
        """
        try:
            with service.db_manager.get_session() as session:
                from ..models import Person, FaceEncoding
                
                # 验证人员是否存在
                person = session.query(Person).filter(Person.id == person_id).first()
                if not person:
                    raise HTTPException(status_code=404, detail="人员不存在")
                
                # 获取人员姓名，避免后续会话问题
                person_name = person.name
                
                # 验证人脸编码是否存在且属于该人员
                face_encoding = session.query(FaceEncoding).filter(
                    FaceEncoding.id == face_id,
                    FaceEncoding.person_id == person_id
                ).first()
                
                if not face_encoding:
                    raise HTTPException(status_code=404, detail="指定人脸不存在或不属于该人员")
                
                # 删除人脸编码
                session.delete(face_encoding)
                session.commit()
            
            # 在会话外清除缓存并重新加载
            service._face_cache.clear()
            service._load_face_cache()
            
            return JSONResponse(content={
                "success": True,
                "message": f"已删除 {person_name} 的人脸照片"
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除人员人脸失败: {str(e)}")
            raise HTTPException(status_code=500, detail="删除人员人脸失败")

    @app.post("/api/person/{person_id}/faces")
    async def add_person_faces(
        person_id: int,
        faces: List[UploadFile] = File(..., description="人脸图像文件列表"),
        service = Depends(get_face_service)
    ):
        """
        📸 为指定人员添加更多人脸照片
        
        为已存在的人员添加多张人脸照片
        """
        try:
            person_name = ""  # 初始化人员姓名变量
            
            with service.db_manager.get_session() as session:
                from ..models import Person
                
                # 验证人员是否存在
                person = session.query(Person).filter(Person.id == person_id).first()
                if not person:
                    raise HTTPException(status_code=404, detail="人员不存在")
                
                # 保存人员姓名，避免会话问题
                person_name = person.name
            
            success_count = 0
            error_count = 0
            results = []
            
            for i, face_file in enumerate(faces):
                try:
                    # 验证文件类型
                    if face_file.content_type and not face_file.content_type.startswith('image/'):
                        results.append({
                            'file_name': face_file.filename,
                            'success': False,
                            'error': '不支持的文件类型'
                        })
                        error_count += 1
                        continue
                    
                    # 保存临时文件
                    content = await face_file.read()
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    temp_file.write(content)
                    temp_file.close()
                    
                    try:
                        # 使用人脸识别服务处理图像并提取编码
                        # 读取图像
                        image = cv2.imread(temp_file.name)
                        if image is None:
                            results.append({
                                'file_name': face_file.filename,
                                'success': False,
                                'error': '无法读取图像文件'
                            })
                            error_count += 1
                            continue
                        
                        # 检测人脸并提取特征
                        detected_faces = service.detect_faces(image)
                        if not detected_faces:
                            results.append({
                                'file_name': face_file.filename,
                                'success': False,
                                'error': '未检测到人脸'
                            })
                            error_count += 1
                            continue
                        
                        # 使用第一个检测到的人脸
                        detected_face = detected_faces[0]
                        encoding = detected_face.get('embedding')
                        if encoding is None:
                            results.append({
                                'file_name': face_file.filename,
                                'success': False,
                                'error': '无法提取人脸特征'
                            })
                            error_count += 1
                            continue
                        
                        # 读取图像数据用于存储
                        with open(temp_file.name, 'rb') as img_file:
                            image_data = img_file.read()
                        
                        # 添加到数据库
                        face_encoding = service.db_manager.add_face_encoding(
                            person_id=person_id,
                            encoding=encoding,
                            image_path=face_file.filename,  # 存储原始文件名
                            image_data=image_data,
                            face_bbox=str(detected_face.get('bbox', [])),
                            confidence=detected_face.get('det_score', 1.0),
                            quality_score=detected_face.get('quality', 1.0)
                        )
                        
                        results.append({
                            'file_name': face_file.filename,
                            'success': True,
                            'encoding_id': face_encoding.id,
                            'quality_score': detected_face.get('quality', 0)
                        })
                        success_count += 1
                    finally:
                        # 清理临时文件
                        if os.path.exists(temp_file.name):
                            os.unlink(temp_file.name)
                
                except Exception as file_error:
                    results.append({
                        'file_name': face_file.filename,
                        'success': False,
                        'error': f"处理文件失败: {str(file_error)}"
                    })
                    error_count += 1
            
            return JSONResponse(content={
                "success": True,
                "person_id": person_id,
                "person_name": person_name,
                "total_files": len(faces),
                "success_count": success_count,
                "error_count": error_count,
                "count": success_count,  # 兼容前端
                "results": results,
                "message": f"为 {person_name} 添加人脸完成：成功 {success_count} 个，失败 {error_count} 个"
            })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"添加人员人脸失败: {str(e)}")
            raise HTTPException(status_code=500, detail="添加人员人脸失败")

    @app.post("/api/detect_faces")
    async def detect_faces(
        file: UploadFile = File(...),
        include_landmarks: bool = Query(default=False, description="是否包含关键点信息"),
        include_attributes: bool = Query(default=False, description="是否包含人脸属性(年龄、性别)"),
        min_face_size: int = Query(default=20, description="最小人脸尺寸(像素)")
    ):
        """
        🔍 纯人脸检测接口
        
        只进行人脸检测，不进行识别和入库操作
        
        Args:
            file: 上传的图片文件
            include_landmarks: 是否返回面部关键点坐标
            include_attributes: 是否分析人脸属性(年龄、性别)
            min_face_size: 检测的最小人脸尺寸
            
        Returns:
            检测到的所有人脸信息
        """
        try:
            # 验证文件类型 - 从配置文件读取
            allowed_extensions = config.get_allowed_extensions_with_dot()
            if file.filename and not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
                raise HTTPException(status_code=400, detail=f"不支持的文件格式。支持的格式: {', '.join(allowed_extensions)}")
            
            # 读取图片
            image_data = await file.read()
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise HTTPException(status_code=400, detail="无法解析图片文件")
            
            # 获取人脸检测服务
            face_service = get_advanced_face_service()
            
            # 执行人脸检测
            faces = face_service.detect_faces(image)
            
            # 过滤小于最小尺寸的人脸
            if min_face_size > 0:
                filtered_faces = []
                for face in faces:
                    bbox = face.get('bbox', [0, 0, 0, 0])
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    if width >= min_face_size and height >= min_face_size:
                        filtered_faces.append(face)
                faces = filtered_faces
            
            # 构建返回数据
            result_faces = []
            for i, face in enumerate(faces):
                face_data = {
                    "face_id": i + 1,
                    "bbox": face.get('bbox', []),
                    "confidence": face.get('det_score', 0.0),
                    "quality_score": face.get('quality', 0.0)
                }
                
                # 添加关键点信息
                if include_landmarks and 'landmarks' in face:
                    face_data["landmarks"] = face['landmarks']
                
                # 添加属性信息
                if include_attributes:
                    if 'age' in face and face['age'] is not None:
                        face_data["age"] = int(face['age'])
                    if 'gender' in face and face['gender'] is not None:
                        face_data["gender"] = "男" if face['gender'] == 1 else "女"
                
                result_faces.append(face_data)
            
            return JSONResponse(content={
                "success": True,
                "message": f"检测到 {len(result_faces)} 个人脸",
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
            logger.error(f"人脸检测失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"人脸检测失败: {str(e)}")

    @app.get("/health")
    @app.head("/health")
    async def health_check_docker():
        """Docker 健康检查接口"""
        try:
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

    @app.get("/api/health")
    @app.head("/api/health")
    async def health_check():
        """
        ❤️ 健康检查接口
        
        检查系统运行状态
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "先进人脸识别系统",
            "version": "2.0.0",
            "features": [
                "InsightFace 高精度检测",
                "DeepFace 多模型支持", 
                "人脸属性分析",
                "RESTful API"
            ]
        }

    return app

def draw_chinese_text(img, text, position, font_size=20, color=(255, 255, 255)):
    """
    在图像上绘制中文文字，使用统一的字体管理器
    """
    try:
        # 转换为PIL图像
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        # 获取字体管理器并加载字体
        font_manager = get_font_manager()
        font = font_manager.get_font(font_size)
        
        if font is None:
            # 如果字体管理器无法提供字体，使用OpenCV绘制
            cv2.putText(img, str(text), position, cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            return img
        
        # 添加文字背景以提高可读性
        try:
            bbox = draw.textbbox(position, text, font=font)
            # 绘制半透明背景
            overlay = Image.new('RGBA', img_pil.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2], 
                                 fill=(0, 0, 0, 128))  # 半透明黑色背景
            img_pil = Image.alpha_composite(img_pil.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img_pil)
        except:
            pass  # 如果背景绘制失败，继续绘制文字
        
        # 绘制文字
        draw.text(position, text, font=font, fill=color)
        
        # 转换回OpenCV格式
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
    except Exception as e:
        # 如果PIL完全失败，使用OpenCV绘制
        logger.error(f"绘制中文文字失败: {e}")
        try:
            # 尝试编码为ASCII，失败则显示英文替代
            display_text = text.encode('ascii', 'ignore').decode('ascii')
            if not display_text.strip():
                display_text = "Chinese Name"
        except:
            display_text = "Name"
        
        cv2.putText(img, display_text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        return img

# 创建应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)

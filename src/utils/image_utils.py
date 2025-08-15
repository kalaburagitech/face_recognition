"""
图像处理工具函数
"""
import cv2
import numpy as np
from PIL import Image
import os
import logging

logger = logging.getLogger(__name__)

def validate_image(image_path: str) -> bool:
    """
    验证图片文件是否有效
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        True如果图片有效，False否则
    """
    try:
        if not os.path.exists(image_path):
            return False
        
        # 检查文件扩展名 - 从配置文件读取
        from .config import config
        allowed_extensions = config.get_allowed_extensions_with_dot()
        valid_extensions = set(ext.lower() for ext in allowed_extensions)
        _, ext = os.path.splitext(image_path.lower())
        if ext not in valid_extensions:
            return False
        
        # 尝试加载图片
        with Image.open(image_path) as img:
            img.verify()  # 验证图片是否完整
        
        return True
        
    except Exception as e:
        logger.warning(f"图片验证失败 {image_path}: {str(e)}")
        return False

def preprocess_image(image_path: str, target_size: tuple = None, normalize: bool = False) -> np.ndarray:
    """
    预处理图片
    
    Args:
        image_path: 图片路径
        target_size: 目标尺寸 (width, height)
        normalize: 是否归一化像素值到0-1
        
    Returns:
        预处理后的图片数组
    """
    try:
        # 读取图片
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图片: {image_path}")
        
        # 转换BGR到RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 调整尺寸
        if target_size:
            image = cv2.resize(image, target_size)
        
        # 归一化
        if normalize:
            image = image.astype(np.float32) / 255.0
        
        return image
        
    except Exception as e:
        logger.error(f"图片预处理失败 {image_path}: {str(e)}")
        raise

def resize_image(image: np.ndarray, max_width: int = 800, max_height: int = 600) -> np.ndarray:
    """
    按比例调整图片尺寸
    
    Args:
        image: 输入图片数组
        max_width: 最大宽度
        max_height: 最大高度
        
    Returns:
        调整尺寸后的图片
    """
    height, width = image.shape[:2]
    
    # 计算缩放比例
    scale_width = max_width / width
    scale_height = max_height / height
    scale = min(scale_width, scale_height, 1.0)  # 不放大图片
    
    if scale < 1.0:
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    return image

def draw_face_boxes(image: np.ndarray, face_results: list, color: tuple = (0, 255, 0), thickness: int = 2) -> np.ndarray:
    """
    在图片上绘制人脸框和标签
    
    Args:
        image: 输入图片
        face_results: 人脸识别结果列表
        color: 框的颜色 (R, G, B)
        thickness: 线条粗细
        
    Returns:
        绘制了人脸框的图片
    """
    result_image = image.copy()
    
    for result in face_results:
        face_location = result['face_location']
        person_name = result['person_name']
        confidence = result['confidence']
        
        # face_location格式: (top, right, bottom, left)
        top, right, bottom, left = face_location
        
        # 绘制矩形框
        cv2.rectangle(result_image, (left, top), (right, bottom), color, thickness)
        
        # 绘制标签
        label = f"{person_name}"
        if confidence > 0:
            label += f" ({confidence:.2f})"
        
        # 计算文本尺寸
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        text_thickness = 1
        (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, text_thickness)
        
        # 绘制文本背景
        cv2.rectangle(result_image, (left, top - text_height - 10), 
                     (left + text_width, top), color, -1)
        
        # 绘制文本
        cv2.putText(result_image, label, (left, top - 5), 
                   font, font_scale, (255, 255, 255), text_thickness)
    
    return result_image

def save_image_with_results(image: np.ndarray, face_results: list, output_path: str) -> bool:
    """
    保存带有识别结果的图片
    
    Args:
        image: 输入图片
        face_results: 人脸识别结果
        output_path: 输出文件路径
        
    Returns:
        保存是否成功
    """
    try:
        # 绘制人脸框
        result_image = draw_face_boxes(image, face_results)
        
        # 转换RGB到BGR用于保存
        if len(result_image.shape) == 3:
            result_image = cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR)
        
        # 保存图片
        success = cv2.imwrite(output_path, result_image)
        
        if success:
            logger.info(f"结果图片已保存到: {output_path}")
        else:
            logger.error(f"保存图片失败: {output_path}")
            
        return success
        
    except Exception as e:
        logger.error(f"保存图片时出错: {str(e)}")
        return False

def create_thumbnail(image_path: str, thumbnail_path: str, size: tuple = (150, 150)) -> bool:
    """
    创建图片缩略图
    
    Args:
        image_path: 原图片路径
        thumbnail_path: 缩略图保存路径
        size: 缩略图尺寸
        
    Returns:
        创建是否成功
    """
    try:
        with Image.open(image_path) as img:
            # 转换为RGB模式
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 创建缩略图
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # 保存缩略图
            img.save(thumbnail_path, 'JPEG', quality=85)
            
        logger.info(f"缩略图已创建: {thumbnail_path}")
        return True
        
    except Exception as e:
        logger.error(f"创建缩略图失败: {str(e)}")
        return False

def get_image_info(image_path: str) -> dict:
    """
    获取图片信息
    
    Args:
        image_path: 图片路径
        
    Returns:
        图片信息字典
    """
    try:
        with Image.open(image_path) as img:
            info = {
                'width': img.width,
                'height': img.height,
                'mode': img.mode,
                'format': img.format,
                'size_bytes': os.path.getsize(image_path)
            }
            
        return info
        
    except Exception as e:
        logger.error(f"获取图片信息失败: {str(e)}")
        return {}

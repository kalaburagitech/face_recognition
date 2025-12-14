"""
Image processing tool functions
"""
import cv2
import numpy as np
from PIL import Image
import os
import logging

logger = logging.getLogger(__name__)

def validate_image(image_path: str) -> bool:
    """
    Verify that the image file is valid
    
    Args:
        image_path: Image file path
        
    Returns:
        TrueIf the image is valid，Falseotherwise
    """
    try:
        if not os.path.exists(image_path):
            return False
        
        # Check file extension - Read from configuration file
        from .config import config
        allowed_extensions = config.get_allowed_extensions_with_dot()
        valid_extensions = set(ext.lower() for ext in allowed_extensions)
        _, ext = os.path.splitext(image_path.lower())
        if ext not in valid_extensions:
            return False
        
        # Try to load image
        with Image.open(image_path) as img:
            img.verify()  # Verify that the image is complete
        
        return True
        
    except Exception as e:
        logger.warning(f"Image verification failed {image_path}: {str(e)}")
        return False

def preprocess_image(image_path: str, target_size: tuple = None, normalize: bool = False) -> np.ndarray:
    """
    Preprocess images
    
    Args:
        image_path: Image path
        target_size: target size (width, height)
        normalize: Whether to normalize pixel values ​​to0-1
        
    Returns:
        Preprocessed image array
    """
    try:
        # Read pictures
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Unable to read image: {image_path}")
        
        # ConvertBGRarriveRGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # resize
        if target_size:
            image = cv2.resize(image, target_size)
        
        # normalization
        if normalize:
            image = image.astype(np.float32) / 255.0
        
        return image
        
    except Exception as e:
        logger.error(f"Image preprocessing failed {image_path}: {str(e)}")
        raise

def resize_image(image: np.ndarray, max_width: int = 800, max_height: int = 600) -> np.ndarray:
    """
    Resize image proportionally
    
    Args:
        image: Input image array
        max_width: maximum width
        max_height: maximum height
        
    Returns:
        Resized image
    """
    height, width = image.shape[:2]
    
    # Calculate scaling
    scale_width = max_width / width
    scale_height = max_height / height
    scale = min(scale_width, scale_height, 1.0)  # Do not enlarge picture
    
    if scale < 1.0:
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    return image

def draw_face_boxes(image: np.ndarray, face_results: list, color: tuple = (0, 255, 0), thickness: int = 2) -> np.ndarray:
    """
    Draw face boxes and labels on pictures
    
    Args:
        image: Enter picture
        face_results: Face recognition result list
        color: box color (R, G, B)
        thickness: line thickness
        
    Returns:
        Picture with face frame drawn
    """
    result_image = image.copy()
    
    for result in face_results:
        face_location = result['face_location']
        person_name = result['person_name']
        confidence = result['confidence']
        
        # face_locationFormat: (top, right, bottom, left)
        top, right, bottom, left = face_location
        
        # Draw a rectangular box
        cv2.rectangle(result_image, (left, top), (right, bottom), color, thickness)
        
        # draw labels
        label = f"{person_name}"
        if confidence > 0:
            label += f" ({confidence:.2f})"
        
        # Calculate text size
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        text_thickness = 1
        (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, text_thickness)
        
        # Draw text background
        cv2.rectangle(result_image, (left, top - text_height - 10), 
                     (left + text_width, top), color, -1)
        
        # draw text
        cv2.putText(result_image, label, (left, top - 5), 
                   font, font_scale, (255, 255, 255), text_thickness)
    
    return result_image

def save_image_with_results(image: np.ndarray, face_results: list, output_path: str) -> bool:
    """
    Save image with recognition results
    
    Args:
        image: Enter picture
        face_results: Face recognition results
        output_path: Output file path
        
    Returns:
        Is the save successful?
    """
    try:
        # Draw face frame
        result_image = draw_face_boxes(image, face_results)
        
        # ConvertRGBarriveBGRfor saving
        if len(result_image.shape) == 3:
            result_image = cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR)
        
        # save image
        success = cv2.imwrite(output_path, result_image)
        
        if success:
            logger.info(f"The resulting image has been saved to: {output_path}")
        else:
            logger.error(f"Failed to save picture: {output_path}")
            
        return success
        
    except Exception as e:
        logger.error(f"Error saving image: {str(e)}")
        return False

def create_thumbnail(image_path: str, thumbnail_path: str, size: tuple = (150, 150)) -> bool:
    """
    Create image thumbnails
    
    Args:
        image_path: Original image path
        thumbnail_path: Thumbnail save path
        size: Thumbnail size
        
    Returns:
        Is the creation successful?
    """
    try:
        with Image.open(image_path) as img:
            # Convert toRGBmodel
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(thumbnail_path, 'JPEG', quality=85)
            
        logger.info(f"Thumbnail created: {thumbnail_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create thumbnail: {str(e)}")
        return False

def get_image_info(image_path: str) -> dict:
    """
    Get picture information
    
    Args:
        image_path: Image path
        
    Returns:
        Picture information dictionary
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
        logger.error(f"Failed to obtain image information: {str(e)}")
        return {}

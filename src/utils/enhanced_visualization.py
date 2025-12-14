"""
Enhanced face recognition visualization tool
Provides better text rendering、Color differentiation and layout optimization
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from typing import List, Dict, Tuple, Any, Optional
import colorsys
import math
from .font_manager import get_font_manager

class EnhancedFaceVisualizer:
    """Enhanced face visualizer"""
    
    def __init__(self):
        self.colors = self._generate_distinct_colors(20)  # pregenerated20different colors
        self.font_cache = {}  # Font cache，Improve performance
        self.font_manager = get_font_manager()  # Use a unified font manager
    
    def _generate_distinct_colors(self, num_colors: int) -> List[Tuple[int, int, int]]:
        """Generate visually distinctive colors"""
        colors = []
        for i in range(num_colors):
            # useHSVColor space generates evenly distributed colors
            hue = i / num_colors
            saturation = 0.8 + (i % 3) * 0.1  # 0.8-1.0change between
            value = 0.8 + (i % 2) * 0.2       # 0.8-1.0change between
            
            # Convert toRGB
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            # Convert toBGRFormat(OpenCVuseBGR)
            bgr = (int(rgb[2] * 255), int(rgb[1] * 255), int(rgb[0] * 255))
            colors.append(bgr)
        
        return colors
    
    def _load_font(self, size: int = 20) -> Optional[Any]:
        """Load appropriate fonts，Use a font manager"""
        return self.font_manager.get_font(size)
    
    def _get_text_size(self, text: str, font_size: int = 20) -> Tuple[int, int]:
        """Get text size，Use a font manager"""
        return self.font_manager.get_text_size(text, font_size)
    
    def _calculate_adaptive_font_size(self, bbox: List[int], text: str, 
                                     min_size: int = 12, max_size: int = 24) -> int:
        """Adaptively calculate font size based on bounding box size"""
        if len(bbox) != 4:
            return 16  # default size
        
        x1, y1, x2, y2 = bbox
        box_width = x2 - x1
        box_height = y2 - y1
        
        # Calculate font size based on bounding box size
        # Use the smaller side of the bounding box as a reference
        min_dimension = min(box_width, box_height)
        
        # Font size is approximately the smallest side of the bounding box1/8arrive1/6
        font_size = max(min_size, min(max_size, min_dimension // 6))
        
        # Consider text length，Use a smaller font for long text
        if len(text) > 8:
            font_size = max(min_size, int(font_size * 0.8))
        elif len(text) > 12:
            font_size = max(min_size, int(font_size * 0.7))
        
        return int(font_size)

    def _find_best_text_position(self, bbox: List[int], text_size: Tuple[int, int], 
                                image_shape: Tuple[int, int]) -> Tuple[int, int]:
        """Intelligent calculation of optimal text position，Avoid overflowing image boundaries"""
        x1, y1, x2, y2 = bbox
        text_width, text_height = text_size
        img_height, img_width = image_shape[:2]
        
        # Candidate location（Priority from high to low）
        positions = [
            (x1, y1 - text_height - 10),  # above
            (x1, y2 + 5),                 # below
            (x2 + 5, y1),                 # right side
            (max(0, x1 - text_width - 5), y1),  # left side
            (x1, y1 + 5),                 # Above the box
            (x1, y2 - text_height - 5),   # below the box
        ]
        
        # Check if each position is within the image bounds
        for pos_x, pos_y in positions:
            if (0 <= pos_x <= img_width - text_width and 
                0 <= pos_y <= img_height - text_height):
                return pos_x, pos_y
        
        # If none of them are suitable，Use a safe location
        safe_x = max(0, min(x1, img_width - text_width))
        safe_y = max(0, min(y1, img_height - text_height))
        return safe_x, safe_y
    
    def _draw_text_with_background(self, image: np.ndarray, text: str, 
                                  position: Tuple[int, int], color: Tuple[int, int, int],
                                  font_size: int = 20, alpha: float = 0.8) -> np.ndarray:
        """Draw high-quality text with background，Support Chinese，Enhance contrast"""
        # Convert toPILImage for text rendering
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        # Use fonts that support Chinese
        font = self._load_font(font_size)
        if not font:
            font = ImageFont.load_default()
        
        x, y = position
        
        # Get text bounds
        try:
            bbox = draw.textbbox((x, y), text, font=font)
        except Exception as e:
            print(f"Error getting text bbox: {e}")
            # Use estimates
            text_width, text_height = self._get_text_size(text, font_size)
            bbox = [x, y, x + text_width, y + text_height]
        
        # Enhance background effect：double background
        margin = 6
        bg_bbox = [
            bbox[0] - margin, bbox[1] - margin,
            bbox[2] + margin, bbox[3] + margin
        ]
        
        # Create multi-layered background effects
        overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # outer dark background（Enhance contrast）
        outer_bg_color = (0, 0, 0, int(255 * 0.8))
        overlay_draw.rectangle(bg_bbox, fill=outer_bg_color)
        
        # Inner color background
        inner_margin = 2
        inner_bg_bbox = [
            bbox[0] - inner_margin, bbox[1] - inner_margin,
            bbox[2] + inner_margin, bbox[3] + inner_margin
        ]
        background_color = (*color, int(255 * alpha * 0.7))
        overlay_draw.rectangle(inner_bg_bbox, fill=background_color)
        
        # Merge background
        pil_image = Image.alpha_composite(pil_image.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(pil_image)
        
        # Draw text outline（Enhance contrast）
        outline_color = (0, 0, 0)  # black outline
        try:
            # Draw outline（Draw black text around main text）
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
            
            # Draw main text（White）
            draw.text((x, y), text, font=font, fill=(255, 255, 255))
        except Exception as e:
            print(f"Error drawing text: {e}")
            # Fall back to system default font
            draw.text((x, y), text, fill=(255, 255, 255))
        
        # transfer backOpenCVFormat
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    def visualize_face_detection(self, image: np.ndarray, faces: List[Dict]) -> Dict[str, Any]:
        """
        Visualizing face detection results
        
        Args:
            image: original image
            faces: Face detection result list
            
        Returns:
            Visual results dictionary
        """
        if image is None:
            return {'success': False, 'error': 'Invalid image'}
        
        result_image = image.copy()
        face_details = []
        
        # Assign color mapping and intelligence to different peopleID
        person_color_map = {}
        person_face_count = {}  # Record the number of faces of each person
        unknown_count = 0  # Unknown people counter
        
        for i, face_info in enumerate(faces):
            bbox = face_info.get('bbox', [])
            if len(bbox) != 4:
                continue
                
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            
            # Get person name，for color assignment
            name = face_info.get('name', f'human face{i+1}')
            person_id = face_info.get('person_id', -1)
            
            # intelligentIDdistribution system
            if person_id != -1:
                # known persons，useperson_idas colorkey
                color_key = f"person_{person_id}"
                
                # Calculate the face serial number of the person
                if person_id not in person_face_count:
                    person_face_count[person_id] = 0
                person_face_count[person_id] += 1
                
                # Generate displayID
                if person_face_count[person_id] > 1:
                    # Multiple faces of the same person，Distinguish with letter suffix
                    suffix = chr(ord('A') + person_face_count[person_id] - 1)
                    id_label = f"P{person_id}{suffix}"
                else:
                    id_label = f"P{person_id}"
            else:
                # unknown person，Assigned in order of detectionID
                unknown_count += 1
                id_label = f"U{unknown_count}"
                color_key = f"unknown_{unknown_count}"
            
            if color_key not in person_color_map:
                # Assign new color
                color_index = len(person_color_map) % len(self.colors)
                person_color_map[color_key] = self.colors[color_index]
            
            color = person_color_map[color_key]
            
            # draw border（Turn off corner reinforcement lines）
            self._draw_gradient_box(result_image, (x1, y1, x2, y2), color, 3, show_corners=False)
            
            # Add intelligenceIDlogo
            self._draw_id_badge(result_image, [x1, y1, x2, y2], id_label, color)
            
            # Prepare label text
            quality = face_info.get('quality', face_info.get('det_score', 0))
            confidence = face_info.get('confidence', 0)
            
            # multiline text label
            labels = [
                f"{id_label}: {name}",
                f"quality: {quality:.2f}",
            ]
            
            if confidence > 0:
                labels.append(f"Confidence: {confidence:.2f}")
            
            # Adaptive font size
            adaptive_font_size = self._calculate_adaptive_font_size([x1, y1, x2, y2], name)
            detail_font_size = max(10, adaptive_font_size - 4)
            
            # Calculate total text size
            max_width = 0
            total_height = 0
            line_heights = []
            
            for j, label in enumerate(labels):
                current_font_size = adaptive_font_size if j == 0 else detail_font_size
                w, h = self._get_text_size(label, current_font_size)
                max_width = max(max_width, w)
                line_heights.append(h)
                total_height += h + 2  # line spacing
            
            # Find the best text placement
            text_pos = self._find_best_text_position(
                [x1, y1, x2, y2], 
                (max_width, total_height), 
                result_image.shape
            )
            
            # Draw multiple lines of text
            current_y = text_pos[1]
            for j, label in enumerate(labels):
                current_font_size = adaptive_font_size if j == 0 else detail_font_size
                result_image = self._draw_text_with_background(
                    result_image, label, (text_pos[0], current_y), 
                    color, current_font_size, 0.7
                )
                current_y += line_heights[j] + 2
            
            # Collect details
            face_details.append({
                'id': id_label,  # Use formattedIDLabel
                'person_id': person_id,  # original personnelID
                'index': i + 1,
                'bbox': [x1, y1, x2, y2],
                'quality': float(quality),
                'confidence': float(confidence) if confidence > 0 else None,
                'name': name,
                'color': color,
                'color_key': color_key,
                'size': [x2 - x1, y2 - y1]
            })
        
        # encoded image
        try:
            _, buffer = cv2.imencode('.jpg', result_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                'success': True,
                'image_base64': image_base64,
                'total_faces': len(faces),
                'face_details': face_details,
                'person_color_map': person_color_map,
                'image_size': result_image.shape[:2]
            }
        except Exception as e:
            return {
                'success': False, 
                'error': f'Image encoding failed: {str(e)}'
            }
    
    def _draw_gradient_box(self, image: np.ndarray, bbox: Tuple[int, int, int, int], 
                          color: Tuple[int, int, int], thickness: int = 3, 
                          show_corners: bool = False):
        """Draw gradient border，Add shadow effect"""
        x1, y1, x2, y2 = bbox
        
        # Add shadow effect（Draw a semi-transparent black border on the lower right）
        shadow_offset = 2
        shadow_color = (0, 0, 0)
        shadow_alpha = 0.3
        
        # Create shadow layer
        shadow_overlay = image.copy()
        cv2.rectangle(shadow_overlay, 
                     (x1 + shadow_offset, y1 + shadow_offset), 
                     (x2 + shadow_offset, y2 + shadow_offset), 
                     shadow_color, thickness)
        
        # blend shadows
        cv2.addWeighted(image, 1 - shadow_alpha, shadow_overlay, shadow_alpha, 0, image)
        
        # main border
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
        
        # inner border（slightly lighter color）
        inner_color = tuple(min(255, c + 30) for c in color)
        cv2.rectangle(image, (x1+1, y1+1), (x2-1, y2-1), inner_color, 1)
        
        # Optional corner reinforcements（Off by default，avoid distractions）
        if show_corners:
            corner_size = 8  # reduce size
            corner_thickness = max(1, thickness - 1)  # reduce thickness
            corners = [
                ((x1, y1), (x1 + corner_size, y1), (x1, y1 + corner_size)),  # upper left
                ((x2, y1), (x2 - corner_size, y1), (x2, y1 + corner_size)),  # upper right
                ((x1, y2), (x1 + corner_size, y2), (x1, y2 - corner_size)),  # lower left
                ((x2, y2), (x2 - corner_size, y2), (x2, y2 - corner_size)),  # lower right
            ]
            
            for corner in corners:
                cv2.line(image, corner[0], corner[1], color, corner_thickness)
                cv2.line(image, corner[0], corner[2], color, corner_thickness)
    
    def _detect_overlapping_boxes(self, boxes: List[List[int]]) -> List[List[int]]:
        """Detect overlapping bounding boxes，Return to the position after avoidance adjustment"""
        if len(boxes) <= 1:
            return boxes
        
        adjusted_boxes = []
        for i, box in enumerate(boxes):
            adjusted_box = box.copy()
            
            # Check if it overlaps with the previous box
            for j in range(i):
                if self._boxes_overlap(adjusted_box, adjusted_boxes[j]):
                    # Offset to lower right
                    offset = 10 * (j + 1)
                    adjusted_box[0] += offset
                    adjusted_box[1] += offset
                    adjusted_box[2] += offset
                    adjusted_box[3] += offset
            
            adjusted_boxes.append(adjusted_box)
        
        return adjusted_boxes
    
    def _boxes_overlap(self, box1: List[int], box2: List[int]) -> bool:
        """Determine whether two bounding boxes overlap"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Check if there is overlap
        return not (x2_1 < x1_2 or x2_2 < x1_1 or y2_1 < y1_2 or y2_2 < y1_1)

    def _draw_corner_badge(self, image: np.ndarray, position: Tuple[int, int], 
                          text: str, color: Tuple[int, int, int], style: str = "circle"):
        """draw corner mark，Support different styles，Enhance visibility"""
        x, y = position
        
        if style == "circle":
            # Round corner mark
            radius = 16
            # Draw shadow effect
            cv2.circle(image, (x+2, y+2), radius, (0, 0, 0), -1)
            # Draw a circle background
            cv2.circle(image, (x, y), radius, color, -1)
            cv2.circle(image, (x, y), radius, (255, 255, 255), 2)
            
            # Draw text
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            text_size = cv2.getTextSize(text, font, font_scale, 2)[0]
            text_x = x - text_size[0] // 2
            text_y = y + text_size[1] // 2
            
            cv2.putText(image, text, (text_x, text_y), font, font_scale, (255, 255, 255), 2)
            
        elif style == "square":
            # square corner mark - Enhanced version
            size = 26  # slightly larger for better visibility
            half_size = size // 2
            
            # Draw shadow effect
            cv2.rectangle(image, (x - half_size + 2, y - half_size + 2), 
                         (x + half_size + 2, y + half_size + 2), (0, 0, 0), -1)
            
            # Draw a square background（filling）
            cv2.rectangle(image, (x - half_size, y - half_size), 
                         (x + half_size, y + half_size), color, -1)
            
            # Draw white border
            cv2.rectangle(image, (x - half_size, y - half_size), 
                         (x + half_size, y + half_size), (255, 255, 255), 2)
            
            # Draw text（White，with black outline）
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 2
            
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = x - text_size[0] // 2
            text_y = y + text_size[1] // 2
            
            # black outline
            cv2.putText(image, text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness + 1)
            # white text
            cv2.putText(image, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)
    
    def _draw_id_badge(self, image: np.ndarray, bbox: List[int], face_id, 
                      color: Tuple[int, int, int]):
        """Draw a clear one in the upper left corner of the bounding boxIDlogo，Smart position adjustment"""
        x1, y1, x2, y2 = bbox
        img_height, img_width = image.shape[:2]
        
        # calculateIDIdeal and actual available locations for labels
        badge_size = 24  # Square corner mark size
        margin = 5
        
        # Priority location selection（Sort by priority）
        positions = [
            # 1. Outside upper left corner（default）
            (x1 - badge_size//2 - margin, y1 - badge_size//2 - margin),
            # 2. Outside upper right corner  
            (x2 + margin + badge_size//2, y1 - badge_size//2 - margin),
            # 3. Outside lower left corner
            (x1 - badge_size//2 - margin, y2 + margin + badge_size//2),
            # 4. Outside lower right corner
            (x2 + margin + badge_size//2, y2 + margin + badge_size//2),
            # 5. Inside upper left corner
            (x1 + badge_size//2 + margin, y1 + badge_size//2 + margin),
            # 6. Inside upper right corner
            (x2 - badge_size//2 - margin, y1 + badge_size//2 + margin),
            # 7. above center
            ((x1 + x2) // 2, y1 - badge_size//2 - margin),
            # 8. below center
            ((x1 + x2) // 2, y2 + badge_size//2 + margin)
        ]
        
        # Select the first position within the image bounds
        final_position = None
        for pos_x, pos_y in positions:
            if (badge_size//2 <= pos_x <= img_width - badge_size//2 and
                badge_size//2 <= pos_y <= img_height - badge_size//2):
                final_position = (pos_x, pos_y)
                break
        
        # If none of them are suitable，Use safe boundary locations
        if final_position is None:
            safe_x = max(badge_size//2, min(x1, img_width - badge_size//2))
            safe_y = max(badge_size//2, min(y1, img_height - badge_size//2))
            final_position = (safe_x, safe_y)
        
        # drawIDLabel
        self._draw_corner_badge(image, final_position, str(face_id), 
                               color, style="square")
    
    def visualize_recognition_results(self, image: np.ndarray, matches: List[Dict], 
                                    threshold: float = 0.25) -> Dict[str, Any]:
        """
        Visualizing face recognition results
        
        Args:
            image: original image
            matches: List of matching results
            threshold: recognition threshold
            
        Returns:
            Visual results dictionary
        """
        if image is None:
            return {'success': False, 'error': 'Invalid image'}
        
        result_image = image.copy()
        match_details = []  # Add details to collect
        
        # Assign color mapping and intelligence to different peopleID
        person_color_map = {}
        person_face_count = {}  # Record the number of faces of each person
        unknown_count = 0  # Unknown people counter
        
        for i, match in enumerate(matches):
            bbox = match.get('bbox', [])
            if len(bbox) != 4:
                continue
                
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            
            # Determine color and style based on match
            match_score = match.get('match_score', 0)
            person_id = match.get('person_id', -1)
            name = match.get('name', 'unknown')
            is_known = person_id != -1
            
            # intelligentIDdistribution system
            if person_id != -1:
                # known persons，useperson_idas colorkey
                color_key = f"person_{person_id}"
                
                # Calculate the face serial number of the person
                if person_id not in person_face_count:
                    person_face_count[person_id] = 0
                person_face_count[person_id] += 1
                
                # Generate displayID
                if person_face_count[person_id] > 1:
                    # Multiple faces of the same person，Distinguish with letter suffix
                    suffix = chr(ord('A') + person_face_count[person_id] - 1)
                    id_label = f"P{person_id}{suffix}"
                else:
                    id_label = f"P{person_id}"
            else:
                # unknown person，Assigned in order of detectionID
                unknown_count += 1
                id_label = f"U{unknown_count}"
                color_key = f"unknown_{unknown_count}"
            
            if color_key not in person_color_map:
                # Assign new color
                color_index = len(person_color_map) % len(self.colors)
                person_color_map[color_key] = self.colors[color_index]
            
            base_color = person_color_map[color_key]
            
            # Determine styles based on confidence
            if is_known and match_score >= threshold * 100:
                # known persons，high confidence
                confidence_level = "high"
                # Maintain original color brightness
                color_intensity = 1.0
            elif is_known and match_score >= threshold * 50:
                # known persons，medium confidence
                confidence_level = "medium"
                color_intensity = 0.8
            elif is_known:
                # known persons，low confidence
                confidence_level = "low"
                color_intensity = 0.6
            else:
                # unknown person
                confidence_level = "unknown"
                color_intensity = 0.5
                # Unknown person uses red color
                base_color = (0, 0, 200)
            
            # Adjust color brightness
            color = (
                int(base_color[0] * color_intensity),
                int(base_color[1] * color_intensity),
                int(base_color[2] * color_intensity)
            )
            
            # Draw different styles of borders
            if confidence_level == "high":
                self._draw_gradient_box(result_image, (x1, y1, x2, y2), color, 4, show_corners=False)
            elif confidence_level == "medium":
                cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 3)
                # Add dotted line effect
                self._draw_dashed_rectangle(result_image, (x1, y1, x2, y2), color, 2)
            elif confidence_level == "low":
                cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
            else:
                # Unknown person with dotted box
                self._draw_dashed_rectangle(result_image, (x1, y1, x2, y2), color, 3)
            
            # Add intelligenceIDlogo
            self._draw_id_badge(result_image, [x1, y1, x2, y2], id_label, color)
            
            # Prepare labels
            distance = match.get('distance', 0)
            quality = match.get('quality', 0)
            
            labels = [
                f"{id_label}: {name}",
                f"match: {match_score:.1f}%",
                f"distance: {distance:.3f}",
            ]
            
            if quality > 0:
                labels.append(f"quality: {quality:.2f}")
            
            # Adaptive font size
            adaptive_font_size = self._calculate_adaptive_font_size([x1, y1, x2, y2], name)
            detail_font_size = max(10, adaptive_font_size - 4)
            
            # Count and draw text
            max_width = 0
            total_height = 0
            line_heights = []
            
            for j, label in enumerate(labels):
                current_font_size = adaptive_font_size if j == 0 else detail_font_size
                w, h = self._get_text_size(label, current_font_size)
                max_width = max(max_width, w)
                line_heights.append(h)
                total_height += h + 2
            
            text_pos = self._find_best_text_position(
                [x1, y1, x2, y2], (max_width, total_height), result_image.shape
            )
            
            current_y = text_pos[1]
            for j, label in enumerate(labels):
                current_font_size = adaptive_font_size if j == 0 else detail_font_size
                alpha = 0.8 if confidence_level == "high" else 0.7
                result_image = self._draw_text_with_background(
                    result_image, label, (text_pos[0], current_y), 
                    color, current_font_size, alpha
                )
                current_y += line_heights[j] + 2
            
            # Add confidence indicator
            self._draw_confidence_indicator(result_image, (x2-30, y1+10), 
                                          match_score, confidence_level, color)
            
            # Collect details
            match_details.append({
                'id': id_label,  # Use formattedIDLabel
                'person_id': person_id,  # original personnelID
                'index': i + 1,
                'bbox': [x1, y1, x2, y2],
                'name': name,
                'match_score': float(match_score),
                'distance': float(distance),
                'quality': float(quality),
                'confidence_level': confidence_level,
                'color': color,
                'color_key': color_key,
                'size': [x2 - x1, y2 - y1]
            })
        
        # Encoding return
        try:
            _, buffer = cv2.imencode('.jpg', result_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                'success': True,
                'image_base64': image_base64,
                'total_matches': len(matches),
                'match_details': match_details,  # Use updated details
                'person_color_map': person_color_map
            }
        except Exception as e:
            return {'success': False, 'error': f'Image encoding failed: {str(e)}'}
    
    def _draw_dashed_rectangle(self, image: np.ndarray, bbox: Tuple[int, int, int, int], 
                              color: Tuple[int, int, int], thickness: int = 2):
        """Draw a dashed rectangle"""
        x1, y1, x2, y2 = bbox
        dash_length = 10
        
        # above
        for x in range(x1, x2, dash_length * 2):
            cv2.line(image, (x, y1), (min(x + dash_length, x2), y1), color, thickness)
        
        # below
        for x in range(x1, x2, dash_length * 2):
            cv2.line(image, (x, y2), (min(x + dash_length, x2), y2), color, thickness)
        
        # left
        for y in range(y1, y2, dash_length * 2):
            cv2.line(image, (x1, y), (x1, min(y + dash_length, y2)), color, thickness)
        
        # right
        for y in range(y1, y2, dash_length * 2):
            cv2.line(image, (x2, y), (x2, min(y + dash_length, y2)), color, thickness)
    
    def _draw_confidence_indicator(self, image: np.ndarray, position: Tuple[int, int], 
                                  score: float, level: str, color: Tuple[int, int, int]):
        """Draw confidence indicator"""
        x, y = position
        bar_width = 20
        bar_height = 4
        
        # background strip
        cv2.rectangle(image, (x, y), (x + bar_width, y + bar_height), (128, 128, 128), -1)
        
        # confidence bar
        confidence_width = int(bar_width * min(score / 100, 1.0))
        cv2.rectangle(image, (x, y), (x + confidence_width, y + bar_height), color, -1)
        
        # frame
        cv2.rectangle(image, (x, y), (x + bar_width, y + bar_height), (255, 255, 255), 1)

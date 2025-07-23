"""
增强的人脸识别可视化工具
提供更好的文字渲染、颜色区分和布局优化
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from typing import List, Dict, Tuple, Any, Optional
import colorsys
import math

class EnhancedFaceVisualizer:
    """增强的人脸可视化器"""
    
    def __init__(self):
        self.colors = self._generate_distinct_colors(20)  # 预生成20种不同颜色
        self.font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/PingFang.ttc",
            "/Windows/Fonts/simhei.ttf",
            None  # 系统默认字体
        ]
        self.font = self._load_font()
    
    def _generate_distinct_colors(self, num_colors: int) -> List[Tuple[int, int, int]]:
        """生成视觉上区分度高的颜色"""
        colors = []
        for i in range(num_colors):
            # 使用HSV色彩空间生成均匀分布的颜色
            hue = i / num_colors
            saturation = 0.8 + (i % 3) * 0.1  # 0.8-1.0之间变化
            value = 0.8 + (i % 2) * 0.2       # 0.8-1.0之间变化
            
            # 转换为RGB
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            # 转换为BGR格式(OpenCV使用BGR)
            bgr = (int(rgb[2] * 255), int(rgb[1] * 255), int(rgb[0] * 255))
            colors.append(bgr)
        
        return colors
    
    def _load_font(self) -> Optional[Any]:
        """加载合适的字体"""
        for font_path in self.font_paths:
            try:
                if font_path:
                    return ImageFont.truetype(font_path, 20)
                else:
                    return ImageFont.load_default()
            except:
                continue
        return None
    
    def _get_text_size(self, text: str, font_size: int = 20) -> Tuple[int, int]:
        """获取文字尺寸"""
        if self.font:
            try:
                font = ImageFont.truetype(self.font.path, font_size)
                bbox = font.getbbox(text)
                return int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])
            except:
                pass
        
        # 回退到估算
        return int(len(text) * font_size * 0.6), int(font_size * 1.2)
    
    def _find_best_text_position(self, bbox: List[int], text_size: Tuple[int, int], 
                                image_shape: Tuple[int, int]) -> Tuple[int, int]:
        """智能计算文字最佳位置，避免溢出图片边界"""
        x1, y1, x2, y2 = bbox
        text_width, text_height = text_size
        img_height, img_width = image_shape[:2]
        
        # 候选位置（优先级从高到低）
        positions = [
            (x1, y1 - text_height - 10),  # 上方
            (x1, y2 + 5),                 # 下方
            (x2 + 5, y1),                 # 右侧
            (max(0, x1 - text_width - 5), y1),  # 左侧
            (x1, y1 + 5),                 # 框内上方
            (x1, y2 - text_height - 5),   # 框内下方
        ]
        
        # 检查每个位置是否在图片边界内
        for pos_x, pos_y in positions:
            if (0 <= pos_x <= img_width - text_width and 
                0 <= pos_y <= img_height - text_height):
                return pos_x, pos_y
        
        # 如果都不合适，使用安全位置
        safe_x = max(0, min(x1, img_width - text_width))
        safe_y = max(0, min(y1, img_height - text_height))
        return safe_x, safe_y
    
    def _draw_text_with_background(self, image: np.ndarray, text: str, 
                                  position: Tuple[int, int], color: Tuple[int, int, int],
                                  font_size: int = 20, alpha: float = 0.8) -> np.ndarray:
        """绘制带背景的高质量文字"""
        # 转换为PIL图像进行文字渲染
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        try:
            if self.font:
                font = ImageFont.truetype(self.font.path, font_size)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        x, y = position
        
        # 获取文字边界
        bbox = draw.textbbox((x, y), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 绘制半透明背景
        background_color = (*color, int(255 * alpha))
        margin = 4
        bg_bbox = [
            bbox[0] - margin, bbox[1] - margin,
            bbox[2] + margin, bbox[3] + margin
        ]
        
        # 创建半透明背景
        overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(bg_bbox, fill=background_color)
        
        # 合并背景
        pil_image = Image.alpha_composite(pil_image.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(pil_image)
        
        # 绘制文字（白色，确保对比度）
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
        
        # 转回OpenCV格式
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    def visualize_face_detection(self, image: np.ndarray, faces: List[Dict]) -> Dict[str, Any]:
        """
        可视化人脸检测结果
        
        Args:
            image: 原始图像
            faces: 人脸检测结果列表
            
        Returns:
            可视化结果字典
        """
        if image is None:
            return {'success': False, 'error': '图像无效'}
        
        result_image = image.copy()
        face_details = []
        
        for i, face_info in enumerate(faces):
            bbox = face_info.get('bbox', [])
            if len(bbox) != 4:
                continue
                
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            
            # 获取颜色（循环使用预生成的颜色）
            color = self.colors[i % len(self.colors)]
            
            # 绘制边框（渐变效果）
            self._draw_gradient_box(result_image, (x1, y1, x2, y2), color, 3)
            
            # 准备标签文字
            quality = face_info.get('quality', face_info.get('det_score', 0))
            confidence = face_info.get('confidence', 0)
            name = face_info.get('name', f'人脸 {i+1}')
            
            # 多行文字标签
            labels = [
                f"{name}",
                f"质量: {quality:.2f}",
            ]
            
            if confidence > 0:
                labels.append(f"置信: {confidence:.2f}")
            
            # 计算文字总尺寸
            max_width = 0
            total_height = 0
            line_heights = []
            
            for label in labels:
                w, h = self._get_text_size(label, 16)
                max_width = max(max_width, w)
                line_heights.append(h)
                total_height += h + 2  # 行间距
            
            # 找到最佳文字位置
            text_pos = self._find_best_text_position(
                [x1, y1, x2, y2], 
                (max_width, total_height), 
                result_image.shape
            )
            
            # 绘制多行文字
            current_y = text_pos[1]
            for j, label in enumerate(labels):
                font_size = 18 if j == 0 else 14  # 第一行用大字体
                result_image = self._draw_text_with_background(
                    result_image, label, (text_pos[0], current_y), 
                    color, font_size, 0.7
                )
                current_y += line_heights[j] + 2
            
            # 添加角标（显示序号）
            self._draw_corner_badge(result_image, (x2-25, y1), str(i+1), color)
            
            # 收集详情
            face_details.append({
                'index': i + 1,
                'bbox': [x1, y1, x2, y2],
                'quality': float(quality),
                'confidence': float(confidence) if confidence > 0 else None,
                'name': name,
                'color': color,
                'size': [x2 - x1, y2 - y1]
            })
        
        # 编码图像
        try:
            _, buffer = cv2.imencode('.jpg', result_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                'success': True,
                'image_base64': image_base64,
                'total_faces': len(faces),
                'face_details': face_details,
                'image_size': result_image.shape[:2]
            }
        except Exception as e:
            return {
                'success': False, 
                'error': f'图像编码失败: {str(e)}'
            }
    
    def _draw_gradient_box(self, image: np.ndarray, bbox: Tuple[int, int, int, int], 
                          color: Tuple[int, int, int], thickness: int = 3):
        """绘制渐变边框"""
        x1, y1, x2, y2 = bbox
        
        # 主边框
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
        
        # 内边框（稍浅的颜色）
        inner_color = tuple(min(255, c + 30) for c in color)
        cv2.rectangle(image, (x1+1, y1+1), (x2-1, y2-1), inner_color, 1)
        
        # 角部加强
        corner_size = 15
        corner_thickness = thickness + 1
        corners = [
            ((x1, y1), (x1 + corner_size, y1), (x1, y1 + corner_size)),  # 左上
            ((x2, y1), (x2 - corner_size, y1), (x2, y1 + corner_size)),  # 右上
            ((x1, y2), (x1 + corner_size, y2), (x1, y2 - corner_size)),  # 左下
            ((x2, y2), (x2 - corner_size, y2), (x2, y2 - corner_size)),  # 右下
        ]
        
        for corner in corners:
            cv2.line(image, corner[0], corner[1], color, corner_thickness)
            cv2.line(image, corner[0], corner[2], color, corner_thickness)
    
    def _draw_corner_badge(self, image: np.ndarray, position: Tuple[int, int], 
                          text: str, color: Tuple[int, int, int]):
        """绘制角标"""
        x, y = position
        radius = 12
        
        # 绘制圆形背景
        cv2.circle(image, (x, y), radius, color, -1)
        cv2.circle(image, (x, y), radius, (255, 255, 255), 2)
        
        # 绘制文字
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        text_size = cv2.getTextSize(text, font, font_scale, 1)[0]
        text_x = x - text_size[0] // 2
        text_y = y + text_size[1] // 2
        
        cv2.putText(image, text, (text_x, text_y), font, font_scale, (255, 255, 255), 1)
    
    def visualize_recognition_results(self, image: np.ndarray, matches: List[Dict], 
                                    threshold: float = 0.6) -> Dict[str, Any]:
        """
        可视化人脸识别结果
        
        Args:
            image: 原始图像
            matches: 匹配结果列表
            threshold: 识别阈值
            
        Returns:
            可视化结果字典
        """
        if image is None:
            return {'success': False, 'error': '图像无效'}
        
        result_image = image.copy()
        
        for i, match in enumerate(matches):
            bbox = match.get('bbox', [])
            if len(bbox) != 4:
                continue
                
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            
            # 根据匹配度确定颜色和样式
            match_score = match.get('match_score', 0)
            is_known = match.get('person_id', -1) != -1
            
            if is_known and match_score >= threshold * 100:
                # 已知人员，高置信度 - 绿色系
                base_color = (0, 200, 0)
                confidence_level = "high"
            elif is_known and match_score >= threshold * 50:
                # 已知人员，中等置信度 - 黄色系
                base_color = (0, 165, 255)
                confidence_level = "medium"
            elif is_known:
                # 已知人员，低置信度 - 橙色系
                base_color = (0, 100, 255)
                confidence_level = "low"
            else:
                # 未知人员 - 红色系
                base_color = (0, 0, 200)
                confidence_level = "unknown"
            
            # 调整颜色亮度
            color_intensity = min(1.0, match_score / 100)
            color = (
                int(base_color[0] * (0.5 + 0.5 * color_intensity)),
                int(base_color[1] * (0.5 + 0.5 * color_intensity)),
                int(base_color[2] * (0.5 + 0.5 * color_intensity))
            )
            
            # 绘制不同样式的边框
            if confidence_level == "high":
                self._draw_gradient_box(result_image, (x1, y1, x2, y2), color, 4)
            elif confidence_level == "medium":
                cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 3)
                # 添加虚线效果
                self._draw_dashed_rectangle(result_image, (x1, y1, x2, y2), color, 2)
            elif confidence_level == "low":
                cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
            else:
                # 未知人员用虚线框
                self._draw_dashed_rectangle(result_image, (x1, y1, x2, y2), color, 3)
            
            # 准备标签
            name = match.get('name', '未知')
            distance = match.get('distance', 0)
            quality = match.get('quality', 0)
            
            labels = [
                f"{name}",
                f"匹配: {match_score:.1f}%",
                f"距离: {distance:.3f}",
            ]
            
            if quality > 0:
                labels.append(f"质量: {quality:.2f}")
            
            # 计算并绘制文字
            max_width = 0
            total_height = 0
            line_heights = []
            
            for label in labels:
                w, h = self._get_text_size(label, 16)
                max_width = max(max_width, w)
                line_heights.append(h)
                total_height += h + 2
            
            text_pos = self._find_best_text_position(
                [x1, y1, x2, y2], (max_width, total_height), result_image.shape
            )
            
            current_y = text_pos[1]
            for j, label in enumerate(labels):
                font_size = 18 if j == 0 else 14
                alpha = 0.8 if confidence_level == "high" else 0.7
                result_image = self._draw_text_with_background(
                    result_image, label, (text_pos[0], current_y), 
                    color, font_size, alpha
                )
                current_y += line_heights[j] + 2
            
            # 添加置信度指示器
            self._draw_confidence_indicator(result_image, (x2-30, y1+10), 
                                          match_score, confidence_level, color)
        
        # 编码返回
        try:
            _, buffer = cv2.imencode('.jpg', result_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                'success': True,
                'image_base64': image_base64,
                'total_matches': len(matches),
                'match_details': matches
            }
        except Exception as e:
            return {'success': False, 'error': f'图像编码失败: {str(e)}'}
    
    def _draw_dashed_rectangle(self, image: np.ndarray, bbox: Tuple[int, int, int, int], 
                              color: Tuple[int, int, int], thickness: int = 2):
        """绘制虚线矩形"""
        x1, y1, x2, y2 = bbox
        dash_length = 10
        
        # 上边
        for x in range(x1, x2, dash_length * 2):
            cv2.line(image, (x, y1), (min(x + dash_length, x2), y1), color, thickness)
        
        # 下边
        for x in range(x1, x2, dash_length * 2):
            cv2.line(image, (x, y2), (min(x + dash_length, x2), y2), color, thickness)
        
        # 左边
        for y in range(y1, y2, dash_length * 2):
            cv2.line(image, (x1, y), (x1, min(y + dash_length, y2)), color, thickness)
        
        # 右边
        for y in range(y1, y2, dash_length * 2):
            cv2.line(image, (x2, y), (x2, min(y + dash_length, y2)), color, thickness)
    
    def _draw_confidence_indicator(self, image: np.ndarray, position: Tuple[int, int], 
                                  score: float, level: str, color: Tuple[int, int, int]):
        """绘制置信度指示器"""
        x, y = position
        bar_width = 20
        bar_height = 4
        
        # 背景条
        cv2.rectangle(image, (x, y), (x + bar_width, y + bar_height), (128, 128, 128), -1)
        
        # 置信度条
        confidence_width = int(bar_width * min(score / 100, 1.0))
        cv2.rectangle(image, (x, y), (x + confidence_width, y + bar_height), color, -1)
        
        # 边框
        cv2.rectangle(image, (x, y), (x + bar_width, y + bar_height), (255, 255, 255), 1)

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
        self.font_cache = {}  # 字体缓存，提高性能
        self.font_paths = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # 文泉驿微米黑
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",    # 文泉驿正黑
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Droid Sans
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
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
    
    def _load_font(self, size: int = 20) -> Optional[Any]:
        """加载合适的字体，支持缓存"""
        cache_key = f"font_{size}"
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
            
        for font_path in self.font_paths:
            try:
                if font_path:
                    font = ImageFont.truetype(font_path, size)
                    # 测试中文字符
                    test_text = "测试"
                    font.getbbox(test_text)
                    self.font_cache[cache_key] = font
                    return font
                else:
                    font = ImageFont.load_default()
                    self.font_cache[cache_key] = font
                    return font
            except Exception as e:
                print(f"Failed to load font {font_path}: {e}")
                continue
        return None
    
    def _get_text_size(self, text: str, font_size: int = 20) -> Tuple[int, int]:
        """获取文字尺寸，使用缓存字体"""
        font = self._load_font(font_size)
        if font:
            try:
                bbox = font.getbbox(text)
                return int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])
            except Exception as e:
                print(f"Error getting text size: {e}")
        
        # 回退到估算（考虑中文字符）
        char_count = len(text)
        # 中文字符宽度约为字体大小的0.9倍，英文约0.6倍
        avg_width = font_size * 0.8  # 平均值
        return int(char_count * avg_width), int(font_size * 1.2)
    
    def _calculate_adaptive_font_size(self, bbox: List[int], text: str, 
                                     min_size: int = 12, max_size: int = 24) -> int:
        """根据边界框大小自适应计算字体大小"""
        if len(bbox) != 4:
            return 16  # 默认大小
        
        x1, y1, x2, y2 = bbox
        box_width = x2 - x1
        box_height = y2 - y1
        
        # 基于边界框大小计算字体大小
        # 使用边界框的较小边作为参考
        min_dimension = min(box_width, box_height)
        
        # 字体大小约为边界框最小边的1/8到1/6
        font_size = max(min_size, min(max_size, min_dimension // 6))
        
        # 考虑文字长度，长文字用稍小的字体
        if len(text) > 8:
            font_size = max(min_size, int(font_size * 0.8))
        elif len(text) > 12:
            font_size = max(min_size, int(font_size * 0.7))
        
        return int(font_size)

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
        """绘制带背景的高质量文字，支持中文，增强对比度"""
        # 转换为PIL图像进行文字渲染
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        # 使用支持中文的字体
        font = self._load_font(font_size)
        if not font:
            font = ImageFont.load_default()
        
        x, y = position
        
        # 获取文字边界
        try:
            bbox = draw.textbbox((x, y), text, font=font)
        except Exception as e:
            print(f"Error getting text bbox: {e}")
            # 使用估算值
            text_width, text_height = self._get_text_size(text, font_size)
            bbox = [x, y, x + text_width, y + text_height]
        
        # 增强背景效果：双层背景
        margin = 6
        bg_bbox = [
            bbox[0] - margin, bbox[1] - margin,
            bbox[2] + margin, bbox[3] + margin
        ]
        
        # 创建多层背景效果
        overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # 外层深色背景（增强对比度）
        outer_bg_color = (0, 0, 0, int(255 * 0.8))
        overlay_draw.rectangle(bg_bbox, fill=outer_bg_color)
        
        # 内层彩色背景
        inner_margin = 2
        inner_bg_bbox = [
            bbox[0] - inner_margin, bbox[1] - inner_margin,
            bbox[2] + inner_margin, bbox[3] + inner_margin
        ]
        background_color = (*color, int(255 * alpha * 0.7))
        overlay_draw.rectangle(inner_bg_bbox, fill=background_color)
        
        # 合并背景
        pil_image = Image.alpha_composite(pil_image.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(pil_image)
        
        # 绘制文字轮廓（增强对比度）
        outline_color = (0, 0, 0)  # 黑色轮廓
        try:
            # 绘制轮廓（在主文字周围绘制黑色文字）
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
            
            # 绘制主文字（白色）
            draw.text((x, y), text, font=font, fill=(255, 255, 255))
        except Exception as e:
            print(f"Error drawing text: {e}")
            # 回退到系统默认字体
            draw.text((x, y), text, fill=(255, 255, 255))
        
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
        
        # 为不同的人分配颜色映射和智能ID
        person_color_map = {}
        person_face_count = {}  # 记录每个人员的人脸数量
        unknown_count = 0  # 未知人员计数器
        
        for i, face_info in enumerate(faces):
            bbox = face_info.get('bbox', [])
            if len(bbox) != 4:
                continue
                
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            
            # 获取人员名字，用于颜色分配
            name = face_info.get('name', f'人脸{i+1}')
            person_id = face_info.get('person_id', -1)
            
            # 智能ID分配系统
            if person_id != -1:
                # 已知人员，使用person_id作为颜色key
                color_key = f"person_{person_id}"
                
                # 计算该人员的人脸序号
                if person_id not in person_face_count:
                    person_face_count[person_id] = 0
                person_face_count[person_id] += 1
                
                # 生成显示ID
                if person_face_count[person_id] > 1:
                    # 同一人的多张脸，用字母后缀区分
                    suffix = chr(ord('A') + person_face_count[person_id] - 1)
                    id_label = f"P{person_id}{suffix}"
                else:
                    id_label = f"P{person_id}"
            else:
                # 未知人员，按检测顺序分配ID
                unknown_count += 1
                id_label = f"U{unknown_count}"
                color_key = f"unknown_{unknown_count}"
            
            if color_key not in person_color_map:
                # 分配新颜色
                color_index = len(person_color_map) % len(self.colors)
                person_color_map[color_key] = self.colors[color_index]
            
            color = person_color_map[color_key]
            
            # 绘制边框（关闭角部加强线条）
            self._draw_gradient_box(result_image, (x1, y1, x2, y2), color, 3, show_corners=False)
            
            # 添加智能ID标识
            self._draw_id_badge(result_image, [x1, y1, x2, y2], id_label, color)
            
            # 准备标签文字
            quality = face_info.get('quality', face_info.get('det_score', 0))
            confidence = face_info.get('confidence', 0)
            
            # 多行文字标签
            labels = [
                f"{id_label}: {name}",
                f"质量: {quality:.2f}",
            ]
            
            if confidence > 0:
                labels.append(f"置信: {confidence:.2f}")
            
            # 自适应字体大小
            adaptive_font_size = self._calculate_adaptive_font_size([x1, y1, x2, y2], name)
            detail_font_size = max(10, adaptive_font_size - 4)
            
            # 计算文字总尺寸
            max_width = 0
            total_height = 0
            line_heights = []
            
            for j, label in enumerate(labels):
                current_font_size = adaptive_font_size if j == 0 else detail_font_size
                w, h = self._get_text_size(label, current_font_size)
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
                current_font_size = adaptive_font_size if j == 0 else detail_font_size
                result_image = self._draw_text_with_background(
                    result_image, label, (text_pos[0], current_y), 
                    color, current_font_size, 0.7
                )
                current_y += line_heights[j] + 2
            
            # 收集详情
            face_details.append({
                'id': id_label,  # 使用格式化的ID标签
                'person_id': person_id,  # 原始人员ID
                'index': i + 1,
                'bbox': [x1, y1, x2, y2],
                'quality': float(quality),
                'confidence': float(confidence) if confidence > 0 else None,
                'name': name,
                'color': color,
                'color_key': color_key,
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
                'person_color_map': person_color_map,
                'image_size': result_image.shape[:2]
            }
        except Exception as e:
            return {
                'success': False, 
                'error': f'图像编码失败: {str(e)}'
            }
    
    def _draw_gradient_box(self, image: np.ndarray, bbox: Tuple[int, int, int, int], 
                          color: Tuple[int, int, int], thickness: int = 3, 
                          show_corners: bool = False):
        """绘制渐变边框，增加阴影效果"""
        x1, y1, x2, y2 = bbox
        
        # 添加阴影效果（在右下方绘制半透明黑色边框）
        shadow_offset = 2
        shadow_color = (0, 0, 0)
        shadow_alpha = 0.3
        
        # 创建阴影层
        shadow_overlay = image.copy()
        cv2.rectangle(shadow_overlay, 
                     (x1 + shadow_offset, y1 + shadow_offset), 
                     (x2 + shadow_offset, y2 + shadow_offset), 
                     shadow_color, thickness)
        
        # 混合阴影
        cv2.addWeighted(image, 1 - shadow_alpha, shadow_overlay, shadow_alpha, 0, image)
        
        # 主边框
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
        
        # 内边框（稍浅的颜色）
        inner_color = tuple(min(255, c + 30) for c in color)
        cv2.rectangle(image, (x1+1, y1+1), (x2-1, y2-1), inner_color, 1)
        
        # 可选的角部加强（默认关闭，避免干扰）
        if show_corners:
            corner_size = 8  # 减小尺寸
            corner_thickness = max(1, thickness - 1)  # 减小厚度
            corners = [
                ((x1, y1), (x1 + corner_size, y1), (x1, y1 + corner_size)),  # 左上
                ((x2, y1), (x2 - corner_size, y1), (x2, y1 + corner_size)),  # 右上
                ((x1, y2), (x1 + corner_size, y2), (x1, y2 - corner_size)),  # 左下
                ((x2, y2), (x2 - corner_size, y2), (x2, y2 - corner_size)),  # 右下
            ]
            
            for corner in corners:
                cv2.line(image, corner[0], corner[1], color, corner_thickness)
                cv2.line(image, corner[0], corner[2], color, corner_thickness)
    
    def _detect_overlapping_boxes(self, boxes: List[List[int]]) -> List[List[int]]:
        """检测重叠的边界框，返回避让调整后的位置"""
        if len(boxes) <= 1:
            return boxes
        
        adjusted_boxes = []
        for i, box in enumerate(boxes):
            adjusted_box = box.copy()
            
            # 检查与之前的框是否重叠
            for j in range(i):
                if self._boxes_overlap(adjusted_box, adjusted_boxes[j]):
                    # 向右下方偏移
                    offset = 10 * (j + 1)
                    adjusted_box[0] += offset
                    adjusted_box[1] += offset
                    adjusted_box[2] += offset
                    adjusted_box[3] += offset
            
            adjusted_boxes.append(adjusted_box)
        
        return adjusted_boxes
    
    def _boxes_overlap(self, box1: List[int], box2: List[int]) -> bool:
        """判断两个边界框是否重叠"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # 检查是否有重叠
        return not (x2_1 < x1_2 or x2_2 < x1_1 or y2_1 < y1_2 or y2_2 < y1_1)

    def _draw_corner_badge(self, image: np.ndarray, position: Tuple[int, int], 
                          text: str, color: Tuple[int, int, int], style: str = "circle"):
        """绘制角标，支持不同样式，增强可见性"""
        x, y = position
        
        if style == "circle":
            # 圆形角标
            radius = 16
            # 绘制阴影效果
            cv2.circle(image, (x+2, y+2), radius, (0, 0, 0), -1)
            # 绘制圆形背景
            cv2.circle(image, (x, y), radius, color, -1)
            cv2.circle(image, (x, y), radius, (255, 255, 255), 2)
            
            # 绘制文字
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            text_size = cv2.getTextSize(text, font, font_scale, 2)[0]
            text_x = x - text_size[0] // 2
            text_y = y + text_size[1] // 2
            
            cv2.putText(image, text, (text_x, text_y), font, font_scale, (255, 255, 255), 2)
            
        elif style == "square":
            # 方形角标 - 增强版
            size = 26  # 稍微增大以提高可见性
            half_size = size // 2
            
            # 绘制阴影效果
            cv2.rectangle(image, (x - half_size + 2, y - half_size + 2), 
                         (x + half_size + 2, y + half_size + 2), (0, 0, 0), -1)
            
            # 绘制方形背景（填充）
            cv2.rectangle(image, (x - half_size, y - half_size), 
                         (x + half_size, y + half_size), color, -1)
            
            # 绘制白色边框
            cv2.rectangle(image, (x - half_size, y - half_size), 
                         (x + half_size, y + half_size), (255, 255, 255), 2)
            
            # 绘制文字（白色，带黑色轮廓）
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 2
            
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = x - text_size[0] // 2
            text_y = y + text_size[1] // 2
            
            # 黑色轮廓
            cv2.putText(image, text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness + 1)
            # 白色文字
            cv2.putText(image, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)
    
    def _draw_id_badge(self, image: np.ndarray, bbox: List[int], face_id, 
                      color: Tuple[int, int, int]):
        """在边界框左上角绘制清晰的ID标识，智能位置调整"""
        x1, y1, x2, y2 = bbox
        img_height, img_width = image.shape[:2]
        
        # 计算ID标签的理想位置和实际可用位置
        badge_size = 24  # 方形角标的大小
        margin = 5
        
        # 优先位置选择（按优先级排序）
        positions = [
            # 1. 左上角外侧（默认）
            (x1 - badge_size//2 - margin, y1 - badge_size//2 - margin),
            # 2. 右上角外侧  
            (x2 + margin + badge_size//2, y1 - badge_size//2 - margin),
            # 3. 左下角外侧
            (x1 - badge_size//2 - margin, y2 + margin + badge_size//2),
            # 4. 右下角外侧
            (x2 + margin + badge_size//2, y2 + margin + badge_size//2),
            # 5. 左上角内侧
            (x1 + badge_size//2 + margin, y1 + badge_size//2 + margin),
            # 6. 右上角内侧
            (x2 - badge_size//2 - margin, y1 + badge_size//2 + margin),
            # 7. 中心上方
            ((x1 + x2) // 2, y1 - badge_size//2 - margin),
            # 8. 中心下方
            ((x1 + x2) // 2, y2 + badge_size//2 + margin)
        ]
        
        # 选择第一个在图像边界内的位置
        final_position = None
        for pos_x, pos_y in positions:
            if (badge_size//2 <= pos_x <= img_width - badge_size//2 and
                badge_size//2 <= pos_y <= img_height - badge_size//2):
                final_position = (pos_x, pos_y)
                break
        
        # 如果都不合适，使用安全的边界位置
        if final_position is None:
            safe_x = max(badge_size//2, min(x1, img_width - badge_size//2))
            safe_y = max(badge_size//2, min(y1, img_height - badge_size//2))
            final_position = (safe_x, safe_y)
        
        # 绘制ID标签
        self._draw_corner_badge(image, final_position, str(face_id), 
                               color, style="square")
    
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
        match_details = []  # 添加详情收集
        
        # 为不同的人分配颜色映射和智能ID
        person_color_map = {}
        person_face_count = {}  # 记录每个人员的人脸数量
        unknown_count = 0  # 未知人员计数器
        
        for i, match in enumerate(matches):
            bbox = match.get('bbox', [])
            if len(bbox) != 4:
                continue
                
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            
            # 根据匹配度确定颜色和样式
            match_score = match.get('match_score', 0)
            person_id = match.get('person_id', -1)
            name = match.get('name', '未知')
            is_known = person_id != -1
            
            # 智能ID分配系统
            if person_id != -1:
                # 已知人员，使用person_id作为颜色key
                color_key = f"person_{person_id}"
                
                # 计算该人员的人脸序号
                if person_id not in person_face_count:
                    person_face_count[person_id] = 0
                person_face_count[person_id] += 1
                
                # 生成显示ID
                if person_face_count[person_id] > 1:
                    # 同一人的多张脸，用字母后缀区分
                    suffix = chr(ord('A') + person_face_count[person_id] - 1)
                    id_label = f"P{person_id}{suffix}"
                else:
                    id_label = f"P{person_id}"
            else:
                # 未知人员，按检测顺序分配ID
                unknown_count += 1
                id_label = f"U{unknown_count}"
                color_key = f"unknown_{unknown_count}"
            
            if color_key not in person_color_map:
                # 分配新颜色
                color_index = len(person_color_map) % len(self.colors)
                person_color_map[color_key] = self.colors[color_index]
            
            base_color = person_color_map[color_key]
            
            # 根据置信度确定样式
            if is_known and match_score >= threshold * 100:
                # 已知人员，高置信度
                confidence_level = "high"
                # 保持原色亮度
                color_intensity = 1.0
            elif is_known and match_score >= threshold * 50:
                # 已知人员，中等置信度
                confidence_level = "medium"
                color_intensity = 0.8
            elif is_known:
                # 已知人员，低置信度
                confidence_level = "low"
                color_intensity = 0.6
            else:
                # 未知人员
                confidence_level = "unknown"
                color_intensity = 0.5
                # 未知人员使用红色系
                base_color = (0, 0, 200)
            
            # 调整颜色亮度
            color = (
                int(base_color[0] * color_intensity),
                int(base_color[1] * color_intensity),
                int(base_color[2] * color_intensity)
            )
            
            # 绘制不同样式的边框
            if confidence_level == "high":
                self._draw_gradient_box(result_image, (x1, y1, x2, y2), color, 4, show_corners=False)
            elif confidence_level == "medium":
                cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 3)
                # 添加虚线效果
                self._draw_dashed_rectangle(result_image, (x1, y1, x2, y2), color, 2)
            elif confidence_level == "low":
                cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
            else:
                # 未知人员用虚线框
                self._draw_dashed_rectangle(result_image, (x1, y1, x2, y2), color, 3)
            
            # 添加智能ID标识
            self._draw_id_badge(result_image, [x1, y1, x2, y2], id_label, color)
            
            # 准备标签
            distance = match.get('distance', 0)
            quality = match.get('quality', 0)
            
            labels = [
                f"{id_label}: {name}",
                f"匹配: {match_score:.1f}%",
                f"距离: {distance:.3f}",
            ]
            
            if quality > 0:
                labels.append(f"质量: {quality:.2f}")
            
            # 自适应字体大小
            adaptive_font_size = self._calculate_adaptive_font_size([x1, y1, x2, y2], name)
            detail_font_size = max(10, adaptive_font_size - 4)
            
            # 计算并绘制文字
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
            
            # 添加置信度指示器
            self._draw_confidence_indicator(result_image, (x2-30, y1+10), 
                                          match_score, confidence_level, color)
            
            # 收集详情
            match_details.append({
                'id': id_label,  # 使用格式化的ID标签
                'person_id': person_id,  # 原始人员ID
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
        
        # 编码返回
        try:
            _, buffer = cv2.imencode('.jpg', result_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                'success': True,
                'image_base64': image_base64,
                'total_matches': len(matches),
                'match_details': match_details,  # 使用更新后的详情
                'person_color_map': person_color_map
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

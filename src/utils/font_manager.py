"""
中文字体管理器
确保在不同环境下都能正确显示中文字符
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Tuple, Union
import logging

logger = logging.getLogger(__name__)

class FontManager:
    """中文字体管理器"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """初始化字体管理器
        
        Args:
            base_dir: 项目根目录，如果不指定则自动检测
        """
        if base_dir is None:
            # 自动检测项目根目录
            current_file = Path(__file__).resolve()
            # 从当前文件向上查找到包含main.py的目录
            base_dir = current_file.parent
            while base_dir.parent != base_dir:
                if (base_dir / "main.py").exists():
                    break
                base_dir = base_dir.parent
        
        self.base_dir = Path(base_dir)
        self.font_cache = {}  # 字体缓存
        
        # 项目内字体路径
        self.project_fonts_dir = self.base_dir / "assets" / "fonts"
        
        # 字体查找优先级列表（从高到低）
        self.font_search_paths = self._build_font_search_paths()
        
        # 确保项目字体目录存在
        self.project_fonts_dir.mkdir(parents=True, exist_ok=True)
        
    def _build_font_search_paths(self) -> List[str]:
        """构建字体搜索路径列表"""
        paths = []
        
        # 1. 项目内字体（最高优先级）
        if self.project_fonts_dir.exists():
            for font_file in self.project_fonts_dir.glob("*.tt*"):
                paths.append(str(font_file))
        
        # 2. Linux系统字体路径
        linux_paths = [
            # 文泉驿字体（推荐）
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            
            # Noto字体
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc",
            
            # Droid字体
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            
            # 思源字体
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/arphic/uming.ttc",
            "/usr/share/fonts/truetype/arphic/ukai.ttc",
            
            # Liberation字体（备用）
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        
        # 3. Windows系统字体路径
        windows_paths = [
            "C:/Windows/Fonts/simhei.ttf",       # 黑体
            "C:/Windows/Fonts/simsun.ttc",       # 宋体
            "C:/Windows/Fonts/msyh.ttc",         # 微软雅黑
            "C:/Windows/Fonts/msyhbd.ttc",       # 微软雅黑粗体
            "C:/Windows/Fonts/simkai.ttf",       # 楷体
            "C:/Windows/Fonts/simfang.ttf",      # 仿宋
        ]
        
        # 4. macOS系统字体路径
        macos_paths = [
            "/System/Library/Fonts/PingFang.ttc",                    # 苹方
            "/System/Library/Fonts/Hiragino Sans GB.ttc",           # 冬青黑体
            "/Library/Fonts/Arial Unicode MS.ttf",                   # Arial Unicode
            "/System/Library/Fonts/STHeiti Light.ttc",              # 华文黑体
            "/System/Library/Fonts/STHeiti Medium.ttc",
        ]
        
        # 根据系统类型添加路径
        if sys.platform.startswith('linux'):
            paths.extend(linux_paths)
        elif sys.platform.startswith('win'):
            paths.extend(windows_paths)
        elif sys.platform.startswith('darwin'):
            paths.extend(macos_paths)
        
        # 添加所有系统的路径作为备用
        paths.extend(linux_paths)
        paths.extend(windows_paths)
        paths.extend(macos_paths)
        
        return paths
    
    def get_font(self, size: int = 20) -> Optional[Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]]:
        """获取可用的中文字体
        
        Args:
            size: 字体大小
            
        Returns:
            字体对象，如果找不到返回None
        """
        cache_key = f"font_{size}"
        
        # 检查缓存
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        # 尝试每个字体路径
        for font_path in self.font_search_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, size)
                    
                    # 测试字体是否支持中文
                    if self._test_chinese_support(font):
                        self.font_cache[cache_key] = font
                        logger.info(f"成功加载字体: {font_path}, 大小: {size}")
                        return font
                        
                except Exception as e:
                    logger.debug(f"加载字体失败 {font_path}: {e}")
                    continue
        
        # 如果没有找到合适的字体，尝试使用默认字体
        try:
            default_font = ImageFont.load_default()
            logger.warning(f"未找到中文字体，使用系统默认字体，大小: {size}")
            self.font_cache[cache_key] = default_font
            return default_font
        except Exception as e:
            logger.error(f"无法加载默认字体: {e}")
            return None
    
    def _test_chinese_support(self, font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]) -> bool:
        """测试字体是否支持中文字符
        
        Args:
            font: 要测试的字体对象
            
        Returns:
            是否支持中文
        """
        try:
            # 测试常用中文字符
            test_chars = ["中", "文", "测", "试", "字", "体"]
            
            # 创建临时图像进行测试
            img = Image.new('RGB', (100, 50), color='white')
            draw = ImageDraw.Draw(img)
            
            for char in test_chars:
                bbox = draw.textbbox((0, 0), char, font=font)
                # 如果字符有宽度，说明字体支持该字符
                if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
                    return True
            
            return False
        except Exception:
            return False
    
    def get_available_fonts(self) -> List[dict]:
        """获取所有可用字体的信息
        
        Returns:
            字体信息列表
        """
        available_fonts = []
        
        for font_path in self.font_search_paths:
            if os.path.exists(font_path):
                try:
                    # 尝试加载字体
                    test_font = ImageFont.truetype(font_path, 16)
                    supports_chinese = self._test_chinese_support(test_font)
                    
                    font_info = {
                        'path': font_path,
                        'name': os.path.basename(font_path),
                        'size_on_disk': os.path.getsize(font_path),
                        'supports_chinese': supports_chinese,
                        'is_project_font': str(self.project_fonts_dir) in font_path
                    }
                    available_fonts.append(font_info)
                    
                except Exception as e:
                    logger.debug(f"检测字体时出错 {font_path}: {e}")
        
        return available_fonts
    
    def install_project_fonts(self) -> bool:
        """确保项目字体已安装
        
        Returns:
            是否成功安装项目字体
        """
        try:
            # 检查系统是否有文泉驿字体
            system_wqy_paths = [
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
            ]
            
            project_font_installed = False
            
            for sys_font_path in system_wqy_paths:
                if os.path.exists(sys_font_path):
                    # 复制到项目字体目录
                    font_name = os.path.basename(sys_font_path)
                    dest_path = self.project_fonts_dir / font_name
                    
                    if not dest_path.exists():
                        try:
                            import shutil
                            shutil.copy2(sys_font_path, dest_path)
                            logger.info(f"已复制系统字体到项目: {dest_path}")
                            project_font_installed = True
                        except Exception as e:
                            logger.error(f"复制字体失败: {e}")
                    else:
                        logger.info(f"项目字体已存在: {dest_path}")
                        project_font_installed = True
            
            return project_font_installed
            
        except Exception as e:
            logger.error(f"安装项目字体时出错: {e}")
            return False
    
    def get_text_size(self, text: str, font_size: int = 20) -> Tuple[int, int]:
        """获取文本渲染后的尺寸
        
        Args:
            text: 要测量的文本
            font_size: 字体大小
            
        Returns:
            (width, height) 文本尺寸
        """
        font = self.get_font(font_size)
        if font:
            try:
                # 创建临时图像来测量文本
                img = Image.new('RGB', (1, 1))
                draw = ImageDraw.Draw(img)
                bbox = draw.textbbox((0, 0), text, font=font)
                return int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])
            except Exception:
                pass
        
        # 回退估算方法
        char_count = len(text)
        # 中文字符通常比英文字符宽
        avg_char_width = font_size * 0.8  # 平均字符宽度
        text_height = font_size * 1.2     # 文本高度
        
        return int(char_count * avg_char_width), int(text_height)
    
    def clear_cache(self):
        """清空字体缓存"""
        self.font_cache.clear()
        logger.info("字体缓存已清空")

# 全局字体管理器实例
_font_manager = None

def get_font_manager() -> FontManager:
    """获取全局字体管理器实例"""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager

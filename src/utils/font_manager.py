"""
Chinese font manager
Ensure that Chinese characters can be displayed correctly in different environments
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Tuple, Union
import logging

logger = logging.getLogger(__name__)

class FontManager:
    """Chinese font manager"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize font manager
        
        Args:
            base_dir: Project root directory，If not specified, it will be automatically detected.
        """
        if base_dir is None:
            # Automatically detect project root directory
            current_file = Path(__file__).resolve()
            # Search upwards from the current file to includemain.pydirectory
            base_dir = current_file.parent
            while base_dir.parent != base_dir:
                if (base_dir / "main.py").exists():
                    break
                base_dir = base_dir.parent
        
        self.base_dir = Path(base_dir)
        self.font_cache = {}  # Font cache
        
        # Font path within the project
        self.project_fonts_dir = self.base_dir / "assets" / "fonts"
        
        # Font lookup priority list（from high to low）
        self.font_search_paths = self._build_font_search_paths()
        
        # Make sure the project font directory exists
        self.project_fonts_dir.mkdir(parents=True, exist_ok=True)
        
    def _build_font_search_paths(self) -> List[str]:
        """Build a list of font search paths"""
        paths = []
        
        # 1. Fonts within the project（highest priority）
        if self.project_fonts_dir.exists():
            for font_file in self.project_fonts_dir.glob("*.tt*"):
                paths.append(str(font_file))
        
        # 2. LinuxSystem font path
        linux_paths = [
            # Wenquanyi font（recommend）
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            
            # Notofont
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc",
            
            # Droidfont
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            
            # Siyuan font
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/arphic/uming.ttc",
            "/usr/share/fonts/truetype/arphic/ukai.ttc",
            
            # Liberationfont（spare）
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        
        # 3. WindowsSystem font path
        windows_paths = [
            "C:/Windows/Fonts/simhei.ttf",       # black body
            "C:/Windows/Fonts/simsun.ttc",       # Song Dynasty
            "C:/Windows/Fonts/msyh.ttc",         # Microsoft Yahei
            "C:/Windows/Fonts/msyhbd.ttc",       # Microsoft Yahei Bold
            "C:/Windows/Fonts/simkai.ttf",       # regular script
            "C:/Windows/Fonts/simfang.ttf",      # Imitation of Song Dynasty
        ]
        
        # 4. macOSSystem font path
        macos_paths = [
            "/System/Library/Fonts/PingFang.ttc",                    # Pingfang
            "/System/Library/Fonts/Hiragino Sans GB.ttc",           # holly blackbody
            "/Library/Fonts/Arial Unicode MS.ttf",                   # Arial Unicode
            "/System/Library/Fonts/STHeiti Light.ttc",              # Chinese boldface
            "/System/Library/Fonts/STHeiti Medium.ttc",
        ]
        
        # Add paths based on system type
        if sys.platform.startswith('linux'):
            paths.extend(linux_paths)
        elif sys.platform.startswith('win'):
            paths.extend(windows_paths)
        elif sys.platform.startswith('darwin'):
            paths.extend(macos_paths)
        
        # Add paths to all systems as fallback
        paths.extend(linux_paths)
        paths.extend(windows_paths)
        paths.extend(macos_paths)
        
        return paths
    
    def get_font(self, size: int = 20) -> Optional[Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]]:
        """Get available Chinese fonts
        
        Args:
            size: font size
            
        Returns:
            font object，If not found returnNone
        """
        cache_key = f"font_{size}"
        
        # Check cache
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        # Try each font path
        for font_path in self.font_search_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, size)
                    
                    # Test whether the font supports Chinese
                    if self._test_chinese_support(font):
                        self.font_cache[cache_key] = font
                        logger.info(f"Font loaded successfully: {font_path}, size: {size}")
                        return font
                        
                except Exception as e:
                    logger.debug(f"Failed to load font {font_path}: {e}")
                    continue
        
        # If no suitable font is found，Try using default font
        try:
            default_font = ImageFont.load_default()
            logger.warning(f"Chinese font not found，Use system default font，size: {size}")
            self.font_cache[cache_key] = default_font
            return default_font
        except Exception as e:
            logger.error(f"Unable to load default font: {e}")
            return None
    
    def _test_chinese_support(self, font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]) -> bool:
        """Test whether the font supports Chinese characters
        
        Args:
            font: the font object to test
            
        Returns:
            Whether to support Chinese
        """
        try:
            # Test common Chinese characters
            test_chars = ["middle", "arts", "test", "try", "Character", "body"]
            
            # Create a temporary image for testing
            img = Image.new('RGB', (100, 50), color='white')
            draw = ImageDraw.Draw(img)
            
            for char in test_chars:
                bbox = draw.textbbox((0, 0), char, font=font)
                # If the character has width，Indicates that the font supports this character
                if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
                    return True
            
            return False
        except Exception:
            return False
    
    def get_available_fonts(self) -> List[dict]:
        """Get information about all available fonts
        
        Returns:
            Font information list
        """
        available_fonts = []
        
        for font_path in self.font_search_paths:
            if os.path.exists(font_path):
                try:
                    # Try loading fonts
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
                    logger.debug(f"Error while detecting font {font_path}: {e}")
        
        return available_fonts
    
    def install_project_fonts(self) -> bool:
        """Make sure project fonts are installed
        
        Returns:
            Whether the project font was successfully installed
        """
        try:
            # Check whether the system has Wenquanyi font
            system_wqy_paths = [
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
            ]
            
            project_font_installed = False
            
            for sys_font_path in system_wqy_paths:
                if os.path.exists(sys_font_path):
                    # Copy to project font directory
                    font_name = os.path.basename(sys_font_path)
                    dest_path = self.project_fonts_dir / font_name
                    
                    if not dest_path.exists():
                        try:
                            import shutil
                            shutil.copy2(sys_font_path, dest_path)
                            logger.info(f"Copied system fonts to project: {dest_path}")
                            project_font_installed = True
                        except Exception as e:
                            logger.error(f"Failed to copy font: {e}")
                    else:
                        logger.info(f"Project font already exists: {dest_path}")
                        project_font_installed = True
            
            return project_font_installed
            
        except Exception as e:
            logger.error(f"Error installing project fonts: {e}")
            return False
    
    def get_text_size(self, text: str, font_size: int = 20) -> Tuple[int, int]:
        """Get the size of text after rendering
        
        Args:
            text: text to measure
            font_size: font size
            
        Returns:
            (width, height) text size
        """
        font = self.get_font(font_size)
        if font:
            try:
                # Create temporary image to measure text
                img = Image.new('RGB', (1, 1))
                draw = ImageDraw.Draw(img)
                bbox = draw.textbbox((0, 0), text, font=font)
                return int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])
            except Exception:
                pass
        
        # Fallback estimation method
        char_count = len(text)
        # Chinese characters are usually wider than English characters
        avg_char_width = font_size * 0.8  # average character width
        text_height = font_size * 1.2     # text height
        
        return int(char_count * avg_char_width), int(text_height)
    
    def clear_cache(self):
        """Clear font cache"""
        self.font_cache.clear()
        logger.info("Font cache cleared")

# Global font manager instance
_font_manager = None

def get_font_manager() -> FontManager:
    """Get global font manager instance"""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager

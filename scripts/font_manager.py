#!/usr/bin/env python3
"""
字体管理CLI工具
帮助管理项目中的中文字体资源
"""

import sys
import os
from pathlib import Path
import argparse
import logging

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.utils.font_manager import FontManager, get_font_manager

def setup_logging(verbose: bool = False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def list_fonts(args):
    """列出可用字体"""
    font_manager = get_font_manager()
    available_fonts = font_manager.get_available_fonts()
    
    if not available_fonts:
        print("❌ 未找到任何可用字体")
        return
    
    print(f"📝 找到 {len(available_fonts)} 个字体:")
    print()
    
    # 分类显示
    project_fonts = [f for f in available_fonts if f['is_project_font']]
    system_fonts = [f for f in available_fonts if not f['is_project_font']]
    chinese_fonts = [f for f in available_fonts if f['supports_chinese']]
    
    print("🎯 项目内字体:")
    if project_fonts:
        for font in project_fonts:
            size_mb = font['size_on_disk'] / (1024 * 1024)
            chinese_support = "✅" if font['supports_chinese'] else "❌"
            print(f"  {chinese_support} {font['name']} ({size_mb:.1f}MB)")
            print(f"      路径: {font['path']}")
    else:
        print("  (无)")
    
    print("\n💻 系统字体:")
    if system_fonts:
        for font in system_fonts[:10]:  # 只显示前10个，避免输出过多
            size_mb = font['size_on_disk'] / (1024 * 1024)
            chinese_support = "✅" if font['supports_chinese'] else "❌"
            print(f"  {chinese_support} {font['name']} ({size_mb:.1f}MB)")
        
        if len(system_fonts) > 10:
            print(f"  ... 还有 {len(system_fonts) - 10} 个字体")
    else:
        print("  (无)")
    
    print(f"\n🇨🇳 支持中文的字体: {len(chinese_fonts)}/{len(available_fonts)}")

def install_fonts(args):
    """安装项目字体"""
    print("🔧 安装项目字体...")
    font_manager = get_font_manager()
    
    success = font_manager.install_project_fonts()
    
    if success:
        print("✅ 项目字体安装成功!")
    else:
        print("❌ 项目字体安装失败，请检查系统是否有可用的中文字体")
        print("💡 建议运行: sudo apt-get install fonts-wqy-microhei fonts-wqy-zenhei")

def test_fonts(args):
    """测试字体渲染"""
    print("🧪 测试字体渲染...")
    font_manager = get_font_manager()
    
    test_text = args.text if args.text else "中文字体测试 Font Test 123"
    font_sizes = [12, 16, 20, 24, 32] if args.sizes else [20]
    
    print(f"测试文本: '{test_text}'")
    print()
    
    for size in font_sizes:
        print(f"📏 字体大小: {size}")
        font = font_manager.get_font(size)
        
        if font:
            text_size = font_manager.get_text_size(test_text, size)
            print(f"  ✅ 字体加载成功")
            print(f"  📐 渲染尺寸: {text_size[0]}x{text_size[1]} 像素")
            
            # 尝试创建测试图像
            try:
                from PIL import Image, ImageDraw
                img = Image.new('RGB', (max(200, text_size[0] + 20), text_size[1] + 20), 'white')
                draw = ImageDraw.Draw(img)
                draw.text((10, 10), test_text, font=font, fill='black')
                
                # 保存测试图像
                test_file = Path(f"font_test_{size}px.png")
                img.save(test_file)
                print(f"  💾 测试图像已保存: {test_file}")
                
            except Exception as e:
                print(f"  ⚠️  无法创建测试图像: {e}")
        else:
            print(f"  ❌ 字体加载失败")
        
        print()

def check_environment(args):
    """检查字体环境"""
    print("🔍 检查字体环境...")
    
    # 检查系统类型
    import platform
    print(f"🖥️  操作系统: {platform.system()} {platform.release()}")
    
    # 检查系统字体目录
    font_dirs = [
        "/usr/share/fonts",
        "/usr/local/share/fonts", 
        "~/.fonts",
        "C:/Windows/Fonts",
        "/System/Library/Fonts"
    ]
    
    print("\n📁 系统字体目录:")
    for font_dir in font_dirs:
        expanded_dir = os.path.expanduser(font_dir)
        if os.path.exists(expanded_dir):
            print(f"  ✅ {font_dir}")
        else:
            print(f"  ❌ {font_dir}")
    
    # 检查项目字体目录
    font_manager = get_font_manager()
    project_fonts_dir = font_manager.project_fonts_dir
    print(f"\n🎯 项目字体目录: {project_fonts_dir}")
    
    if project_fonts_dir.exists():
        font_files = list(project_fonts_dir.glob("*.tt*"))
        print(f"  ✅ 目录存在，包含 {len(font_files)} 个字体文件")
        for font_file in font_files:
            size_mb = font_file.stat().st_size / (1024 * 1024)
            print(f"    📄 {font_file.name} ({size_mb:.1f}MB)")
    else:
        print("  ❌ 目录不存在")
    
    # 检查字体配置
    print("\n⚙️  字体配置:")
    try:
        import subprocess
        result = subprocess.run(['fc-list', ':lang=zh'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            chinese_fonts_count = len(result.stdout.strip().split('\n'))
            print(f"  ✅ 系统中文字体数量: {chinese_fonts_count}")
        else:
            print("  ⚠️  无法获取系统字体信息")
    except Exception as e:
        print(f"  ⚠️  字体配置检查失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="字体管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python scripts/font_manager.py list                    # 列出所有字体
  python scripts/font_manager.py install                 # 安装项目字体
  python scripts/font_manager.py test                    # 测试字体渲染
  python scripts/font_manager.py test --text "测试文本"    # 测试自定义文本
  python scripts/font_manager.py check                   # 检查字体环境
        """
    )
    
    parser.add_argument('-v', '--verbose', 
                       action='store_true',
                       help='详细输出')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出可用字体')
    list_parser.set_defaults(func=list_fonts)
    
    # install 命令 
    install_parser = subparsers.add_parser('install', help='安装项目字体')
    install_parser.set_defaults(func=install_fonts)
    
    # test 命令
    test_parser = subparsers.add_parser('test', help='测试字体渲染')
    test_parser.add_argument('--text', help='测试文本')
    test_parser.add_argument('--sizes', action='store_true', help='测试多种字体大小')
    test_parser.set_defaults(func=test_fonts)
    
    # check 命令
    check_parser = subparsers.add_parser('check', help='检查字体环境')
    check_parser.set_defaults(func=check_environment)
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n❌ 操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

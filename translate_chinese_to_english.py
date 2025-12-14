#!/usr/bin/env python3
"""
Chinese to English Translation Script
Automatically translates Chinese text in source files to English using Google Translate
"""

import re
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

try:
    from googletrans import Translator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    print("⚠️  googletrans not installed. Installing now...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "googletrans==4.0.0-rc1"])
    from googletrans import Translator
    TRANSLATOR_AVAILABLE = True


class ChineseTranslator:
    def __init__(self):
        self.translator = Translator()
        self.chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        self.translations_cache = {}
        
    def detect_chinese(self, text):
        """Detect Chinese characters in text"""
        return self.chinese_pattern.findall(text)
    
    def translate_text(self, text, use_cache=True):
        """Translate Chinese text to English"""
        if not text or not text.strip():
            return text
            
        # Check cache first
        if use_cache and text in self.translations_cache:
            return self.translations_cache[text]
        
        try:
            # Translate using Google Translate
            result = self.translator.translate(text, src='zh-cn', dest='en')
            translated = result.text
            
            # Cache the translation
            self.translations_cache[text] = translated
            return translated
        except Exception as e:
            print(f"⚠️  Translation failed for '{text}': {e}")
            return text
    
    def translate_line(self, line):
        """Translate Chinese segments in a line while preserving code structure"""
        chinese_segments = self.chinese_pattern.finditer(line)
        translated_line = line
        
        # Process segments in reverse order to maintain positions
        segments_to_replace = []
        for match in chinese_segments:
            chinese_text = match.group()
            start, end = match.span()
            segments_to_replace.append((start, end, chinese_text))
        
        # Replace from end to start to maintain indices
        for start, end, chinese_text in reversed(segments_to_replace):
            translated = self.translate_text(chinese_text)
            translated_line = translated_line[:start] + translated + translated_line[end:]
        
        return translated_line
    
    def translate_file(self, file_path, create_backup=True, dry_run=False):
        """Translate Chinese text in a file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return False
        
        print(f"\n{'='*80}")
        print(f"📄 Processing: {file_path}")
        print(f"{'='*80}")
        
        # Create backup
        if create_backup and not dry_run:
            backup_path = file_path.with_suffix(file_path.suffix + '.backup')
            shutil.copy2(file_path, backup_path)
            print(f"💾 Backup created: {backup_path}")
        
        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            print(f"⚠️  Cannot read file as UTF-8, skipping: {file_path}")
            return False
        
        translated_lines = []
        changes_made = 0
        
        for line_num, line in enumerate(lines, 1):
            chinese_found = self.detect_chinese(line)
            
            if chinese_found:
                translated_line = self.translate_line(line)
                
                if translated_line != line:
                    changes_made += 1
                    print(f"\n📍 Line {line_num}:")
                    print(f"   BEFORE: {line.rstrip()}")
                    print(f"   AFTER:  {translated_line.rstrip()}")
                    print(f"   Chinese found: {', '.join(chinese_found)}")
                
                translated_lines.append(translated_line)
            else:
                translated_lines.append(line)
        
        if changes_made == 0:
            print("✅ No Chinese text found in this file")
            return True
        
        print(f"\n📊 Total changes: {changes_made} lines")
        
        if dry_run:
            print("🔍 DRY RUN MODE - No changes written to file")
            return True
        
        # Write translated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(translated_lines)
        
        print(f"✅ File translated successfully!")
        return True
    
    def scan_directory(self, directory, file_patterns=None):
        """Scan directory for files with Chinese text"""
        directory = Path(directory)
        
        if file_patterns is None:
            file_patterns = ['*.py', '*.js', '*.html', '*.css', '*.json', '*.md', '*.txt']
        
        files_with_chinese = []
        
        print(f"\n🔍 Scanning directory: {directory}")
        print(f"   Patterns: {', '.join(file_patterns)}\n")
        
        for pattern in file_patterns:
            for file_path in directory.rglob(pattern):
                # Skip backup files and __pycache__
                if '.backup' in file_path.name or '__pycache__' in str(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        chinese_found = self.detect_chinese(content)
                        
                        if chinese_found:
                            files_with_chinese.append({
                                'path': file_path,
                                'count': len(chinese_found)
                            })
                except:
                    continue
        
        return files_with_chinese


def main():
    """Main function"""
    translator = ChineseTranslator()
    
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "Chinese to English Translator" + " "*29 + "║")
    print("╚" + "="*78 + "╝")
    
    if len(sys.argv) < 2:
        print("\n📖 Usage:")
        print("   python translate_chinese_to_english.py <file_path>              # Translate a single file")
        print("   python translate_chinese_to_english.py --scan <directory>       # Scan directory for Chinese text")
        print("   python translate_chinese_to_english.py --dry-run <file_path>    # Preview changes without writing")
        print("\n💡 Examples:")
        print("   python translate_chinese_to_english.py src/services/advanced_face_service.py")
        print("   python translate_chinese_to_english.py --scan src/")
        print("   python translate_chinese_to_english.py --dry-run web/assets/js/analytics.js")
        sys.exit(1)
    
    # Parse arguments
    if sys.argv[1] == '--scan':
        if len(sys.argv) < 3:
            print("❌ Please provide a directory to scan")
            sys.exit(1)
        
        directory = sys.argv[2]
        files = translator.scan_directory(directory)
        
        if not files:
            print("✅ No files with Chinese text found!")
        else:
            print(f"\n📋 Found {len(files)} files with Chinese text:\n")
            for idx, file_info in enumerate(files, 1):
                print(f"   {idx}. {file_info['path']} ({file_info['count']} Chinese segments)")
            
            print(f"\n💡 To translate a file, run:")
            print(f"   python translate_chinese_to_english.py <file_path>")
    
    elif sys.argv[1] == '--dry-run':
        if len(sys.argv) < 3:
            print("❌ Please provide a file path")
            sys.exit(1)
        
        file_path = sys.argv[2]
        translator.translate_file(file_path, create_backup=False, dry_run=True)
    
    else:
        file_path = sys.argv[1]
        
        # Confirm translation
        print(f"\n⚠️  This will translate Chinese text to English in:")
        print(f"   {file_path}")
        print(f"\n   A backup file will be created with .backup extension")
        
        response = input("\n❓ Continue? (yes/no): ").strip().lower()
        
        if response in ['yes', 'y']:
            translator.translate_file(file_path, create_backup=True, dry_run=False)
            print("\n✅ Translation complete!")
            print("\n💡 Tips:")
            print("   - Check the translated file to ensure code functionality")
            print("   - Restore from .backup file if needed")
            print("   - Delete __pycache__ folders and restart server for changes to take effect")
        else:
            print("\n❌ Translation cancelled")


if __name__ == "__main__":
    main()

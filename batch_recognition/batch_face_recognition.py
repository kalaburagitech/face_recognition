#!/usr/bin/env python3
"""
批量人脸识别脚本
支持并发处理、进度条显示、断点续传功能
"""

import os
import csv
import json
import argparse
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from tqdm.asyncio import tqdm
import logging
from datetime import datetime
import mimetypes

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_recognition.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 设置环境变量以避免Windows编码问题
import os
if os.name == 'nt':  # Windows系统
    os.environ['PYTHONIOENCODING'] = 'utf-8'

class BatchFaceRecognition:
    def __init__(self, api_url: str = "https://chatchat.hupu.io/api/recognize", 
                 max_concurrent: int = 5, disable_ssl_verify: bool = False, 
                 prioritize_known: bool = False):
        self.api_url = api_url
        self.max_concurrent = max_concurrent
        self.disable_ssl_verify = disable_ssl_verify
        self.prioritize_known = prioritize_known
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 支持的图片格式
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.avif'}
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = None
        
        if self.disable_ssl_verify:
            # 创建SSL上下文，禁用SSL验证（适用于某些网络环境）
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            logger.warning("SSL验证已禁用，仅在必要时使用")
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60, connect=10),
            connector=connector
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def get_image_files(self, folder_path: str) -> List[Path]:
        """获取文件夹中的所有图片文件"""
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"文件夹不存在: {folder_path}")
        
        image_files = []
        for file_path in folder.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                image_files.append(file_path)
        
        logger.info(f"找到 {len(image_files)} 个图片文件")
        return sorted(image_files)
    
    def load_progress(self, progress_file: str) -> set:
        """加载已处理的文件列表（断点续传）"""
        if not os.path.exists(progress_file):
            return set()
        
        processed_files = set()
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                for line in f:
                    processed_files.add(line.strip())
            logger.info(f"加载已处理文件 {len(processed_files)} 个")
        except Exception as e:
            logger.warning(f"加载进度文件失败: {e}")
        
        return processed_files
    
    def save_progress(self, progress_file: str, file_path: str):
        """保存处理进度"""
        with open(progress_file, 'a', encoding='utf-8') as f:
            f.write(f"{file_path}\n")
    
    async def recognize_single_image(self, image_path: Path) -> Dict[str, Any]:
        """识别单张图片"""
        async with self.semaphore:
            try:
                # 确定文件的MIME类型
                mime_type, _ = mimetypes.guess_type(str(image_path))
                if not mime_type or not mime_type.startswith('image/'):
                    mime_type = 'image/jpeg'  # 默认类型
                
                # 读取图片文件
                async with aiofiles.open(image_path, 'rb') as f:
                    file_content = await f.read()
                
                # 构建表单数据
                data = aiohttp.FormData()
                data.add_field(
                    'file',
                    file_content,
                    filename=image_path.name,
                    content_type=mime_type
                )
                
                # 发送请求
                async with self.session.post(self.api_url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'file_path': str(image_path),
                            'file_name': image_path.name,
                            'success': True,
                            'response': result,
                            'error': None
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'file_path': str(image_path),
                            'file_name': image_path.name,
                            'success': False,
                            'response': None,
                            'error': f"HTTP {response.status}: {error_text}"
                        }
                        
            except aiohttp.ClientSSLError as e:
                # SSL错误特殊处理
                return {
                    'file_path': str(image_path),
                    'file_name': image_path.name,
                    'success': False,
                    'response': None,
                    'error': f"SSL错误: {str(e)} (可尝试使用 --disable-ssl-verify 选项)"
                }
            except asyncio.TimeoutError:
                return {
                    'file_path': str(image_path),
                    'file_name': image_path.name,
                    'success': False,
                    'response': None,
                    'error': "请求超时"
                }
            except Exception as e:
                return {
                    'file_path': str(image_path),
                    'file_name': image_path.name,
                    'success': False,
                    'response': None,
                    'error': str(e)
                }
    
    def flatten_recognition_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """将识别结果扁平化为CSV行数据"""
        row = {
            'file_path': result['file_path'],
            'file_name': result['file_name'],
            'success': result['success'],
            'error': result['error']
        }
        
        if result['success'] and result['response']:
            response = result['response']
            row.update({
                'total_faces': response.get('total_faces', 0),
                'message': response.get('message', ''),
                'api_success': response.get('success', False)
            })
            
            matches = response.get('matches', [])
            
            if matches:
                # 如果启用了优先保留已知人员，重新排序matches
                if self.prioritize_known:
                    # 将已知人员排在前面，未知人员排在后面
                    known_matches = [m for m in matches if m.get('name') != '未知人员' and m.get('person_id', -1) != -1]
                    unknown_matches = [m for m in matches if m.get('name') == '未知人员' or m.get('person_id', -1) == -1]
                    # 重新排序：已知人员在前，未知人员在后
                    matches = known_matches + unknown_matches
                
                # 为每个匹配的人脸创建列（最多记录5个）
                for i, match in enumerate(matches[:5], 1):
                    row.update({
                        f'face_{i}_person_id': match.get('person_id'),
                        f'face_{i}_name': match.get('name'),
                        f'face_{i}_match_score': match.get('match_score'),
                        f'face_{i}_distance': match.get('distance'),
                        f'face_{i}_model': match.get('model'),
                        f'face_{i}_quality': match.get('quality'),
                        f'face_{i}_age': match.get('age'),
                        f'face_{i}_gender': match.get('gender'),
                        f'face_{i}_emotion': match.get('emotion'),
                        f'face_{i}_bbox': str(match.get('bbox', [])) if match.get('bbox') else None
                    })
                
                # 填充剩余的列为空值
                for i in range(len(matches) + 1, 6):
                    for field in ['person_id', 'name', 'match_score', 'distance', 'model', 
                                 'quality', 'age', 'gender', 'emotion', 'bbox']:
                        row[f'face_{i}_{field}'] = None
            else:
                # 如果没有匹配，填充所有人脸列的空值
                for i in range(1, 6):
                    for field in ['person_id', 'name', 'match_score', 'distance', 'model', 
                                 'quality', 'age', 'gender', 'emotion', 'bbox']:
                        row[f'face_{i}_{field}'] = None
        else:
            # 失败情况的默认值
            for field in ['total_faces', 'message', 'api_success']:
                row[field] = None
            for i in range(1, 6):
                for field in ['person_id', 'name', 'match_score', 'distance', 'model', 
                             'quality', 'age', 'gender', 'emotion', 'bbox']:
                    row[f'face_{i}_{field}'] = None
        
        return row
    
    def get_csv_headers(self) -> List[str]:
        """获取CSV文件的列头"""
        headers = [
            'file_path', 'file_name', 'success', 'error',
            'total_faces', 'message', 'api_success'
        ]
        
        # 为最多5个人脸添加列头
        for i in range(1, 6):
            headers.extend([
                f'face_{i}_person_id',
                f'face_{i}_name',
                f'face_{i}_match_score',
                f'face_{i}_distance',
                f'face_{i}_model',
                f'face_{i}_quality',
                f'face_{i}_age',
                f'face_{i}_gender',
                f'face_{i}_emotion',
                f'face_{i}_bbox'
            ])
        
        return headers
    
    async def batch_recognize(self, folder_path: str, output_file: str = "recognition_results.csv",
                            progress_file: str = "progress.txt", resume: bool = True) -> str:
        """批量识别文件夹中的图片"""
        
        # 获取所有图片文件
        image_files = self.get_image_files(folder_path)
        if not image_files:
            raise ValueError(f"在文件夹 {folder_path} 中没有找到支持的图片文件")
        
        # 加载已处理的文件（断点续传）
        processed_files = set()
        if resume:
            processed_files = self.load_progress(progress_file)
        
        # 筛选未处理的文件
        remaining_files = [f for f in image_files if str(f) not in processed_files]
        
        if not remaining_files:
            logger.info("所有文件都已处理完成")
            return output_file
        
        logger.info(f"需要处理 {len(remaining_files)} 个文件 (总共 {len(image_files)} 个)")
        
        # 检查输出文件是否存在，如果不存在则创建并写入表头
        write_header = not os.path.exists(output_file) or not resume
        
        # 创建任务列表
        tasks = [self.recognize_single_image(image_path) for image_path in remaining_files]
        
        # 使用进度条并发执行
        results = []
        with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.get_csv_headers())
            
            if write_header:
                writer.writeheader()
            
            # 批量处理，显示进度条
            pbar = tqdm(total=len(tasks), desc="识别进度")
            
            for coro in asyncio.as_completed(tasks):
                result_data = await coro
                pbar.update(1)
                
                # 扁平化结果并写入CSV
                row = self.flatten_recognition_result(result_data)
                
                # 扁平化结果并写入CSV
                row = self.flatten_recognition_result(result_data)
                writer.writerow(row)
                
                # 保存进度
                self.save_progress(progress_file, result_data['file_path'])
                
                # 日志记录
                if result_data['success']:
                    if result_data['response'] and result_data['response'].get('matches'):
                        matches = result_data['response']['matches']
                        # 统计已知和未知人员
                        known_names = [m.get('name') for m in matches if m.get('name') != '未知人员' and m.get('person_id', -1) != -1]
                        unknown_count = len([m for m in matches if m.get('name') == '未知人员' or m.get('person_id', -1) == -1])
                        
                        if known_names:
                            if unknown_count > 0:
                                logger.info(f"[SUCCESS] {result_data['file_name']}: 识别到已知人员 {known_names} + {unknown_count}个未知人员")
                            else:
                                logger.info(f"[SUCCESS] {result_data['file_name']}: 识别到已知人员 {known_names}")
                        else:
                            logger.info(f"[SUCCESS] {result_data['file_name']}: 只有 {unknown_count}个未知人员")
                    else:
                        logger.info(f"[SUCCESS] {result_data['file_name']}: 无匹配")
                else:
                    logger.error(f"[FAILED] {result_data['file_name']}: {result_data['error']}")
                
                results.append(result_data)
                
                # 强制刷新文件
                csvfile.flush()
            
            pbar.close()
        
        # 统计结果
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        logger.info(f"批量识别完成！成功: {successful}, 失败: {failed}")
        logger.info(f"结果已保存到: {output_file}")
        
        return output_file

def main():
    parser = argparse.ArgumentParser(description="批量人脸识别工具")
    parser.add_argument("folder_path", help="包含图片的文件夹路径")
    parser.add_argument("--api-url", default="https://chatchat.hupu.io/api/recognize",
                        help="人脸识别API地址")
    parser.add_argument("--max-concurrent", type=int, default=5,
                        help="最大并发数 (默认: 5)")
    parser.add_argument("--output", default="recognition_results.csv",
                        help="输出CSV文件名 (默认: recognition_results.csv)")
    parser.add_argument("--progress-file", default="progress.txt",
                        help="进度文件名 (默认: progress.txt)")
    parser.add_argument("--no-resume", action="store_true",
                        help="不使用断点续传，重新开始")
    parser.add_argument("--disable-ssl-verify", action="store_true",
                        help="禁用SSL证书验证（仅在SSL错误时使用）")
    parser.add_argument("--prioritize-known", action="store_false",
                        help="优先保留已知人员结果（将已知人员排在前5位，避免漏掉已知人员）")
    
    args = parser.parse_args()
    
    async def run_batch_recognition():
        async with BatchFaceRecognition(
            api_url=args.api_url,
            max_concurrent=args.max_concurrent,
            disable_ssl_verify=args.disable_ssl_verify,
            prioritize_known=args.prioritize_known
        ) as recognizer:
            try:
                result_file = await recognizer.batch_recognize(
                    folder_path=args.folder_path,
                    output_file=args.output,
                    progress_file=args.progress_file,
                    resume=not args.no_resume
                )
                print(f"\n批量识别完成！结果保存在: {result_file}")
                
                # 显示简单统计
                try:
                    df = pd.read_csv(result_file)
                    total = len(df)
                    successful = df['success'].sum()
                    with_matches = df['face_1_name'].notna().sum()
                    
                    print(f"\n=== 统计结果 ===")
                    print(f"总文件数: {total}")
                    print(f"成功处理: {successful}")
                    print(f"识别到人脸: {with_matches}")
                    print(f"识别率: {with_matches/total*100:.1f}%")
                    
                except Exception as e:
                    logger.warning(f"无法显示统计信息: {e}")
                    
            except Exception as e:
                logger.error(f"批量识别失败: {e}")
                return 1
        
        return 0
    
    # 运行异步主函数
    exit_code = asyncio.run(run_batch_recognition())
    exit(exit_code)

if __name__ == "__main__":
    main()

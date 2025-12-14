#!/usr/bin/env python3
"""
Batch face recognition script
Support concurrent processing、progress bar display、Breakpoint resume function
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

# Setup log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_recognition.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set environment variables to avoidWindowsEncoding issues
import os
if os.name == 'nt':  # Windowssystem
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
        
        # Supported image formats
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.avif'}
        
    async def __aenter__(self):
        """Asynchronous context manager entry"""
        connector = None
        
        if self.disable_ssl_verify:
            # createSSLcontext，DisableSSLverify（Suitable for certain network environments）
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            logger.warning("SSLAuthentication is disabled，Use only when necessary")
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60, connect=10),
            connector=connector
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def get_image_files(self, folder_path: str) -> List[Path]:
        """Get all image files in a folder"""
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Folder does not exist: {folder_path}")
        
        image_files = []
        for file_path in folder.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                image_files.append(file_path)
        
        logger.info(f"turn up {len(image_files)} image files")
        return sorted(image_files)
    
    def load_progress(self, progress_file: str) -> set:
        """Load a list of processed files（Resume upload from breakpoint）"""
        if not os.path.exists(progress_file):
            return set()
        
        processed_files = set()
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                for line in f:
                    processed_files.add(line.strip())
            logger.info(f"Load processed files {len(processed_files)} indivual")
        except Exception as e:
            logger.warning(f"Failed to load progress file: {e}")
        
        return processed_files
    
    def save_progress(self, progress_file: str, file_path: str):
        """Save processing progress"""
        with open(progress_file, 'a', encoding='utf-8') as f:
            f.write(f"{file_path}\n")
    
    async def recognize_single_image(self, image_path: Path) -> Dict[str, Any]:
        """Recognize a single image"""
        async with self.semaphore:
            try:
                # determined fileMIMEtype
                mime_type, _ = mimetypes.guess_type(str(image_path))
                if not mime_type or not mime_type.startswith('image/'):
                    mime_type = 'image/jpeg'  # Default type
                
                # Read image files
                async with aiofiles.open(image_path, 'rb') as f:
                    file_content = await f.read()
                
                # Build form data
                data = aiohttp.FormData()
                data.add_field(
                    'file',
                    file_content,
                    filename=image_path.name,
                    content_type=mime_type
                )
                
                # Send request
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
                # SSLSpecial handling of errors
                return {
                    'file_path': str(image_path),
                    'file_name': image_path.name,
                    'success': False,
                    'response': None,
                    'error': f"SSLmistake: {str(e)} (You can try using --disable-ssl-verify Options)"
                }
            except asyncio.TimeoutError:
                return {
                    'file_path': str(image_path),
                    'file_name': image_path.name,
                    'success': False,
                    'response': None,
                    'error': "Request timeout"
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
        """Flatten the recognition results intoCSVrow data"""
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
                # If Prioritize Retention of Known People is enabled，Reordermatches
                if self.prioritize_known:
                    # Put known people first，Unknown person is next in line
                    known_matches = [m for m in matches if m.get('name') != 'unknown person' and m.get('person_id', -1) != -1]
                    unknown_matches = [m for m in matches if m.get('name') == 'unknown person' or m.get('person_id', -1) == -1]
                    # Reorder：Known people first，Unknown person behind
                    matches = known_matches + unknown_matches
                
                # Create columns for each matching face（Most records5indivual）
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
                
                # Fill remaining columns with null values
                for i in range(len(matches) + 1, 6):
                    for field in ['person_id', 'name', 'match_score', 'distance', 'model', 
                                 'quality', 'age', 'gender', 'emotion', 'bbox']:
                        row[f'face_{i}_{field}'] = None
            else:
                # if no match，Fill all empty values ​​of face column
                for i in range(1, 6):
                    for field in ['person_id', 'name', 'match_score', 'distance', 'model', 
                                 'quality', 'age', 'gender', 'emotion', 'bbox']:
                        row[f'face_{i}_{field}'] = None
        else:
            # Default value for failure cases
            for field in ['total_faces', 'message', 'api_success']:
                row[field] = None
            for i in range(1, 6):
                for field in ['person_id', 'name', 'match_score', 'distance', 'model', 
                             'quality', 'age', 'gender', 'emotion', 'bbox']:
                    row[f'face_{i}_{field}'] = None
        
        return row
    
    def get_csv_headers(self) -> List[str]:
        """GetCSVfile column header"""
        headers = [
            'file_path', 'file_name', 'success', 'error',
            'total_faces', 'message', 'api_success'
        ]
        
        # for the most5Add column headers for personal faces
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
        """Recognize pictures in folders in batches"""
        
        # Get all image files
        image_files = self.get_image_files(folder_path)
        if not image_files:
            raise ValueError(f"in folder {folder_path} No supported image file found in")
        
        # Load processed files（Resume upload from breakpoint）
        processed_files = set()
        if resume:
            processed_files = self.load_progress(progress_file)
        
        # Filter unprocessed files
        remaining_files = [f for f in image_files if str(f) not in processed_files]
        
        if not remaining_files:
            logger.info("All files have been processed")
            return output_file
        
        logger.info(f"Need to be processed {len(remaining_files)} files (total {len(image_files)} indivual)")
        
        # Check if the output file exists，If it does not exist, create and write the header
        write_header = not os.path.exists(output_file) or not resume
        
        # Create task list
        tasks = [self.recognize_single_image(image_path) for image_path in remaining_files]
        
        # Concurrent execution using progress bar
        results = []
        with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.get_csv_headers())
            
            if write_header:
                writer.writeheader()
            
            # Batch processing，Show progress bar
            pbar = tqdm(total=len(tasks), desc="Identify progress")
            
            for coro in asyncio.as_completed(tasks):
                result_data = await coro
                pbar.update(1)
                
                # Flatten the results and writeCSV
                row = self.flatten_recognition_result(result_data)
                
                # Flatten the results and writeCSV
                row = self.flatten_recognition_result(result_data)
                writer.writerow(row)
                
                # save progress
                self.save_progress(progress_file, result_data['file_path'])
                
                # logging
                if result_data['success']:
                    if result_data['response'] and result_data['response'].get('matches'):
                        matches = result_data['response']['matches']
                        # Count known and unknown people
                        known_names = [m.get('name') for m in matches if m.get('name') != 'unknown person' and m.get('person_id', -1) != -1]
                        unknown_count = len([m for m in matches if m.get('name') == 'unknown person' or m.get('person_id', -1) == -1])
                        
                        if known_names:
                            if unknown_count > 0:
                                logger.info(f"[SUCCESS] {result_data['file_name']}: Known person identified {known_names} + {unknown_count}unknown person")
                            else:
                                logger.info(f"[SUCCESS] {result_data['file_name']}: Known person identified {known_names}")
                        else:
                            logger.info(f"[SUCCESS] {result_data['file_name']}: only {unknown_count}unknown person")
                    else:
                        logger.info(f"[SUCCESS] {result_data['file_name']}: No match")
                else:
                    logger.error(f"[FAILED] {result_data['file_name']}: {result_data['error']}")
                
                results.append(result_data)
                
                # Force refresh file
                csvfile.flush()
            
            pbar.close()
        
        # Statistical results
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        logger.info(f"Batch identification completed！success: {successful}, fail: {failed}")
        logger.info(f"Results have been saved to: {output_file}")
        
        return output_file

def main():
    parser = argparse.ArgumentParser(description="Batch face recognition tool")
    parser.add_argument("folder_path", help="Path to folder containing images")
    parser.add_argument("--api-url", default="https://chatchat.hupu.io/api/recognize",
                        help="face recognitionAPIaddress")
    parser.add_argument("--max-concurrent", type=int, default=5,
                        help="Maximum number of concurrencies (default: 5)")
    parser.add_argument("--output", default="recognition_results.csv",
                        help="outputCSVfile name (default: recognition_results.csv)")
    parser.add_argument("--progress-file", default="progress.txt",
                        help="Progress file name (default: progress.txt)")
    parser.add_argument("--no-resume", action="store_true",
                        help="Resume download without using breakpoint，restart")
    parser.add_argument("--disable-ssl-verify", action="store_true",
                        help="DisableSSLCertificate verification（only inSSLUse on error）")
    parser.add_argument("--prioritize-known", action="store_false",
                        help="Prioritize retention of known person results（Put known people first5Bit，Avoid missing known people）")
    
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
                print(f"\nBatch identification completed！The results are saved in: {result_file}")
                
                # Show simple statistics
                try:
                    df = pd.read_csv(result_file)
                    total = len(df)
                    successful = df['success'].sum()
                    with_matches = df['face_1_name'].notna().sum()
                    
                    print(f"\n=== Statistical results ===")
                    print(f"Total number of files: {total}")
                    print(f"successfully processed: {successful}")
                    print(f"Face recognized: {with_matches}")
                    print(f"Recognition rate: {with_matches/total*100:.1f}%")
                    
                except Exception as e:
                    logger.warning(f"Unable to display statistics: {e}")
                    
            except Exception as e:
                logger.error(f"Batch recognition failed: {e}")
                return 1
        
        return 0
    
    # Run the asynchronous main function
    exit_code = asyncio.run(run_batch_recognition())
    exit(exit_code)

if __name__ == "__main__":
    main()

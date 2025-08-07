#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面诊断前端图片显示问题
"""
import requests
import sqlite3
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def comprehensive_image_diagnosis():
    """全面诊断图片显示问题"""
    print("🔍 === 前端图片显示问题全面诊断 ===")
    
    # 第1步：检查数据库中的图片数据
    print("\n1️⃣ 检查数据库中的图片存储...")
    try:
        conn = sqlite3.connect("data/database/face_recognition.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.id, p.name, fe.id as face_id, fe.image_path, 
                   length(fe.image_data) as image_size,
                   CASE WHEN fe.image_data IS NOT NULL THEN 'YES' ELSE 'NO' END as has_image_data
            FROM persons p 
            JOIN face_encodings fe ON p.id = fe.person_id 
            ORDER BY p.id
        """)
        
        records = cursor.fetchall()
        print("💾 数据库图片数据:")
        
        for record in records:
            person_id, person_name, face_id, image_path, image_size, has_image_data = record
            print(f"  👤 {person_name} (人员ID: {person_id})")
            print(f"      🆔 人脸ID: {face_id}")
            print(f"      📁 原始文件名: {image_path}")
            print(f"      💿 图片数据: {has_image_data} ({image_size:,} bytes)")
            print(f"      🔗 预期API URL: /api/face/{face_id}/image")
            print()
        
        conn.close()
        
        if not records:
            print("❌ 数据库中没有找到任何人员和图片数据!")
            return
            
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return
    
    # 第2步：测试API返回的人员列表
    print("2️⃣ 测试人员列表API...")
    try:
        response = requests.get(f"{BASE_URL}/api/persons", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 人员列表API正常")
            print(f"📊 返回 {data['total']} 个人员")
            
            for person in data['persons']:
                print(f"  👤 {person['name']} (ID: {person['id']})")
                print(f"      🖼️ 头像URL: {person.get('face_image_url', 'None')}")
                print(f"      📊 人脸数量: {person.get('face_count', 0)}")
                
                # 测试头像URL
                if person.get('face_image_url'):
                    try:
                        img_response = requests.head(f"{BASE_URL}{person['face_image_url']}", timeout=5)
                        if img_response.status_code == 200:
                            print(f"      ✅ 头像图片可访问 ({img_response.headers.get('content-length', '未知')} bytes)")
                        else:
                            print(f"      ❌ 头像图片访问失败: HTTP {img_response.status_code}")
                    except Exception as img_error:
                        print(f"      ❌ 头像图片请求异常: {img_error}")
                print()
        else:
            print(f"❌ 人员列表API失败: HTTP {response.status_code}")
            print(response.text)
            return
            
    except Exception as e:
        print(f"❌ 人员列表API异常: {e}")
        return
    
    # 第3步：测试人员详情API
    print("3️⃣ 测试人员详情API...")
    if records:
        test_person_id = records[0][0]  # 使用第一个人员ID
        try:
            response = requests.get(f"{BASE_URL}/api/person/{test_person_id}/faces", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 人员详情API正常 (人员ID: {test_person_id})")
                print(f"📊 返回 {data.get('total_faces', 0)} 张人脸")
                
                if data.get('face_encodings'):
                    for i, face in enumerate(data['face_encodings'], 1):
                        print(f"  🖼️ 人脸 {i}:")
                        print(f"      🆔 编码ID: {face.get('id')}")
                        print(f"      📁 图片路径: {face.get('image_path')}")
                        print(f"      💿 有图片数据: {face.get('has_image_data', False)}")
                        print(f"      📊 质量评分: {face.get('quality_score', 0):.3f}")
                        
                        # 测试图片URL
                        if face.get('id'):
                            img_url = f"/api/face/{face['id']}/image"
                            try:
                                img_response = requests.head(f"{BASE_URL}{img_url}", timeout=5)
                                if img_response.status_code == 200:
                                    print(f"      ✅ 图片可访问: {img_url}")
                                else:
                                    print(f"      ❌ 图片访问失败: {img_url} (HTTP {img_response.status_code})")
                            except Exception as img_error:
                                print(f"      ❌ 图片请求异常: {img_error}")
                        print()
            else:
                print(f"❌ 人员详情API失败: HTTP {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ 人员详情API异常: {e}")
    
    # 第4步：检查前端HTML结构
    print("4️⃣ 生成前端调试建议...")
    print("🔧 前端调试步骤:")
    print("  1. 打开浏览器开发者工具 (F12)")
    print("  2. 导航到人员管理页面")
    print("  3. 查看Console是否有JavaScript错误")
    print("  4. 查看Network标签页，检查图片请求:")
    for record in records[:3]:  # 只显示前3个
        person_id, person_name, face_id, _, _, _ = record
        print(f"     - 应该看到请求: /api/face/{face_id}/image")
    print("  5. 如果图片显示为❌或占位符，右键检查元素查看img标签")
    
    print("\n🎯 常见问题排查:")
    print("  • 如果头像显示默认图标，但API数据正常 → 前端JavaScript可能有错误")
    print("  • 如果图片请求返回404 → 检查face_id是否正确")
    print("  • 如果图片请求返回500 → 检查后端get_face_image API")
    print("  • 如果图片加载慢 → 正常现象，数据库BLOB转换需要时间")
    
    print("\n✅ 诊断完成!")

if __name__ == "__main__":
    comprehensive_image_diagnosis()

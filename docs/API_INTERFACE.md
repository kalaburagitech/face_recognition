# 人脸识别系统 API 接口文档

## 人脸识别接口

### 1. 人脸识别接口

**接口地址:** `POST /api/recognize`

**功能描述:** 上传图像进行人脸识别，返回匹配的人员信息和具体的人脸特征ID

**请求参数:**
- `file` (必需): 待识别的图像文件

**响应示例:**
```json
{
    "success": true,
    "matches": [
        {
            "person_id": 123,
            "face_encoding_id": 456,
            "name": "张三",
            "match_score": 95.5,
            "distance": 0.045,
            "model": "InsightFace_buffalo_l",
            "bbox": [100, 150, 200, 250],
            "quality": 0.92
        }
    ],
    "total_faces": 1,
    "message": "识别完成，检测到 1 个人脸，识别出 1 个已知人员"
}
```

**重要更新:** 现在识别接口会返回 `face_encoding_id` 字段，表示匹配的具体人脸特征ID，可用于后续的人脸管理操作。

## 人脸入库接口

### 1. 标准入库接口

**接口地址:** `POST /api/enroll`

**功能描述:** 上传人脸图像进行人员注册入库，返回完整的入库信息包括可视化图像

**请求参数:**
- `file` (必需): 人脸图像文件
- `name` (必需): 人员姓名
- `description` (可选): 人员描述

**响应示例:**
```json
{
    "success": true,
    "person_id": 123,
    "face_encoding_id": 456,
    "person_name": "张三",
    "description": "员工",
    "faces_detected": 1,
    "face_quality": 0.85,
    "processing_time": 1.23,
    "feature_dim": 512,
    "embeddings_count": 1,
    "visualized_image": "base64编码的图像数据...",
    "face_details": [...]
}
```

### 2. 简化入库接口 (新增)

**接口地址:** `POST /api/enroll_simple`

**功能描述:** 上传人脸图像进行人员注册入库，不返回图片数据，节省带宽

**请求参数:**
- `file` (必需): 人脸图像文件
- `name` (必需): 人员姓名
- `description` (可选): 人员描述

**响应示例:**
```json
{
    "success": true,
    "person_id": 123,
    "face_encoding_id": 456,
    "person_name": "张三",
    "description": "员工",
    "faces_detected": 1,
    "face_quality": 0.85,
    "processing_time": 1.23,
    "feature_dim": 512,
    "embeddings_count": 1,
    "visualized_image": null,
    "face_details": null
}
```

### 3. 批量入库接口 (已优化)

**接口地址:** `POST /api/batch_enroll`

**功能描述:** 批量上传人脸图像进行人员注册入库

**请求参数:**
- `files` (必需): 人脸图像文件列表
- `names` (可选): 人员姓名列表
- `descriptions` (可选): 人员描述列表
- `sort_by_filename` (可选): 是否按文件名排序，默认为true

**响应示例:**
```json
{
    "success": true,
    "total_files": 2,
    "success_count": 2,
    "error_count": 0,
    "results": [
        {
            "file_name": "person1.jpg",
            "name": "张三",
            "person_id": 123,
            "face_encoding_id": 456,
            "success": true,
            "quality_score": 0.85
        },
        {
            "file_name": "person2.jpg",
            "name": "李四",
            "person_id": 124,
            "face_encoding_id": 457,
            "success": true,
            "quality_score": 0.92
        }
    ],
    "message": "批量入库完成：成功 2 个，失败 0 个"
}
```

## 人脸删除接口

### 1. 通过人脸ID删除

**接口地址:** `DELETE /api/face_encoding/{encoding_id}`

**功能描述:** 删除指定的人脸特征向量，支持同一人员多张人脸的单独删除

**路径参数:**
- `encoding_id`: 人脸编码ID (从入库接口返回的 face_encoding_id)

**响应示例:**
```json
{
    "success": true,
    "message": "人脸编码删除成功"
}
```

### 2. 通过人员ID和人脸ID删除

**接口地址:** `DELETE /api/person/{person_id}/faces/{face_encoding_id}`

**功能描述:** 删除指定人员的某张人脸照片

**路径参数:**
- `person_id`: 人员ID
- `face_encoding_id`: 人脸编码ID

**响应示例:**
```json
{
    "success": true,
    "message": "已删除 张三 的人脸照片"
}
```

## 为人员添加更多人脸接口 (已优化)

**接口地址:** `POST /api/person/{person_id}/faces`

**功能描述:** 为已存在的人员添加多张人脸照片

**路径参数:**
- `person_id`: 人员ID

**请求参数:**
- `faces`: 人脸图像文件列表

**响应示例:**
```json
{
    "success": true,
    "person_id": 123,
    "person_name": "张三",
    "total_files": 2,
    "success_count": 2,
    "error_count": 0,
    "count": 2,
    "results": [
        {
            "file_name": "face1.jpg",
            "success": true,
            "face_encoding_id": 458,
            "quality_score": 0.88
        },
        {
            "file_name": "face2.jpg",
            "success": true,
            "face_encoding_id": 459,
            "quality_score": 0.91
        }
    ],
    "message": "为 张三 添加人脸完成：成功 2 个，失败 0 个"
}
```

## 使用示例

### Python 示例

```python
import requests

# 入库示例
def enroll_person():
    url = "http://localhost:8000/api/enroll_simple"
    
    with open("person.jpg", "rb") as f:
        files = {"file": f}
        data = {
            "name": "张三",
            "description": "员工"
        }
        response = requests.post(url, files=files, data=data)
    
    result = response.json()
    if result["success"]:
        print(f"入库成功！人员ID: {result['person_id']}, 人脸ID: {result['face_encoding_id']}")
        return result["face_encoding_id"]
    else:
        print(f"入库失败: {result['error']}")
        return None

# 删除示例
def delete_face(face_encoding_id):
    url = f"http://localhost:8000/api/face_encoding/{face_encoding_id}"
    response = requests.delete(url)
    
    result = response.json()
    if result["success"]:
        print("删除成功！")
    else:
        print(f"删除失败: {result.get('detail', '未知错误')}")

# 使用示例
face_encoding_id = enroll_person()
if face_encoding_id:
    delete_face(face_encoding_id)
```

### cURL 示例

```bash
# 简化入库
curl -X POST "http://localhost:8000/api/enroll_simple" \
     -F "file=@person.jpg" \
     -F "name=张三" \
     -F "description=员工"

# 删除人脸
curl -X DELETE "http://localhost:8000/api/face_encoding/456"
```

## 主要变更说明

1. **新增 face_encoding_id 返回字段**: 所有入库相关接口现在都返回人脸特征ID
2. **新增简化入库接口**: `/api/enroll_simple` 不返回图片数据，适合带宽敏感的应用
3. **优化批量入库**: 现在返回每个文件对应的人脸ID
4. **优化人员添加人脸**: 返回字段名统一为 `face_encoding_id`
5. **完善删除接口**: 提供两种删除方式，支持灵活的人脸管理

## 错误码说明

- 200: 成功
- 400: 请求参数错误（文件类型不支持、文件太大等）
- 404: 资源不存在（人员不存在、人脸不存在等）
- 500: 服务器内部错误

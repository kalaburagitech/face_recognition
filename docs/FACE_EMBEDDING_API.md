# 人脸特征向量提取接口

## 概述

新增的`/api/extract_embeddings`接口专门用于提取人脸特征向量，不进行身份识别，适合外部系统进行相似度计算或其他机器学习任务。

## API接口

### POST /api/extract_embeddings

提取图像中所有人脸的特征向量。

#### 请求参数

- `file`: 图像文件 (multipart/form-data)

#### 响应格式

```json
{
  "success": true,
  "faces": [
    {
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.95,
      "quality": 0.95,
      "embedding": [512维浮点数数组]
    }
  ],
  "total_faces": 1,
  "processing_time": 0.45,
  "model_info": "InsightFace-buffalo_l",
  "image_size": [width, height]
}
```

#### 响应字段说明

- `success`: 处理是否成功
- `faces`: 检测到的人脸列表
  - `bbox`: 人脸边界框坐标 [x1, y1, x2, y2]
  - `confidence`: 人脸检测置信度 (0-1)
  - `quality`: 人脸质量分数 (0-1)
  - `embedding`: 512维特征向量
- `total_faces`: 检测到的人脸数量
- `processing_time`: 处理耗时（秒）
- `model_info`: 使用的AI模型信息
- `image_size`: 输入图像尺寸 [宽度, 高度]

## 使用示例

### cURL示例

```bash
curl -X POST "http://localhost:8000/api/extract_embeddings" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/face.jpg"
```

### Python示例

```python
import requests

url = "http://localhost:8000/api/extract_embeddings"
files = {"file": open("face.jpg", "rb")}

response = requests.post(url, files=files)
result = response.json()

if result["success"] and result["faces"]:
    face = result["faces"][0]
    print(f"检测到人脸，置信度: {face['confidence']}")
    print(f"特征向量维度: {len(face['embedding'])}")
    print(f"边界框: {face['bbox']}")
else:
    print("未检测到人脸或处理失败")
```

## 特性

1. **专用功能**: 只进行人脸检测和特征提取，不进行身份识别
2. **高精度**: 使用InsightFace Buffalo_l模型，提供512维特征向量
3. **多人脸支持**: 可以处理包含多个人脸的图像
4. **标准化输出**: 返回标准化的特征向量，便于相似度计算
5. **完整信息**: 返回人脸位置、质量评估等详细信息

## 应用场景

- **相似度计算**: 比较两个人脸的相似度
- **人脸聚类**: 将相似的人脸分组
- **特征存储**: 将特征向量存储到向量数据库
- **机器学习**: 作为下游任务的特征输入
- **人脸搜索**: 在大量人脸中搜索相似人脸

## 注意事项

1. 支持常见图像格式 (JPG, PNG等)
2. 文件大小限制：默认10MB
3. 对于低质量图像，可能影响特征提取准确性
4. 特征向量已经过标准化处理，可直接用于余弦相似度计算

## 错误处理

当处理失败时，响应格式为：

```json
{
  "success": false,
  "error": "错误描述",
  "faces": null,
  "total_faces": 0
}
```

常见错误：
- 文件格式不支持
- 文件过大
- 图像质量过低
- 未检测到人脸（这种情况下`success`为`true`，但`faces`为空数组）

# Face Recognition System - API Documentation

This document provides a comprehensive overview of all API endpoints in the Face Recognition System. The system is built with FastAPI and uses PostgreSQL with pgvector for efficient face recognition.

---

## Table of Contents

1. [Web Pages](#web-pages)
2. [Person Enrollment](#person-enrollment)
3. [Face Recognition](#face-recognition)
4. [Person Management](#person-management)
5. [Face Management](#face-management)
6. [Attendance Management](#attendance-management)
7. [Configuration](#configuration)
8. [Statistics & Monitoring](#statistics--monitoring)
9. [Health Checks](#health-checks)

---

## Web Pages

### GET `/`
**Purpose:** Serve the main web interface (home page)  
**Returns:** HTML page  
**Usage:** Access the web UI in browser

### GET `/{file_path}.html`
**Purpose:** Serve specific HTML pages (recognition.html, enrollment.html, etc.)  
**Parameters:**
- `file_path`: Name of the HTML file without extension
**Returns:** HTML page

---

## Person Enrollment

### POST `/api/enroll`
**Purpose:** Register a new person with face image (with visualization)  
**Parameters:**
- `file`: Face image file (multipart/form-data)
- `name`: Person's name
- `region`: Region code (ka/ap/tn)
- `emp_id`: Employee ID (unique)
- `emp_rank`: Employee rank/position
- `description`: Optional description

**Returns:**
```json
{
  "success": true,
  "person_id": 123,
  "face_encoding_id": 456,
  "person_name": "John Doe",
  "faces_detected": 1,
  "face_quality": 0.95,
  "processing_time": 0.234,
  "feature_dim": 512,
  "visualized_image": "base64_encoded_image",
  "face_details": [...]
}
```

**Features:**
- Detects duplicate faces (prevents same face with different names)
- Returns visualization of detected face
- Quality score validation
- Duplicate threshold: 60% similarity

### POST `/api/enroll_simple`
**Purpose:** Register a new person (simplified, no visualization)  
**Parameters:** Same as `/api/enroll`  
**Returns:** Same structure but without `visualized_image` and `face_details`  
**Usage:** Faster enrollment when visualization is not needed

### POST `/api/batch_enroll`
**Purpose:** Register multiple persons at once  
**Parameters:**
- `files`: List of face image files
- `names`: Optional list of names (or extracted from filenames)
- `region`: Region code
- `emp_id`: Employee ID
- `emp_rank`: Employee rank
- `descriptions`: Optional list of descriptions
- `sort_by_filename`: Sort files by name (default: true)

**Returns:**
```json
{
  "success": true,
  "total_files": 10,
  "success_count": 9,
  "error_count": 1,
  "results": [...]
}
```

**Features:**
- Supports video frame registration
- Pre-checks for duplicates before processing
- Processes files in sorted order

### POST `/api/extract_embeddings`
**Purpose:** Extract face feature vectors without enrollment  
**Parameters:**
- `file`: Face image file

**Returns:**
```json
{
  "success": true,
  "faces": [
    {
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.99,
      "quality": 0.95,
      "embedding": [512-dimensional vector]
    }
  ],
  "total_faces": 1,
  "processing_time": 0.123,
  "model_info": "buffalo_l",
  "image_size": [width, height]
}
```

**Usage:** For external systems to get face embeddings for custom processing

---

## Face Recognition

### POST `/api/recognize`
**Purpose:** Recognize faces in an image  
**Parameters:**
- `file`: Image file to recognize
- `region`: Region to search in (ka/ap/tn)

**Returns:**
```json
{
  "success": true,
  "matches": [
    {
      "person_id": 123,
      "name": "John Doe",
      "match_score": 95.5,
      "distance": 0.045,
      "model": "InsightFace",
      "bbox": [x1, y1, x2, y2],
      "quality": 0.95,
      "face_encoding_id": 456,
      "age": 30,
      "gender": "male"
    }
  ],
  "total_faces": 1,
  "message": "Recognition completed"
}
```

**Features:**
- Region-based filtering
- Uses pgvector for fast similarity search
- Returns top matches above threshold (default: 35%)

### POST `/api/recognize_visual`
**Purpose:** Recognize faces with visualization (annotated image)  
**Parameters:** Same as `/api/recognize`  
**Returns:** Image file with bounding boxes and labels  
**Usage:** For displaying recognition results visually

### POST `/api/analyze`
**Purpose:** Analyze face attributes (age, gender, emotion, race)  
**Parameters:**
- `file`: Image file to analyze

**Returns:**
```json
{
  "success": true,
  "faces": [
    {
      "bbox": [x1, y1, x2, y2],
      "age": 30,
      "gender": "male",
      "gender_confidence": 0.98,
      "emotion": "happy",
      "emotion_scores": {...},
      "race": "asian",
      "race_scores": {...}
    }
  ],
  "total_faces": 1
}
```

### POST `/api/detect_faces`
**Purpose:** Detect faces in an image without recognition  
**Parameters:**
- `file`: Image file

**Returns:**
```json
{
  "success": true,
  "faces": [
    {
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.99,
      "landmarks": [[x, y], ...],
      "quality": 0.95
    }
  ],
  "total_faces": 1,
  "image_size": [width, height]
}
```

---

## Person Management

### GET `/api/persons`
**Purpose:** Get list of all registered persons  
**Parameters:**
- `include_image_info`: Include face image details (default: false)

**Returns:**
```json
{
  "success": true,
  "total": 100,
  "persons": [
    {
      "id": 123,
      "name": "John Doe",
      "region": "ka",
      "emp_id": "EMP001",
      "emp_rank": "Manager",
      "description": "...",
      "face_count": 5,
      "created_at": "2025-12-13T10:00:00",
      "updated_at": "2025-12-13T10:00:00"
    }
  ]
}
```

### GET `/api/person/{person_id}`
**Purpose:** Get details of a specific person  
**Parameters:**
- `person_id`: Person's ID

**Returns:**
```json
{
  "success": true,
  "person": {
    "id": 123,
    "name": "John Doe",
    "region": "ka",
    "emp_id": "EMP001",
    "emp_rank": "Manager",
    "description": "...",
    "face_count": 5,
    "created_at": "2025-12-13T10:00:00"
  }
}
```

### PUT `/api/person/{person_id}`
**Purpose:** Update person information  
**Parameters:**
- `person_id`: Person's ID
- `name`: New name (optional)
- `description`: New description (optional)

**Returns:**
```json
{
  "success": true,
  "message": "Person updated successfully",
  "person": {...}
}
```

### DELETE `/api/person/{person_id}`
**Purpose:** Delete a person and all their data  
**Parameters:**
- `person_id`: Person's ID

**Returns:**
```json
{
  "success": true,
  "message": "personnel John Doe Deleted"
}
```

**Note:** This deletes:
- Person record
- All face encodings
- All attendance records

---

## Face Management

### GET `/api/person/{person_id}/faces`
**Purpose:** Get all face images of a person  
**Parameters:**
- `person_id`: Person's ID

**Returns:**
```json
{
  "success": true,
  "person_id": 123,
  "person_name": "John Doe",
  "total_faces": 5,
  "faces": [
    {
      "id": 456,
      "image_path": "image.jpg",
      "face_bbox": "[x1,y1,x2,y2]",
      "confidence": 0.99,
      "quality_score": 0.95,
      "created_at": "2025-12-13T10:00:00",
      "has_image_data": true
    }
  ]
}
```

### GET `/api/face/{face_encoding_id}/image`
**Purpose:** Get the actual face image  
**Parameters:**
- `face_encoding_id`: Face encoding ID

**Returns:** Image file (JPEG)  
**Usage:** Display face images in UI

### POST `/api/person/{person_id}/faces`
**Purpose:** Add additional face images to existing person  
**Parameters:**
- `person_id`: Person's ID
- `files`: List of face image files

**Returns:**
```json
{
  "success": true,
  "person_id": 123,
  "added_count": 3,
  "failed_count": 0,
  "results": [...]
}
```

### DELETE `/api/face_encoding/{encoding_id}`
**Purpose:** Delete a specific face encoding  
**Parameters:**
- `encoding_id`: Face encoding ID

**Returns:**
```json
{
  "success": true,
  "message": "Face encoding deleted"
}
```

### DELETE `/api/person/{person_id}/faces/{face_encoding_id}`
**Purpose:** Delete a specific face of a person  
**Parameters:**
- `person_id`: Person's ID
- `face_encoding_id`: Face encoding ID

**Returns:**
```json
{
  "success": true,
  "message": "Deleted John Doe face photos"
}
```

---

## Attendance Management

### POST `/api/attendance/mark`
**Purpose:** Mark attendance for a person  
**Parameters:**
- `person_id`: Person's ID (optional)
- `emp_id`: Employee ID (optional)
- `name`: Person's name (optional)
- `date`: Date in YYYY-MM-DD format (optional, defaults to today)
- `status`: Attendance status (default: "present")

**Returns:**
```json
{
  "success": true,
  "already_marked": false,
  "message": "Attendance marked successfully",
  "person": {
    "id": 123,
    "name": "John Doe",
    "emp_id": "EMP001",
    "emp_rank": "Manager"
  },
  "attendance": {
    "id": 1,
    "status": "present",
    "marked_at": "2025-12-13T10:00:00",
    "date": "2025-12-13"
  }
}
```

**Features:**
- Prevents duplicate attendance for same day
- Returns `already_marked: true` if attendance exists
- Can identify person by ID, emp_id, or name

### GET `/api/attendance/check`
**Purpose:** Check if attendance is already marked  
**Parameters:**
- `person_id`: Person's ID (optional)
- `emp_id`: Employee ID (optional)
- `name`: Person's name (optional)
- `date`: Date in YYYY-MM-DD format (optional)

**Returns:**
```json
{
  "success": true,
  "is_marked": true,
  "person": {...},
  "attendance": {...}
}
```

### GET `/api/attendance/debug/{person_id}`
**Purpose:** Debug endpoint to check attendance status  
**Parameters:**
- `person_id`: Person's ID

**Returns:**
```json
{
  "person_id": 123,
  "person_name": "John Doe",
  "today_date": "2025-12-13T00:00:00",
  "has_attendance": true,
  "attendance": {...}
}
```

### GET `/api/attendance`
**Purpose:** Get attendance records for a date  
**Parameters:**
- `date`: Date in YYYY-MM-DD format (optional, defaults to today)
- `region`: Region filter (optional)

**Returns:**
```json
{
  "success": true,
  "date": "2025-12-13",
  "region": "ka",
  "total": 100,
  "present": 85,
  "absent": 15,
  "records": [
    {
      "attendance_id": 1,
      "person_id": 123,
      "name": "John Doe",
      "emp_id": "EMP001",
      "emp_rank": "Manager",
      "region": "ka",
      "status": "present",
      "marked_at": "2025-12-13T10:00:00",
      "date": "2025-12-13"
    }
  ]
}
```

---

## Configuration

### GET `/api/config`
**Purpose:** Get current system configuration  
**Returns:**
```json
{
  "success": true,
  "config": {
    "recognition_threshold": 0.35,
    "detection_threshold": 0.4,
    "duplicate_threshold": 0.60,
    "max_file_size": 16777216,
    "supported_formats": ["jpg", "jpeg", "png", ...],
    "model": "buffalo_l",
    "database_path": "...",
    "models_root": "...",
    "cache_dir": "..."
  }
}
```

### POST `/api/config`
**Purpose:** Update system configuration  
**Parameters:**
- `recognition_threshold`: Recognition threshold (0.0-1.0)
- `detection_threshold`: Detection threshold (0.0-1.0)
- `duplicate_threshold`: Duplicate detection threshold (0.0-1.0)
- `threshold`: Alias for recognition_threshold

**Returns:**
```json
{
  "success": true,
  "message": "Configuration updated",
  "updated_config": {...}
}
```

### POST `/api/config/threshold`
**Purpose:** Update recognition threshold  
**Parameters:**
- `threshold`: New threshold value (0.0-1.0)

**Returns:**
```json
{
  "success": true,
  "message": "Threshold updated to 0.35",
  "threshold": 0.35
}
```

### POST `/api/config/duplicate_threshold`
**Purpose:** Update duplicate detection threshold  
**Parameters:**
- `threshold`: New threshold value (0.8-0.99)

**Returns:**
```json
{
  "success": true,
  "message": "Duplicate threshold updated to 0.60",
  "threshold": 0.60
}
```

---

## Statistics & Monitoring

### GET `/api/statistics`
**Purpose:** Get system statistics  
**Returns:**
```json
{
  "success": true,
  "statistics": {
    "total_persons": 100,
    "total_encodings": 500,
    "avg_photos_per_person": 5.0,
    "region_counts": {
      "ka": 40,
      "ap": 35,
      "tn": 25
    }
  },
  "performance": {
    "detection_speed": "~50ms/frame",
    "recognition_speed": "~10ms/face",
    "max_face_size": "640x640"
  }
}
```

### GET `/api/sync/status`
**Purpose:** Get cache synchronization status  
**Returns:**
```json
{
  "success": true,
  "cache_enabled": false,
  "message": "Using PostgreSQL + pgvector (no cache needed)"
}
```

### POST `/api/sync/refresh`
**Purpose:** Force cache refresh (no-op with pgvector)  
**Returns:**
```json
{
  "success": true,
  "message": "No cache to refresh - using PostgreSQL + pgvector"
}
```

### GET `/api/cache/info`
**Purpose:** Get cache information  
**Returns:**
```json
{
  "success": true,
  "cache_enabled": false,
  "message": "Using PostgreSQL + pgvector for direct database search"
}
```

---

## Health Checks

### GET `/health`
### HEAD `/health`
**Purpose:** Docker health check endpoint  
**Returns:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-13T10:00:00"
}
```

### GET `/api/health`
### HEAD `/api/health`
**Purpose:** Detailed health check  
**Returns:**
```json
{
  "status": "healthy",
  "database": "connected",
  "model": "loaded",
  "timestamp": "2025-12-13T10:00:00"
}
```

---

## Architecture Overview

### How the System Works

1. **Frontend (Web UI)**
   - HTML/CSS/JavaScript interface
   - Makes API calls to backend
   - Displays results dynamically

2. **Backend (FastAPI)**
   - Handles all API requests
   - Processes images
   - Manages database operations

3. **Face Recognition Engine**
   - InsightFace for face detection and feature extraction
   - 512-dimensional face embeddings
   - High accuracy (99.83% on LFW dataset)

4. **Database (PostgreSQL + pgvector)**
   - Stores person information
   - Stores face embeddings as vectors
   - Fast similarity search using HNSW index
   - Handles attendance records

5. **Workflow:**
   ```
   User uploads image → API receives request → 
   Face detection → Feature extraction → 
   Vector similarity search in PostgreSQL → 
   Return matches → Display in UI
   ```

### Key Features

- **Region-based filtering:** Separate databases for different regions (ka, ap, tn)
- **Duplicate prevention:** Prevents same face from being registered with different names
- **Attendance tracking:** Mark and track attendance with duplicate detection
- **Real-time recognition:** Fast recognition using pgvector similarity search
- **Multi-face support:** Can register and recognize multiple faces per person
- **Quality validation:** Ensures face quality before enrollment

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message here"
}
```

HTTP Status Codes:
- `200`: Success
- `400`: Bad request (invalid parameters)
- `404`: Resource not found
- `500`: Internal server error

---

## Rate Limiting & Performance

- Face detection: ~50ms per frame
- Face recognition: ~10ms per face
- Database queries: <10ms with pgvector index
- Max file size: 10MB (configurable)
- Supported formats: JPG, JPEG, PNG, BMP, TIFF, GIF, WEBP, AVIF, HEIC

---

## Security Considerations

1. **File validation:** Only image files accepted
2. **Size limits:** Prevents large file uploads
3. **SQL injection protection:** Using parameterized queries
4. **CORS enabled:** For cross-origin requests
5. **Input validation:** All inputs validated before processing

---

## Getting Started

1. Start the server:
   ```bash
   python -m uvicorn src.api.advanced_fastapi_app:app --reload --host 0.0.0.0 --port 8000
   ```

2. Access the web UI:
   ```
   http://localhost:8000
   ```

3. View API documentation:
   ```
   http://localhost:8000/docs
   ```

4. Test an endpoint:
   ```bash
   curl -X POST "http://localhost:8000/api/recognize" \
     -F "file=@face.jpg" \
     -F "region=ka"
   ```

---

## Support

For issues or questions, check the logs at `logs/face_recognition.log`

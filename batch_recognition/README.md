# 批量人脸识别工具

这是一个支持并发处理、进度显示和断点续传的批量人脸识别工具。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法
```bash
python batch_face_recognition.py /path/to/image/folder
```

### Windows用法
```cmd
set PYTHONIOENCODING=utf-8
python batch_face_recognition.py C:\path\to\image\folder

REM 过滤纯未知人员记录
python batch_face_recognition.py C:\path\to\image\folder --skip-unknown
```

### 测试用法（使用提供的测试图片）
```bash
python batch_face_recognition.py /opt/data2/chenlei/face-recognition-system/data/test_images
```

### 高级选项

```bash
# 自定义输出文件
python batch_face_recognition.py /path/to/images --output my_results.csv

# 调整并发数（默认5）
python batch_face_recognition.py /path/to/images --max-concurrent 3

# 自定义API地址
python batch_face_recognition.py /path/to/images --api-url https://your-api.com/recognize

# 重新开始（不使用断点续传）
python batch_face_recognition.py /path/to/images --no-resume

# 如果遇到SSL错误，禁用SSL验证
python batch_face_recognition.py /path/to/images --disable-ssl-verify

# 优先保留已知人员（推荐用于混合场景）
python batch_face_recognition.py /path/to/images --prioritize-known

# 查看帮助
python batch_face_recognition.py --help
```

## 重要功能说明

### 优先保留已知人员 (--prioritize-known)

当一张图片包含多个人脸时（超过5个），API返回的匹配结果可能会导致已知人员排在第6位之后，从而在CSV中被忽略。使用 `--prioritize-known` 选项可以：

- **自动重排序**：将已知人员的匹配结果排在前5位
- **避免遗漏**：确保已知人员不会因为排序问题而丢失  
- **保留数据**：所有数据都会记录，只是调整了优先级

**推荐使用场景**：
- 群体照片或聚会照片
- 监控场景（重点关注已知人员）
- 大型活动现场照片

## Windows系统使用说明

在Windows系统上运行时，如遇到编码错误，请：

1. **设置环境变量**（推荐）:
   ```cmd
   set PYTHONIOENCODING=utf-8
   python batch_face_recognition.py /path/to/images
   ```

2. **使用PowerShell**:
   ```powershell
   $env:PYTHONIOENCODING="utf-8"
   python batch_face_recognition.py /path/to/images
   ```

3. **在脚本中设置**（已内置）:
   脚本已自动检测Windows系统并设置UTF-8编码

## 功能特性

1. **并发处理**: 支持同时处理多个图片，提高效率
2. **进度显示**: 实时显示处理进度条
3. **断点续传**: 支持中断后继续处理，避免重复处理
4. **详细记录**: 将所有结果保存到CSV文件
5. **错误处理**: 记录处理失败的文件和错误信息
6. **多人脸支持**: 支持单张图片多个人脸的识别结果  
7. **智能过滤**: 可跳过纯未知人员记录，但保留可能包含已知人员的记录

## 输出格式

CSV文件包含以下列：

- `file_path`: 图片文件完整路径
- `file_name`: 图片文件名
- `success`: 处理是否成功
- `error`: 错误信息（如有）
- `total_faces`: 检测到的人脸数量
- `message`: API返回的消息
- `api_success`: API调用是否成功
- `face_N_*`: 每个人脸的详细信息（最多5个）
  - `face_N_person_id`: 人员ID
  - `face_N_name`: 人员姓名
  - `face_N_match_score`: 匹配分数
  - `face_N_distance`: 距离
  - `face_N_model`: 使用的模型
  - `face_N_quality`: 人脸质量
  - `face_N_age`: 年龄
  - `face_N_gender`: 性别
  - `face_N_emotion`: 情绪
  - `face_N_bbox`: 人脸边界框

## 支持的图片格式

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- WebP (.webp)
- AVIF (.avif)

## 日志文件

处理过程中的日志会保存到 `batch_recognition.log` 文件中，包括：
- 处理进度信息
- 成功/失败的文件列表
- 错误详情

## 断点续传

程序会自动创建 `progress.txt` 文件来记录已处理的文件。如果程序中断，再次运行时会自动跳过已处理的文件。

如果需要重新开始，可以：
1. 删除 `progress.txt` 文件，或
2. 使用 `--no-resume` 选项

## 常见问题解决

### SSL证书错误
如遇到以下错误：
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**解决方案**：
```bash
# 使用SSL禁用选项
python batch_face_recognition.py /path/to/images --disable-ssl-verify
```

### Windows编码错误
如遇到UnicodeEncodeError：
```cmd
set PYTHONIOENCODING=utf-8
python batch_face_recognition.py /path/to/images
```

### 网络连接问题
- 检查网络连接
- 验证API地址是否正确
- 尝试降低并发数: `--max-concurrent 1`

## 智能过滤说明

`--skip-unknown` 参数的过滤逻辑：

1. **保留的记录**：
   - 包含任何已知人员的记录
   - 匹配结果超过5个的记录（可能后面有已知人员）
   - 处理失败的记录

2. **跳过的记录**：
   - 只有当所有匹配结果都是"未知人员"且匹配数≤5时才跳过
   - 确保不会漏掉可能存在的已知人员

3. **使用场景**：
   - 减少CSV文件大小，专注于有价值的识别结果
   - 避免漏掉排在后面的已知人员匹配结果

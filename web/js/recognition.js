/**
 * 人脸识别模块 - recognition.js
 * 处理人脸识别相关功能
 */

// 全局变量
let currentRecognitionFile = null;
let lastRecognitionResult = null;

// ============= 文件处理 =============
function setupRecognitionTab() {
    const recognitionFileInput = document.getElementById('recognitionFileInput');
    const recognitionDropZone = document.getElementById('recognitionUploadArea');
    const recognitionBtn = document.getElementById('recognitionBtn');
    
    if (!recognitionFileInput) return;
    
    // 文件选择事件
    recognitionFileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        console.log('文件选择事件触发，文件:', file);
        if (file) {
            handleRecognitionFile(file);
        }
    });
    
    // 拖拽支持
    if (recognitionDropZone) {
        recognitionDropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add('dragover');
        });
        
        recognitionDropZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('dragover');
        });
        
        recognitionDropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleRecognitionFile(files[0]);
            }
        });
        
        recognitionDropZone.addEventListener('click', function() {
            console.log('上传区域被点击，触发文件选择');
            recognitionFileInput.click();
        });
    }
    
    // 识别按钮事件
    if (recognitionBtn) {
        recognitionBtn.addEventListener('click', function(e) {
            e.preventDefault(); // 防止任何默认行为
            e.stopPropagation(); // 防止事件冒泡
            
            console.log('识别按钮被点击，当前文件:', currentRecognitionFile);
            
            // 获取当前文件，优先使用全局变量
            let fileToUse = currentRecognitionFile;
            
            // 如果全局变量为空，尝试从input元素获取
            if (!fileToUse) {
                const fileInput = document.getElementById('recognitionFileInput');
                if (fileInput && fileInput.files && fileInput.files.length > 0) {
                    fileToUse = fileInput.files[0];
                    console.log('从input元素获取文件:', fileToUse);
                    // 更新全局变量
                    currentRecognitionFile = fileToUse;
                }
            }
            
            if (fileToUse) {
                console.log('开始识别，使用文件:', fileToUse.name);
                performRecognition(fileToUse);
            } else {
                console.error('没有可用的文件');
                showToast('错误', '请先选择图片文件', 'error');
            }
        });
    }
}

function handleRecognitionFile(file) {
    try {
        console.log('处理识别文件:', file);
        
        // 验证文件
        validateImageFile(file);
        
        currentRecognitionFile = file;
        console.log('设置当前识别文件:', currentRecognitionFile);
        
        // 显示预览
        showRecognitionPreview(file);
        
        // 启用识别按钮
        const recognitionBtn = document.getElementById('recognitionBtn');
        if (recognitionBtn) {
            recognitionBtn.disabled = false;
        }
        
        // 清除之前的结果
        clearRecognitionResults();
        
        showToast('文件选择', `已选择文件: ${file.name} (${formatFileSize(file.size)})`, 'info', 3000);
        
    } catch (error) {
        handleError(error, '文件处理');
        clearRecognitionFile();
    }
}

async function showRecognitionPreview(file) {
    try {
        const preview = document.getElementById('recognitionPreview');
        const previewImg = document.getElementById('recognitionPreviewImg');
        
        if (preview && previewImg) {
            const imageSrc = await createImagePreview(file);
            previewImg.src = imageSrc;
            preview.style.display = 'block';
        }
        
        // 更新文件信息
        const fileInfo = document.getElementById('recognitionFileInfo');
        if (fileInfo) {
            fileInfo.innerHTML = `
                <div class="file-info">
                    <i class="bi bi-file-earmark-image me-2"></i>
                    <strong>${file.name}</strong>
                    <span class="text-muted ms-2">${formatFileSize(file.size)}</span>
                </div>
            `;
            fileInfo.style.display = 'block';
        }
        
    } catch (error) {
        console.error('预览显示失败:', error);
    }
}

function clearRecognitionFile() {
    currentRecognitionFile = null;
    
    // 重置文件输入
    const recognitionFileInput = document.getElementById('recognitionFileInput');
    if (recognitionFileInput) {
        recognitionFileInput.value = '';
    }
    
    // 隐藏预览
    hideElement('recognitionPreview');
    hideElement('recognitionFileInfo');
    
    // 禁用识别按钮
    const recognitionBtn = document.getElementById('recognitionBtn');
    if (recognitionBtn) {
        recognitionBtn.disabled = true;
    }
    
    // 清除结果
    clearRecognitionResults();
}

function clearRecognitionResults() {
    const resultsDiv = document.getElementById('recognitionResults');
    if (resultsDiv) {
        resultsDiv.innerHTML = '';
        resultsDiv.style.display = 'none';
    }
    
    // 清除错误信息
    hideElement('recognitionError');
    lastRecognitionResult = null;
}

// ============= 人脸识别核心功能 =============
async function performRecognition(file) {
    console.log('performRecognition 被调用，参数 file:', file);
    console.log('全局变量 currentRecognitionFile:', currentRecognitionFile);
    
    if (!file) {
        console.error('没有文件参数，检查全局变量');
        if (currentRecognitionFile) {
            console.log('使用全局变量中的文件');
            file = currentRecognitionFile;
        } else {
            showToast('错误', '请先选择图片文件', 'error');
            return;
        }
    }
    
    console.log('最终使用的文件:', file);
    
    // 严格验证文件对象
    if (!file) {
        showToast('错误', '文件对象为空', 'error');
        return;
    }
    
    if (!(file instanceof File)) {
        console.error('file不是File实例:', typeof file, file);
        showToast('错误', '无效的文件对象', 'error');
        return;
    }
    
    if (!file.name || !file.size) {
        console.error('文件对象属性无效:', {name: file.name, size: file.size, type: file.type});
        showToast('错误', '文件对象属性无效', 'error');
        return;
    }
    
    console.log('文件验证通过:', {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified
    });
    
    // 创建文件对象的副本以防止引用丢失
    const fileClone = new File([file], file.name, {
        type: file.type,
        lastModified: file.lastModified
    });
    
    try {
        showGlobalSpinner('正在识别人脸...');
        clearRecognitionResults();
        
        // 显示加载状态
        const resultsDiv = document.getElementById('recognitionResults');
        if (resultsDiv) {
            resultsDiv.innerHTML = `
                <div class="text-center text-muted p-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">识别中...</span>
                    </div>
                    <h6 class="mt-3">正在识别人脸，请稍候...</h6>
                    <p class="mb-0">正在分析图片中的人脸特征</p>
                </div>
            `;
            resultsDiv.style.display = 'block';
        }
        
        // 获取当前识别阈值
        let threshold = 0.6; // 默认值
        try {
            const statsResponse = await fetchWithRetry(`${API_BASE_URL}/statistics`);
            const stats = await statsResponse.json();
            threshold = stats.recognition_threshold || 0.6;
            console.log('当前识别阈值:', threshold);
        } catch (e) {
            console.warn('获取阈值失败，使用默认值:', e);
        }
        
        // 验证文件对象是否仍然有效
        if (!fileClone || !(fileClone instanceof File)) {
            throw new Error('文件对象无效或已丢失');
        }
        
        console.log('发送识别请求...', { 
            fileName: fileClone.name, 
            fileSize: formatFileSize(fileClone.size),
            threshold: threshold,
            fileType: fileClone.type,
            fileObject: fileClone
        });
        
        // 最终验证：在发送请求前重新创建FormData
        console.log('=== 发送前最终验证 ===');
        const finalFormData = new FormData();
        finalFormData.append('file', fileClone);
        
        console.log('最终FormData验证:');
        console.log('  has("file"):', finalFormData.has('file'));
        for (let [key, value] of finalFormData.entries()) {
            console.log('  Entry:', key, '=', value);
            if (value instanceof File) {
                console.log('    File details:', {
                    name: value.name,
                    size: value.size,
                    type: value.type
                });
            }
        }
        
        // 最终验证：确保FormData不为空
        if (!finalFormData.has('file')) {
            throw new Error('FormData中缺少file字段');
        }
        
        // 调用识别API
        const response = await fetchWithRetry(`${API_BASE_URL}/recognize?threshold=${threshold}`, {
            method: 'POST',
            body: finalFormData
        });
        
        const result = await response.json();
        console.log('识别结果:', result);
        
        lastRecognitionResult = result;
        
        // 获取可视化图像（如果有检测到人脸）
        let visualImageSrc = null;
        if (result.total_faces && result.total_faces > 0) {
            visualImageSrc = await getVisualizationImage(fileClone, threshold);
        }
        
        // 显示识别结果
        displayRecognitionResults(result, visualImageSrc);
        
        showToast('识别完成', result.message || '人脸识别已完成', 'success');
        
    } catch (error) {
        console.error('识别错误:', error);
        handleError(error, '人脸识别');
        
        // 显示错误状态
        const resultsDiv = document.getElementById('recognitionResults');
        if (resultsDiv) {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    <strong>识别失败:</strong> ${error.message}
                </div>
            `;
        }
    } finally {
        hideGlobalSpinner();
    }
}

async function getVisualizationImage(file, threshold) {
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('threshold', threshold.toString());
        
        console.log('请求可视化图像...');
        
        const response = await fetchWithRetry(`${API_BASE_URL}/recognize_visual?threshold=${threshold}`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const imageUrl = URL.createObjectURL(blob);
            console.log('可视化图像获取成功');
            return imageUrl;
        } else {
            console.error('获取可视化图像失败:', response.status);
            return null;
        }
    } catch (error) {
        console.error('可视化图像请求错误:', error);
        return null;
    }
}

// ============= 结果显示 =============
function displayRecognitionResults(result, visualImageSrc = null) {
    const resultsDiv = document.getElementById('recognitionResults');
    if (!resultsDiv) return;
    
    if (!result.matches || result.matches.length === 0) {
        // 无匹配结果
        resultsDiv.innerHTML = createNoMatchResultsHTML(result, visualImageSrc);
        return;
    }
    
    // 有匹配结果
    resultsDiv.innerHTML = createMatchResultsHTML(result, visualImageSrc);
}

function createNoMatchResultsHTML(result, visualImageSrc) {
    return `
        <div class="row">
            ${visualImageSrc ? `
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="bi bi-image me-2"></i>检测结果可视化
                        </h6>
                    </div>
                    <div class="card-body text-center">
                        <img src="${visualImageSrc}" class="img-fluid rounded" 
                             style="max-height: 400px; cursor: pointer;" 
                             onclick="showImageModal('${visualImageSrc}', '检测结果图片')">
                        <div class="mt-2">
                            <small class="text-muted">
                                <i class="bi bi-zoom-in me-1"></i>点击图片可放大查看
                            </small>
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
            <div class="col-md-${visualImageSrc ? '6' : '12'} mb-3">
                <div class="text-center text-muted p-4">
                    <i class="bi bi-exclamation-triangle fs-1 text-warning"></i>
                    <h5 class="mt-3">未识别到已知人员</h5>
                    <p>检测到人脸数量: <strong>${result.total_faces || 0}</strong></p>
                    <small class="text-muted">
                        ${result.total_faces > 0 ? 
                            '图片中包含人脸，但未匹配到数据库中的已知人员' : 
                            '未在图片中检测到任何人脸'}
                    </small>
                    ${result.total_faces > 0 ? `
                        <div class="mt-3">
                            <small class="text-info">
                                <i class="bi bi-info-circle me-1"></i>
                                建议：可以将此人脸添加到人员库中
                            </small>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function createMatchResultsHTML(result, visualImageSrc) {
    // ID说明卡片
    const idExplanationCard = `
        <div class="card border-info mb-3">
            <div class="card-header bg-info text-white">
                <h6 class="mb-0">
                    <i class="bi bi-info-circle me-2"></i>ID标识说明
                </h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <div class="d-flex align-items-center mb-2">
                            <span class="badge bg-primary me-2" style="width: 35px;">P1</span>
                            <small>人员库ID=1的已知人员</small>
                        </div>
                        <div class="d-flex align-items-center mb-2">
                            <span class="badge bg-primary me-2" style="width: 35px;">P1B</span>
                            <small>同一人员的第2张脸</small>
                        </div>
                        <div class="d-flex align-items-center">
                            <span class="badge bg-warning me-2" style="width: 35px;">U1</span>
                            <small>第1个未知人员</small>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <small class="text-muted">
                            • <strong>相同颜色</strong>表示同一人员<br>
                            • <strong>P开头</strong>表示已知人员<br>
                            • <strong>U开头</strong>表示未知人员<br>
                            • <strong>字母后缀</strong>区分同一人的多张脸
                        </small>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 主要布局
    let html = idExplanationCard + `
        <div class="row">
            ${visualImageSrc ? `
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="bi bi-image me-2"></i>检测结果可视化
                        </h6>
                    </div>
                    <div class="card-body text-center">
                        <img src="${visualImageSrc}" class="img-fluid rounded" 
                             style="max-height: 400px; cursor: pointer;" 
                             onclick="showImageModal('${visualImageSrc}', '识别结果图片')">
                        <div class="mt-2">
                            <small class="text-muted">
                                <i class="bi bi-zoom-in me-1"></i>点击图片可放大查看
                            </small>
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
            <div class="col-md-${visualImageSrc ? '6' : '12'}">
                <div class="alert alert-info mb-3">
                    <i class="bi bi-info-circle me-2"></i>
                    <strong>识别统计：</strong> 检测到 ${result.total_faces} 张人脸，识别出 ${result.matches.length} 个已知人员
                </div>
    `;
    
    // 显示每个匹配结果
    result.matches.forEach((match, index) => {
        const matchScore = match.match_score ? match.match_score.toFixed(1) : '0.0';
        const distance = match.distance ? match.distance.toFixed(3) : 'N/A';
        const badgeClass = parseFloat(matchScore) > 80 ? 'bg-success' : 
                          parseFloat(matchScore) > 60 ? 'bg-warning text-dark' : 'bg-secondary';
        
        const isUnknown = match.person_id === -1 || match.name === '未知人员';
        const cardClass = isUnknown ? 'border-warning' : 'border-success';
        
        html += `
            <div class="card ${cardClass} mb-3">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span class="fw-bold ${isUnknown ? 'text-warning' : 'text-success'}">
                        <i class="bi ${isUnknown ? 'bi-question-circle' : 'bi-person-check'} me-2"></i>
                        ${match.name}
                    </span>
                    <span class="badge ${badgeClass} fs-6">${matchScore}%</span>
                </div>
                <div class="card-body">
                    ${!isUnknown ? `
                        <p class="card-text mb-2">
                            <strong>人员ID:</strong> ${match.person_id}
                        </p>
                    ` : ''}
                    <div class="row text-center">
                        <div class="col-4">
                            <small class="text-muted">匹配度</small>
                            <div class="fw-bold text-primary">${matchScore}%</div>
                        </div>
                        <div class="col-4">
                            <small class="text-muted">距离</small>
                            <div class="fw-bold text-info">${distance}</div>
                        </div>
                        <div class="col-4">
                            <small class="text-muted">质量</small>
                            <div class="fw-bold text-success">
                                ${match.quality ? (match.quality * 100).toFixed(1) + '%' : 'N/A'}
                            </div>
                        </div>
                    </div>
                    ${match.bbox ? `
                        <div class="mt-2">
                            <small class="text-muted">
                                <i class="bi bi-geo-alt me-1"></i>
                                检测位置: [${match.bbox.join(', ')}]
                            </small>
                        </div>
                    ` : ''}
                    <div class="mt-2">
                        <small class="text-muted">
                            <i class="bi bi-clock me-1"></i>
                            识别时间: ${formatDate(new Date())}
                        </small>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += `
            </div>
        </div>
    `;
    
    return html;
}

// ============= 图片模态框 =============
function showImageModal(imageSrc, title) {
    let modal = document.getElementById('imageModal');
    
    if (!modal) {
        // 创建模态框
        modal = document.createElement('div');
        modal.id = 'imageModal';
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="imageModalTitle">图片预览</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center">
                        <img id="imageModalImg" class="img-fluid">
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <button type="button" class="btn btn-primary" onclick="downloadModalImage()">
                            <i class="bi bi-download me-2"></i>下载图片
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // 设置内容
    document.getElementById('imageModalTitle').textContent = title;
    document.getElementById('imageModalImg').src = imageSrc;
    
    // 显示模态框
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

function downloadModalImage() {
    const img = document.getElementById('imageModalImg');
    if (img && img.src) {
        const link = document.createElement('a');
        link.href = img.src;
        link.download = 'recognition_result_' + Date.now() + '.png';
        link.click();
    }
}

// ============= 导出全局函数 =============
window.setupRecognitionTab = setupRecognitionTab;
window.handleRecognitionFile = handleRecognitionFile;
window.clearRecognitionFile = clearRecognitionFile;
window.performRecognition = performRecognition;
window.showImageModal = showImageModal;
window.downloadModalImage = downloadModalImage;

// 添加一个简单的测试函数
window.testDirectUpload = function() {
    const fileInput = document.getElementById('recognitionFileInput');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        console.error('没有选择文件');
        alert('请先选择一个文件');
        return;
    }
    
    const file = fileInput.files[0];
    console.log('测试直接上传，文件:', file);
    
    const formData = new FormData();
    formData.append('file', file);
    
    console.log('FormData检查:');
    console.log('  has("file"):', formData.has('file'));
    for (let [key, value] of formData.entries()) {
        console.log('  ', key, ':', value);
        if (value instanceof File) {
            console.log('    文件详情:', {name: value.name, size: value.size, type: value.type});
        }
    }
    
    // 使用原生fetch直接发送，不通过fetchWithRetry
    fetch('http://localhost:8001/api/recognize?threshold=0.6', {
        method: 'POST',
        body: formData
    }).then(response => {
        console.log('响应状态:', response.status);
        return response.text();
    }).then(text => {
        console.log('响应内容:', text);
        alert('响应: ' + text);
    }).catch(error => {
        console.error('请求错误:', error);
        alert('错误: ' + error.message);
    });
};

/**
 * 人脸识别系统前端JavaScript
 */

// API配置
const API_BASE_URL = '/api';

// 全局变量
let currentFiles = [];
let currentUploadType = 'single';

// 全局加载指示器管理
let loadingCount = 0;

function showGlobalSpinner(text = '处理中...') {
    loadingCount++;
    const spinner = document.getElementById('globalSpinner');
    const spinnerText = document.getElementById('spinnerText');
    
    if (spinner) {
        spinner.style.display = 'block';
        if (spinnerText) {
            spinnerText.textContent = text;
        }
    }
    
    // 显示顶部加载条
    const loadingBar = document.getElementById('loadingBar');
    if (loadingBar) {
        loadingBar.style.display = 'block';
        loadingBar.style.transform = 'scaleX(0.3)';
    }
}

function hideGlobalSpinner() {
    loadingCount = Math.max(0, loadingCount - 1);
    
    if (loadingCount === 0) {
        const spinner = document.getElementById('globalSpinner');
        const loadingBar = document.getElementById('loadingBar');
        
        if (spinner) {
            spinner.style.display = 'none';
        }
        
        if (loadingBar) {
            loadingBar.style.transform = 'scaleX(1)';
            setTimeout(() => {
                loadingBar.style.display = 'none';
                loadingBar.style.transform = 'scaleX(0)';
            }, 300);
        }
    }
}

/**
 * 网络请求重试机制
 */
async function fetchWithRetry(url, options = {}, retries = 3, delay = 1000) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, {
                ...options,
                signal: AbortSignal.timeout(30000) // 30秒超时
            });
            
            if (response.ok) {
                return response;
            }
            
            // 如果是最后一次重试，抛出详细错误
            if (i === retries - 1) {
                const errorData = await response.text().catch(() => '');
                throw new Error(`HTTP ${response.status}: ${errorData || response.statusText}`);
            }
        } catch (error) {
            // 如果是最后一次重试，抛出错误
            if (i === retries - 1) {
                if (error.name === 'AbortError') {
                    showToast('请求超时', '网络请求超时，请检查网络连接', 'warning');
                    throw new Error('请求超时');
                } else if (error.message.includes('Failed to fetch')) {
                    showToast('网络错误', '无法连接到服务器，请检查网络连接', 'error');
                    throw new Error('网络连接失败');
                }
                throw error;
            }
            // 等待后重试
            await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
        }
    }
}

/**
 * 显示错误信息
 */
function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                ${message}
            </div>
        `;
        container.style.display = 'block';
    } else {
        // 如果找不到指定容器，显示在通用错误区域
        console.error('错误:', message);
        alert(message);
    }
}

/**
 * 显示成功信息
 */
function showSuccess(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="alert alert-success" role="alert">
                <i class="bi bi-check-circle-fill me-2"></i>
                ${message}
            </div>
        `;
        container.style.display = 'block';
    }
}

/**
 * 清除消息
 */
function clearMessages(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
        container.style.display = 'none';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * 初始化应用
 */
function initializeApp() {
    setupEventListeners();
    setupKeyboardShortcuts();
    loadStatistics();
    loadPersons();
    loadConfig();
}

/**
 * 设置键盘快捷键
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+R: 刷新统计信息
        if (e.ctrlKey && e.key === 'r') {
            e.preventDefault();
            loadStatistics();
            loadPersons();
            showToast('提示', '数据已刷新', 'info');
        }
        
        // Escape: 关闭模态框
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
        
        // Ctrl+U: 快速上传 (人脸识别页面)
        if (e.ctrlKey && e.key === 'u') {
            e.preventDefault();
            const activeTab = document.querySelector('#mainTabs .nav-link.active');
            if (activeTab && activeTab.getAttribute('data-bs-target') === '#recognition') {
                document.getElementById('recognitionFileInput').click();
            } else if (activeTab && activeTab.getAttribute('data-bs-target') === '#enrollment') {
                document.getElementById('enrollmentFileInput').click();
            }
        }
    });
}

/**
 * 设置事件监听器
 */
function setupEventListeners() {
    // 人脸识别页面
    setupRecognitionTab();
    
    // 人脸入库页面
    setupEnrollmentTab();
    
    // 配置表单
    setupConfigForm();
    
    // 标签页切换事件
    document.querySelectorAll('#mainTabs button[data-bs-toggle="pill"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            const targetTab = event.target.getAttribute('data-bs-target');
            if (targetTab === '#statistics') {
                loadStatistics();
            } else if (targetTab === '#management') {
                loadPersons();
            }
        });
    });
}

/**
 * 设置人脸识别页面事件
 */
function setupRecognitionTab() {
    const uploadArea = document.getElementById('recognitionUploadArea');
    const fileInput = document.getElementById('recognitionFileInput');
    const previewDiv = document.getElementById('recognitionPreview');
    const previewImg = document.getElementById('recognitionPreviewImg');
    const recognitionBtn = document.getElementById('recognitionBtn');

    // 阈值滑块事件
    const thresholdSlider = document.getElementById('recognitionThreshold');
    const thresholdValue = document.getElementById('thresholdValue');
    if (thresholdSlider && thresholdValue) {
        thresholdSlider.addEventListener('input', function() {
            thresholdValue.textContent = this.value;
        });
    }

    // 点击上传区域
    uploadArea.addEventListener('click', () => fileInput.click());

    // 文件选择
    fileInput.addEventListener('change', function(e) {
        handleRecognitionFile(e.target.files[0]);
    });

    // 拖拽事件
    setupDragAndDrop(uploadArea, handleRecognitionFile);

    // 识别按钮
    recognitionBtn.addEventListener('click', function() {
        if (currentFiles && currentFiles.length > 0) {
            performRecognition(currentFiles[0]);
        } else {
            showToast('错误', '请先选择图片文件', 'error');
        }
    });
}

/**
 * 设置人脸入库页面事件
 */
function setupEnrollmentTab() {
    const uploadArea = document.getElementById('enrollmentUploadArea');
    const fileInput = document.getElementById('enrollmentFileInput');
    const form = document.getElementById('enrollmentForm');
    const uploadTypeRadios = document.querySelectorAll('input[name="uploadType"]');

    // 上传方式切换
    uploadTypeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            currentUploadType = this.value;
            updateUploadAreaText();
            fileInput.multiple = (this.value === 'batch');
            clearEnrollmentPreview();
        });
    });

    // 点击上传区域
    uploadArea.addEventListener('click', () => fileInput.click());

    // 文件选择
    fileInput.addEventListener('change', function(e) {
        handleEnrollmentFiles(Array.from(e.target.files));
    });

    // 拖拽事件
    setupDragAndDrop(uploadArea, (files) => {
        if (currentUploadType === 'single') {
            handleEnrollmentFiles([files]);
        } else {
            handleEnrollmentFiles(Array.from(files));
        }
    });

    // 表单提交
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        handleEnrollmentSubmit();
    });
}

/**
 * 设置配置表单事件
 */
function setupConfigForm() {
    // 配置已移至识别页面，这里不需要处理
}

/**
 * 设置拖拽上传
 */
function setupDragAndDrop(element, callback) {
    element.addEventListener('dragover', function(e) {
        e.preventDefault();
        element.classList.add('dragover');
    });

    element.addEventListener('dragleave', function(e) {
        e.preventDefault();
        element.classList.remove('dragover');
    });

    element.addEventListener('drop', function(e) {
        e.preventDefault();
        element.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files).filter(file => 
            file.type.startsWith('image/')
        );
        
        if (files.length > 0) {
            if (callback.length > 1) {
                callback(files);
            } else {
                callback(files[0]);
            }
        }
    });
}

/**
 * 处理识别文件（增加验证）
 */
function handleRecognitionFile(file) {
    const validation = validateFile(file);
    if (!validation.valid) {
        showToast('错误', validation.error, 'error');
        return;
    }

    const previewDiv = document.getElementById('recognitionPreview');
    const previewImg = document.getElementById('recognitionPreviewImg');
    const recognitionBtn = document.getElementById('recognitionBtn');

    // 显示预览
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImg.src = e.target.result;
        previewDiv.style.display = 'block';
        recognitionBtn.disabled = false;
    };
    reader.readAsDataURL(file);

    currentFiles = [file];
    
    // 显示文件信息
    showToast('成功', `已选择文件: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, 'success');
}

/**
 * 验证文件类型和大小
 */
function validateFile(file) {
    // 支持的图片格式
    const supportedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/webp'];
    // 最大文件大小 (10MB)
    const maxSize = 10 * 1024 * 1024;
    
    if (!supportedTypes.includes(file.type)) {
        return {
            valid: false,
            error: `不支持的文件格式: ${file.name}。支持格式: JPG, PNG, BMP, WebP`
        };
    }
    
    if (file.size > maxSize) {
        return {
            valid: false,
            error: `文件过大: ${file.name} (${(file.size / 1024 / 1024).toFixed(1)}MB)。最大支持10MB`
        };
    }
    
    return { valid: true };
}

/**
 * 处理入库文件（增加验证）
 */
function handleEnrollmentFiles(files) {
    if (!files.length) {
        return;
    }

    // 验证所有文件
    const invalidFiles = [];
    const validFiles = [];
    
    files.forEach(file => {
        const validation = validateFile(file);
        if (validation.valid) {
            validFiles.push(file);
        } else {
            invalidFiles.push(validation.error);
        }
    });
    
    // 显示验证错误
    if (invalidFiles.length > 0) {
        showToast('错误', invalidFiles.join('\n'), 'error');
    }
    
    if (validFiles.length === 0) {
        showToast('错误', '没有有效的图片文件', 'error');
        return;
    }

    if (currentUploadType === 'single' && validFiles.length > 1) {
        showToast('警告', '单张模式只能选择一张图片', 'warning');
        return;
    }

    currentFiles = validFiles;
    showEnrollmentPreview(validFiles);
    document.getElementById('enrollmentBtn').disabled = false;
    
    // 显示文件统计
    if (invalidFiles.length > 0) {
        showToast('提示', `已选择${validFiles.length}个有效文件，${invalidFiles.length}个文件被跳过`, 'info');
    }
}

/**
 * 显示入库预览（优化性能）
 */
function showEnrollmentPreview(files) {
    const previewDiv = document.getElementById('enrollmentPreview');
    const previewImages = document.getElementById('enrollmentPreviewImages');
    
    previewImages.innerHTML = '';
    
    files.forEach((file, index) => {
        // 限制预览数量以提升性能
        if (index >= 20) {
            if (index === 20) {
                const col = document.createElement('div');
                col.className = 'col-md-3 mb-3';
                col.innerHTML = `
                    <div class="card border-dashed">
                        <div class="card-body text-center p-3">
                            <i class="bi bi-three-dots fs-1 text-muted"></i>
                            <p class="mb-0 text-muted">还有 ${files.length - 20} 个文件</p>
                        </div>
                    </div>
                `;
                previewImages.appendChild(col);
            }
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            const col = document.createElement('div');
            col.className = 'col-md-3 mb-3';
            col.innerHTML = `
                <div class="card">
                    <img src="${e.target.result}" class="card-img-top" style="height: 150px; object-fit: cover;" loading="lazy">
                    <div class="card-body p-2">
                        <small class="text-muted">${file.name}</small>
                        <br><small class="text-muted">${(file.size / 1024).toFixed(1)} KB</small>
                    </div>
                </div>
            `;
            previewImages.appendChild(col);
        };
        reader.readAsDataURL(file);
    });
    
    previewDiv.style.display = 'block';
}

/**
 * 清除入库预览
 */
function clearEnrollmentPreview() {
    document.getElementById('enrollmentPreview').style.display = 'none';
    document.getElementById('enrollmentBtn').disabled = true;
    currentFiles = [];
}

/**
 * 更新上传区域文本
 */
function updateUploadAreaText() {
    const uploadText = document.getElementById('uploadText');
    if (currentUploadType === 'single') {
        uploadText.textContent = '点击选择图片或拖拽图片到此处';
    } else {
        uploadText.textContent = '点击选择多张图片或拖拽图片到此处';
    }
}

/**
 * 执行人脸识别
 */
async function performRecognition(file) {
    // 清除之前的错误消息
    clearMessages('recognitionError');
    
    // 重置结果区域为加载状态
    const resultsDiv = document.getElementById('recognitionResults');
    resultsDiv.innerHTML = `
        <div class="text-center text-muted">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">识别中...</span>
            </div>
            <p class="mt-3">正在识别人脸，请稍候...</p>
        </div>
    `;
    resultsDiv.style.display = 'block';
    
    try {
        // 从系统配置获取当前阈值
        let threshold = 0.6; // 默认值
        try {
            const statsResponse = await fetch(`${API_BASE_URL}/statistics`);
            if (statsResponse.ok) {
                const stats = await statsResponse.json();
                threshold = stats.system_config?.recognition_threshold?.current || 0.6;
            }
        } catch (e) {
            console.warn('获取阈值失败，使用默认值:', e);
        }
        
        const formData = new FormData();
        formData.append('file', file);

        console.log('发送识别请求...', { fileName: file.name, threshold: threshold });

        // 首先调用普通识别API获取结果数据（传递阈值参数）
        const response = await fetch(`${API_BASE_URL}/recognize?threshold=${threshold}`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            console.log('识别结果:', result);
            
            // 如果有检测到人脸，获取可视化图像
            let visualImageSrc = null;
            if (result.total_faces > 0) {
                visualImageSrc = await getVisualizationImage(file, threshold);
            }
            
            // 显示识别结果（图片和文字交换位置）
            displayRecognitionResults(result, visualImageSrc);
            
            showToast('成功', result.message || '识别完成', 'success');
        } else {
            const result = await response.json();
            showError('recognitionError', result.error || '识别失败');
            showToast('错误', result.error || '识别失败', 'error');
        }
    } catch (error) {
        console.error('识别错误:', error);
        showError('recognitionError', '识别过程中发生错误: ' + error.message);
        showToast('错误', '识别过程中发生错误', 'error');
    }
}

/**
 * 获取可视化识别图像
 */
async function getVisualizationImage(file, threshold) {
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('threshold', threshold.toString());

        const response = await fetch(`${API_BASE_URL}/recognize_visual?threshold=${threshold}`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const blob = await response.blob();
            const imageUrl = URL.createObjectURL(blob);
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

/**
 * 显示识别结果
 */
function displayRecognitionResults(result, visualImageSrc = null) {
    const resultsDiv = document.getElementById('recognitionResults');
    
    if (!result.matches || result.matches.length === 0) {
        resultsDiv.innerHTML = `
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
                            <img src="${visualImageSrc}" class="img-fluid rounded" style="max-height: 400px;">
                        </div>
                    </div>
                </div>
                ` : ''}
                <div class="col-md-${visualImageSrc ? '6' : '12'} mb-3">
                    <div class="text-center text-muted p-4">
                        <i class="bi bi-exclamation-triangle fs-1 text-warning"></i>
                        <h5 class="mt-3">未识别到已知人员</h5>
                        <p>检测到人脸数量: ${result.total_faces || 0}</p>
                        <small class="text-muted">
                            ${result.total_faces > 0 ? '检测到人脸，但未匹配到数据库中的人员' : '未检测到任何人脸'}
                        </small>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    // 创建结果布局：左侧图片，右侧文字结果
    let html = `
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
                        <img src="${visualImageSrc}" class="img-fluid rounded" style="max-height: 400px;">
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

    // 显示识别结果
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
                    ${!isUnknown ? `<p class="card-text mb-2"><strong>人员ID:</strong> ${match.person_id}</p>` : ''}
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
                            <div class="fw-bold text-success">${match.quality ? (match.quality * 100).toFixed(1) + '%' : 'N/A'}</div>
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
                            <i class="bi bi-cpu me-1"></i>
                            识别模型: ${match.model || 'N/A'}
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

    resultsDiv.innerHTML = html;
}

/**
 * 处理入库表单提交
 */
async function handleEnrollmentSubmit() {
    const nameInput = document.getElementById('personName');
    const descriptionInput = document.getElementById('personDescription');
    
    const name = nameInput.value.trim();
    const description = descriptionInput.value.trim();
    
    if (!currentFiles || currentFiles.length === 0) {
        showToast('错误', '请选择图片文件', 'error');
        return;
    }
    
    // 设置按钮加载状态
    const submitBtn = document.getElementById('enrollmentBtn');
    setButtonLoading(submitBtn, true);
    
    try {
        if (currentUploadType === 'single') {
            // 单张图片入库
            if (!name) {
                showToast('错误', '请输入人员姓名', 'error');
                return;
            }
            await performEnrollment(currentFiles[0], name, description);
        } else {
            // 批量入库 - 调用专门的批量处理函数
            await processBatchEnrollment(currentFiles, name, description);
        }
        
        // 清空表单
        nameInput.value = '';
        descriptionInput.value = '';
        clearEnrollmentPreview();
        
    } finally {
        setButtonLoading(submitBtn, false);
    }
}

/**
 * 执行单个文件的批量入库
 */
async function performEnrollmentBatch(file, name, description) {
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', name);
        if (description && description.trim()) {
            formData.append('description', description.trim());
        }

        const response = await fetch('/api/enroll', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: '服务器错误' }));
            return {
                success: false,
                error: `入库失败 (${response.status}): ${errorData.detail || errorData.message || '未知错误'}`
            };
        }

        const result = await response.json();
        
        if (result.success) {
            return {
                success: true,
                data: result,
                personName: name,
                fileName: file.name
            };
        } else {
            return {
                success: false,
                error: result.error || result.message || '入库失败'
            };
        }
    } catch (error) {
        return {
            success: false,
            error: '网络请求失败: ' + error.message
        };
    }
}

/**
 * 处理批量入库（带进度提示）
 */
async function processBatchEnrollment(files, name, description) {
    const resultsDiv = document.getElementById('enrollmentResults');
    const totalFiles = files.length;
    
    // 初始化进度显示
    showBatchProgress(0, totalFiles, '准备开始批量入库...');
    
    const batchResults = [];
    const errorResults = [];
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // 批量入库逻辑：如果有输入人名就用人名，否则用文件名
        let personName;
        if (name && name.trim()) {
            // 有输入人名，直接使用（一个人的多张照片）
            personName = name.trim();
        } else {
            // 没有输入人名，使用文件名（去掉扩展名）
            personName = file.name.split('.')[0];
        }
        
        // 更新进度
        showBatchProgress(i + 1, totalFiles, `正在处理 ${file.name} (${personName})...`);
        
        try {
            const result = await performEnrollmentBatch(file, personName, description);
            if (result && result.success) {
                batchResults.push(result);
                // 实时更新成功计数
                updateBatchProgressSuccess(batchResults.length, totalFiles);
            } else {
                errorResults.push({
                    fileName: file.name,
                    personName: personName,
                    error: result ? result.error : '未知错误'
                });
            }
        } catch (error) {
            console.error(`批量入库第${i+1}个文件失败:`, error);
            errorResults.push({
                fileName: file.name,
                personName: personName,
                error: error.message || '网络请求失败'
            });
        }
        
        // 短暂延迟，让用户看到进度变化
        await new Promise(resolve => setTimeout(resolve, 200));
    }
    
    // 显示最终结果
    displayBatchResults(batchResults, errorResults, totalFiles);
}

/**
 * 显示批量入库进度
 */
function showBatchProgress(current, total, message) {
    const resultsDiv = document.getElementById('enrollmentResults');
    const percentage = Math.round((current / total) * 100);
    
    resultsDiv.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0">
                    <i class="bi bi-upload me-2"></i>批量入库进度
                </h6>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="text-muted">进度</span>
                        <span class="fw-bold">${current}/${total}</span>
                    </div>
                    <div class="progress" style="height: 8px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" 
                             style="width: ${percentage}%"
                             aria-valuenow="${percentage}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">
                        </div>
                    </div>
                </div>
                <div class="d-flex align-items-center">
                    <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <span class="text-muted">${message}</span>
                </div>
            </div>
        </div>
    `;
    resultsDiv.style.display = 'block';
}

/**
 * 更新批量进度中的成功计数
 */
function updateBatchProgressSuccess(successCount, total) {
    const resultsDiv = document.getElementById('enrollmentResults');
    if (resultsDiv.innerHTML.includes('批量入库进度')) {
        // 添加成功计数显示
        const cardBody = resultsDiv.querySelector('.card-body');
        let successInfo = cardBody.querySelector('.success-info');
        if (!successInfo) {
            successInfo = document.createElement('div');
            successInfo.className = 'success-info mt-2 p-2 bg-success bg-opacity-10 rounded';
            cardBody.appendChild(successInfo);
        }
        successInfo.innerHTML = `
            <small class="text-success">
                <i class="bi bi-check-circle me-1"></i>
                已成功入库: ${successCount} 个
            </small>
        `;
    }
}

/**
 * 显示批量入库最终结果
 */
function displayBatchResults(successResults, errorResults, totalFiles) {
    const resultsDiv = document.getElementById('enrollmentResults');
    const successCount = successResults.length;
    const errorCount = errorResults.length;
    
    let html = `
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0">
                    <i class="bi bi-check2-all me-2"></i>批量入库完成
                </h6>
            </div>
            <div class="card-body">
                <!-- 总体统计 -->
                <div class="row mb-3">
                    <div class="col-md-4">
                        <div class="text-center p-3 bg-light rounded">
                            <h4 class="text-primary mb-1">${totalFiles}</h4>
                            <small class="text-muted">总计文件</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center p-3 bg-success bg-opacity-10 rounded">
                            <h4 class="text-success mb-1">${successCount}</h4>
                            <small class="text-muted">成功入库</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center p-3 ${errorCount > 0 ? 'bg-danger bg-opacity-10' : 'bg-light'} rounded">
                            <h4 class="${errorCount > 0 ? 'text-danger' : 'text-muted'} mb-1">${errorCount}</h4>
                            <small class="text-muted">失败文件</small>
                        </div>
                    </div>
                </div>
    `;
    
    // 成功结果
    if (successCount > 0) {
        html += `
                <div class="mb-3">
                    <h6 class="text-success">
                        <i class="bi bi-check-circle me-2"></i>成功入库的文件 (${successCount})
                    </h6>
                    <div class="list-group list-group-flush">
        `;
        
        successResults.forEach(result => {
            html += `
                        <div class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${result.fileName}</strong>
                                <br><small class="text-muted">人员: ${result.personName}</small>
                            </div>
                            <span class="badge bg-success rounded-pill">
                                <i class="bi bi-check"></i>
                            </span>
                        </div>
            `;
        });
        
        html += `
                    </div>
                </div>
        `;
    }
    
    // 失败结果
    if (errorCount > 0) {
        html += `
                <div class="mb-3">
                    <h6 class="text-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>失败的文件 (${errorCount})
                    </h6>
                    <div class="list-group list-group-flush">
        `;
        
        errorResults.forEach(result => {
            html += `
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <strong class="text-danger">${result.fileName}</strong>
                                    <br><small class="text-muted">人员: ${result.personName}</small>
                                    <br><small class="text-danger">错误: ${result.error}</small>
                                </div>
                                <span class="badge bg-danger rounded-pill">
                                    <i class="bi bi-x"></i>
                                </span>
                            </div>
                        </div>
            `;
        });
        
        html += `
                    </div>
                </div>
        `;
    }
    
    html += `
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">
                        批量入库完成时间: ${new Date().toLocaleString('zh-CN')}
                    </small>
                    <button class="btn btn-primary btn-sm" onclick="loadPersons(); loadStatistics();">
                        <i class="bi bi-arrow-clockwise me-1"></i>刷新数据
                    </button>
                </div>
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
    
    // 显示总结Toast
    if (errorCount === 0) {
        showToast('成功', `批量入库完成！成功处理 ${successCount} 个文件`, 'success');
    } else {
        showToast('完成', `批量入库完成！成功 ${successCount} 个，失败 ${errorCount} 个`, 'warning');
    }
    
    // 自动刷新数据
    setTimeout(() => {
        loadPersons();
        loadStatistics();
    }, 1000);
}

/**
 * 执行人脸入库
 */
async function performEnrollment(file, name, description) {
    // 清除之前的消息
    clearMessages('enrollmentError');
    clearMessages('enrollmentResults');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', name);
        if (description && description.trim()) {
            formData.append('description', description.trim());
        }

        console.log('发送入库请求...', { fileName: file.name, name: name });

        const response = await fetch('/api/enroll', {
            method: 'POST',
            body: formData
        });

        console.log('入库响应状态:', response.status);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: '服务器错误' }));
            console.error('入库请求失败:', response.status, errorData);
            showError('enrollmentError', `入库失败 (${response.status}): ${errorData.detail || errorData.message || '未知错误'}`);
            return;
        }

        const result = await response.json();
        console.log('入库结果:', result);
        
        if (result.success) {
            displayEnrollmentResults(result);
            // 刷新人员列表
            setTimeout(() => {
                loadPersons();
                loadStatistics();
            }, 500);
        } else {
            showError('enrollmentError', result.error || result.message || '入库失败');
        }
    } catch (error) {
        console.error('入库请求异常:', error);
        showError('enrollmentError', '网络请求失败: ' + error.message);
    }
}

/**
 * 显示入库结果
 */
function displayEnrollmentResults(result) {
    const resultsDiv = document.getElementById('enrollmentResults');
    
    let html = `
        <div class="alert alert-success" role="alert">
            <i class="bi bi-check-circle-fill me-2"></i>
            <strong>人脸入库成功！</strong>
        </div>
    `;

    // 如果有人脸检测图像，先显示可视化结果
    if (result.visualized_image) {
        html += `
            <div class="card mb-3">
                <div class="card-header">
                    <h6 class="mb-0">
                        <i class="bi bi-eye me-2"></i>人脸检测结果
                    </h6>
                </div>
                <div class="card-body text-center">
                    <img src="data:image/jpeg;base64,${result.visualized_image}" 
                         class="img-fluid rounded border" 
                         alt="人脸检测结果" 
                         style="max-width: 100%; max-height: 400px;">
                    <div class="mt-2">
                        <small class="text-muted">
                            <i class="bi bi-info-circle me-1"></i>
                            绿色框标记检测到的人脸区域及质量评分
                        </small>
                    </div>
                </div>
            </div>
        `;
    }

    // 显示入库详情
    html += `
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0">
                    <i class="bi bi-person-plus me-2"></i>入库信息
                </h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label fw-bold text-primary">人员信息</label>
                            <p class="mb-1"><strong>姓名:</strong> ${result.person_name}</p>
                            <p class="mb-1"><strong>ID:</strong> ${result.person_id}</p>
                            ${result.description ? `<p class="mb-1"><strong>备注:</strong> ${result.description}</p>` : ''}
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label fw-bold text-success">检测统计</label>
                            <p class="mb-1"><strong>检测人脸数:</strong> ${result.faces_detected || 1}</p>
                            <p class="mb-1"><strong>处理时间:</strong> ${result.processing_time ? (result.processing_time * 1000).toFixed(0) + 'ms' : 'N/A'}</p>
                            ${result.face_quality ? `<p class="mb-1"><strong>人脸质量:</strong> ${(result.face_quality * 100).toFixed(1)}%</p>` : ''}
                        </div>
                    </div>
                </div>
                
                ${result.face_details && result.face_details.length > 0 ? `
                    <div class="mt-3">
                        <label class="form-label fw-bold text-info">人脸详情</label>
                        <div class="row">
                            ${result.face_details.map((face, index) => `
                                <div class="col-md-4 mb-2">
                                    <div class="card border-light">
                                        <div class="card-body p-2">
                                            <h6 class="card-title mb-1">人脸 ${index + 1}</h6>
                                            <small class="text-muted">
                                                质量: ${face.quality ? (face.quality * 100).toFixed(1) + '%' : 'N/A'}<br>
                                                ${face.bbox ? `位置: [${face.bbox.map(v => Math.round(v)).join(', ')}]` : ''}
                                            </small>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                ${result.embeddings_count ? `
                    <div class="mt-3 p-2 bg-light rounded">
                        <small class="text-muted">
                            <i class="bi bi-cpu me-1"></i>
                            已提取特征向量 ${result.embeddings_count} 个，特征维度: ${result.feature_dim || 'N/A'}
                        </small>
                    </div>
                ` : ''}
            </div>
        </div>
    `;

    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

/**
 * 加载统计信息（使用重试机制）
 */
async function loadStatistics() {
    try {
        showGlobalSpinner('加载统计数据...');
        
        const response = await fetchWithRetry(`${API_BASE_URL}/statistics`);
        const stats = await response.json();
        
        // 更新统计数据
        document.getElementById('totalPersons').textContent = stats.total_persons || 0;
        document.getElementById('totalEncodings').textContent = stats.total_encodings || 0;
        document.getElementById('tolerance').textContent = stats.system_config?.recognition_threshold?.current?.toFixed(2) || 'N/A';
        document.getElementById('loadedEncodings').textContent = stats.cache_size || 0;
        
        // 更新系统配置部分
        if (stats.system_config) {
            updateSystemConfig(stats.system_config);
        }
        
        showToast('成功', '统计数据加载完成', 'success');
    } catch (error) {
        console.error('加载统计信息错误:', error);
        showToast('警告', '统计信息加载失败，将使用缓存数据', 'warning');
        
        // 设置默认值
        document.getElementById('totalPersons').textContent = '-';
        document.getElementById('totalEncodings').textContent = '-';
        document.getElementById('tolerance').textContent = '-';
        document.getElementById('loadedEncodings').textContent = '-';
    } finally {
        hideGlobalSpinner();
    }
}

/**
 * 更新系统配置显示
 */
function updateSystemConfig(config) {
    const configContainer = document.getElementById('systemConfigContainer');
    if (!configContainer) return;
    
    const threshold = config.recognition_threshold;
    const duplicateThreshold = config.duplicate_threshold || { current: 0.95, min: 0.8, max: 0.99, step: 0.01 };
    const modelInfo = config.model_info;
    const performance = config.performance;
    
    configContainer.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h6 class="card-title mb-0">
                    <i class="bi bi-gear-fill me-2"></i>系统配置
                </h6>
            </div>
            <div class="card-body">
                <!-- 识别阈值设置 -->
                <div class="row mb-3">
                    <label class="col-sm-3 col-form-label">识别阈值:</label>
                    <div class="col-sm-6">
                        <input type="range" class="form-range" id="thresholdSlider" 
                               min="${threshold.min}" max="${threshold.max}" step="${threshold.step}" 
                               value="${threshold.current}">
                    </div>
                    <div class="col-sm-3">
                        <span class="badge bg-primary" id="thresholdDisplay">${(threshold.current * 100).toFixed(0)}%</span>
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-sm-3"></div>
                    <div class="col-sm-9">
                        <small class="text-muted">${threshold.description}</small>
                    </div>
                </div>
                
                <!-- 重复入库阈值设置 -->
                <div class="row mb-3">
                    <label class="col-sm-3 col-form-label">重复阈值:</label>
                    <div class="col-sm-6">
                        <input type="range" class="form-range" id="duplicateThresholdSlider" 
                               min="${duplicateThreshold.min}" max="${duplicateThreshold.max}" step="${duplicateThreshold.step}" 
                               value="${duplicateThreshold.current}">
                    </div>
                    <div class="col-sm-3">
                        <span class="badge bg-warning" id="duplicateThresholdDisplay">${(duplicateThreshold.current * 100).toFixed(0)}%</span>
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-sm-3"></div>
                    <div class="col-sm-9">
                        <small class="text-muted">${duplicateThreshold.description || '防止重复入库：相似度超过此值的人脸将被拒绝入库'}</small>
                    </div>
                </div>
                
                <!-- 模型信息 -->
                <div class="row mb-3">
                    <label class="col-sm-3 col-form-label">识别模型:</label>
                    <div class="col-sm-9">
                        <span class="badge bg-success">${modelInfo.primary}</span>
                        <small class="text-muted ms-2">准确率: ${modelInfo.accuracy}</small>
                    </div>
                </div>
                
                <!-- 性能信息 -->
                <div class="row mb-3">
                    <label class="col-sm-3 col-form-label">处理性能:</label>
                    <div class="col-sm-9">
                        <small class="text-muted">
                            检测速度: ${performance.detection_speed} | 
                            识别速度: ${performance.recognition_speed} | 
                            最大分辨率: ${performance.max_face_size}
                        </small>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-sm-3"></div>
                    <div class="col-sm-9">
                        <button class="btn btn-primary btn-sm me-2" onclick="updateThreshold()">
                            <i class="bi bi-check-lg me-1"></i>保存识别阈值
                        </button>
                        <button class="btn btn-warning btn-sm" onclick="updateDuplicateThreshold()">
                            <i class="bi bi-check-lg me-1"></i>保存重复阈值
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 设置阈值滑块事件
    const slider = document.getElementById('thresholdSlider');
    const display = document.getElementById('thresholdDisplay');
    if (slider && display) {
        slider.addEventListener('input', function() {
            display.textContent = (this.value * 100).toFixed(0) + '%';
        });
    }
    
    // 设置重复阈值滑块事件
    const duplicateSlider = document.getElementById('duplicateThresholdSlider');
    const duplicateDisplay = document.getElementById('duplicateThresholdDisplay');
    if (duplicateSlider && duplicateDisplay) {
        duplicateSlider.addEventListener('input', function() {
            duplicateDisplay.textContent = (this.value * 100).toFixed(0) + '%';
        });
    }
}

/**
 * 更新识别阈值
 */
async function updateThreshold() {
    const slider = document.getElementById('thresholdSlider');
    if (!slider) return;
    
    const newThreshold = parseFloat(slider.value);
    
    try {
        const formData = new FormData();
        formData.append('threshold', newThreshold);
        
        const response = await fetch(`${API_BASE_URL}/config/threshold`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('messagesContainer', `识别阈值已更新为 ${(newThreshold * 100).toFixed(0)}%`);
            loadStatistics(); // 重新加载统计信息
        } else {
            showError('messagesContainer', result.message || '更新阈值失败');
        }
    } catch (error) {
        console.error('更新阈值错误:', error);
        showError('messagesContainer', '更新阈值失败: ' + error.message);
    }
}

/**
 * 更新重复入库阈值
 */
async function updateDuplicateThreshold() {
    const slider = document.getElementById('duplicateThresholdSlider');
    if (!slider) return;
    
    const newThreshold = parseFloat(slider.value);
    
    try {
        const formData = new FormData();
        formData.append('threshold', newThreshold);
        
        const response = await fetch(`${API_BASE_URL}/config/duplicate_threshold`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('messagesContainer', `重复入库阈值已更新为 ${(newThreshold * 100).toFixed(0)}%`);
            loadStatistics(); // 重新加载统计信息
        } else {
            showError('messagesContainer', result.message || '更新重复阈值失败');
        }
    } catch (error) {
        console.error('更新重复阈值错误:', error);
        showError('messagesContainer', '更新重复阈值失败: ' + error.message);
    }
}

/**
 * 加载人员列表
 */
async function loadPersons() {
    const tableBody = document.getElementById('personsTableBody');
    
    try {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">加载中...</td></tr>';
        
        const response = await fetch(`${API_BASE_URL}/persons`);
        const result = await response.json();
        
        if (result.success && result.persons.length > 0) {
            const html = result.persons.map(person => {
                const createdAt = new Date(person.created_at).toLocaleString('zh-CN');
                return `
                    <tr>
                        <td>${person.id}</td>
                        <td>${person.name}</td>
                        <td>${person.description || '-'}</td>
                        <td>
                            <span class="badge bg-info" id="face-count-${person.id}">-</span>
                        </td>
                        <td>${createdAt}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-info me-1" onclick="viewPerson(${person.id})">
                                <i class="bi bi-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deletePerson(${person.id}, '${person.name}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
            
            tableBody.innerHTML = html;
            
            // 异步加载每个人的人脸数量
            result.persons.forEach(async person => {
                try {
                    const personResponse = await fetch(`${API_BASE_URL}/person/${person.id}`);
                    const personResult = await personResponse.json();
                    if (personResult.success) {
                        const faceCount = personResult.person.encoding_count || 0;
                        const badge = document.getElementById(`face-count-${person.id}`);
                        if (badge) {
                            badge.textContent = faceCount;
                        }
                    }
                } catch (error) {
                    console.error(`加载人员${person.id}详情错误:`, error);
                    const badge = document.getElementById(`face-count-${person.id}`);
                    if (badge) {
                        badge.textContent = '0';
                    }
                }
            });
            
        } else {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">暂无数据</td></tr>';
        }
    } catch (error) {
        console.error('加载人员列表错误:', error);
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">加载失败</td></tr>';
    }
}

/**
 * 查看人员详情
 */
async function viewPerson(personId) {
    try {
        // 获取或创建模态框实例（避免重复创建）
        const modalElement = document.getElementById('personDetailModal');
        let modal = bootstrap.Modal.getInstance(modalElement);
        if (!modal) {
            modal = new bootstrap.Modal(modalElement);
        }
        
        const modalTitle = document.getElementById('personDetailModalTitle');
        const modalBody = document.getElementById('personDetailModalBody');
        
        modalTitle.textContent = '加载中...';
        modalBody.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
        modal.show();
        
        await loadPersonDetails(personId, modalTitle, modalBody);
        
    } catch (error) {
        console.error('查看人员详情错误:', error);
        const modalElement = document.getElementById('personDetailModal');
        if (modalElement) {
            document.getElementById('personDetailModalTitle').textContent = '错误';
            document.getElementById('personDetailModalBody').innerHTML = '<div class="alert alert-danger">获取人员详情时发生错误</div>';
        }
    }
}

/**
 * 刷新人员模态框内容（不重新创建模态框）
 */
async function refreshPersonModal(personId) {
    try {
        const modalTitle = document.getElementById('personDetailModalTitle');
        const modalBody = document.getElementById('personDetailModalBody');
        
        // 显示加载状态
        modalTitle.textContent = '刷新中...';
        modalBody.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
        
        await loadPersonDetails(personId, modalTitle, modalBody);
        
    } catch (error) {
        console.error('刷新人员详情错误:', error);
        const modalTitle = document.getElementById('personDetailModalTitle');
        const modalBody = document.getElementById('personDetailModalBody');
        modalTitle.textContent = '错误';
        modalBody.innerHTML = '<div class="alert alert-danger">刷新人员详情时发生错误</div>';
    }
}

/**
 * 加载人员详情内容
 */
async function loadPersonDetails(personId, modalTitle, modalBody) {
    const response = await fetch(`${API_BASE_URL}/person/${personId}`);
    const result = await response.json();
    
    if (result.success) {
        const person = result.person;
        modalTitle.textContent = `人员详情 - ${person.name}`;
        
        // 获取人脸编码详情
        const facesResponse = await fetch(`${API_BASE_URL}/person/${personId}/faces`);
        let faceEncodings = [];
        if (facesResponse.ok) {
            const facesResult = await facesResponse.json();
            faceEncodings = facesResult.face_encodings || [];
        }
        
        let html = `
            <div class="row">
                <div class="col-md-6">
                    <h6><i class="bi bi-person me-2"></i>基本信息</h6>
                    <table class="table table-sm">
                        <tr><td><strong>姓名:</strong></td><td>${person.name}</td></tr>
                        <tr><td><strong>描述:</strong></td><td>${person.description || '无'}</td></tr>
                        <tr><td><strong>人脸数量:</strong></td><td>${person.encoding_count || 0}</td></tr>
                        <tr><td><strong>创建时间:</strong></td><td>${new Date(person.created_at).toLocaleString('zh-CN')}</td></tr>
                        <tr><td><strong>更新时间:</strong></td><td>${new Date(person.updated_at).toLocaleString('zh-CN')}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6><i class="bi bi-images me-2"></i>人脸图片</h6>
                    <div class="row" id="faceImagesContainer">
        `;
        
        if (faceEncodings.length > 0) {
            faceEncodings.forEach((face, index) => {
                html += `
                    <div class="col-6 mb-3">
                        <div class="card border-light">
                            <img src="${API_BASE_URL}/face_image/${face.id}" 
                                 class="card-img-top" 
                                 style="height: 120px; object-fit: cover; cursor: pointer;"
                                 alt="人脸 ${index + 1}"
                                 onclick="showImageModal('${API_BASE_URL}/face_image/${face.id}', '${person.name} - 人脸 ${index + 1}')"
                                 onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2YwZjBmMCIvPjx0ZXh0IHg9IjUwIiB5PSI1NSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjNjY2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj7ml6Dlm77niYc8L3RleHQ+PC9zdmc+'">
                            <div class="card-body p-2">
                                <small class="text-muted">
                                    质量: ${face.quality_score ? (face.quality_score * 100).toFixed(1) + '%' : 'N/A'}<br>
                                    置信度: ${face.confidence ? (face.confidence * 100).toFixed(1) + '%' : 'N/A'}
                                </small>
                                <div class="mt-1">
                                    <button class="btn btn-outline-primary btn-sm me-1" 
                                            onclick="showImageModal('${API_BASE_URL}/face_image/${face.id}', '${person.name} - 人脸 ${index + 1}')"
                                            title="查看大图">
                                        <i class="bi bi-zoom-in"></i>
                                    </button>
                                    <button class="btn btn-outline-danger btn-sm" 
                                            onclick="deleteFaceEncoding(${face.id}, ${personId})"
                                            title="删除此人脸">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
        } else {
            html += `
                <div class="col-12">
                    <div class="text-center text-muted">
                        <i class="bi bi-image fs-1"></i>
                        <p class="mt-2">暂无人脸图片</p>
                    </div>
                </div>
            `;
        }
        
        html += `
                    </div>
                </div>
            </div>
        `;
        
        modalBody.innerHTML = html;
    } else {
        modalTitle.textContent = '错误';
        modalBody.innerHTML = '<div class="alert alert-danger">获取人员详情失败</div>';
    }
}

/**
 * 删除人员
 */
async function deletePerson(personId, personName) {
    if (!confirm(`确定要删除人员 "${personName}" 吗？此操作将删除该人员的所有人脸特征数据，且不可恢复。`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/person/${personId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('成功', `人员 "${personName}" 已删除`, 'success');
            loadPersons(); // 刷新列表
            loadStatistics(); // 刷新统计
        } else {
            showToast('错误', result.message, 'error');
        }
    } catch (error) {
        console.error('删除人员错误:', error);
        showToast('错误', '删除人员时发生错误', 'error');
    }
}

/**
 * 删除人脸编码
 */
async function deleteFaceEncoding(encodingId, personId) {
    if (!confirm('确定要删除这个人脸特征吗？此操作不可恢复。')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/face_encoding/${encodingId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('成功', '人脸特征已删除', 'success');
            // 刷新人员详情模态框内容，但不重新创建模态框
            await refreshPersonModal(personId);
            // 刷新人员列表和统计
            loadPersons();
            loadStatistics();
        } else {
            showToast('错误', result.message || '删除人脸特征失败', 'error');
        }
    } catch (error) {
        console.error('删除人脸特征错误:', error);
        showToast('错误', '删除人脸特征时发生错误', 'error');
    }
}

/**
 * 加载配置
 */
async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/config`);
        const result = await response.json();
        
        if (result.success) {
            // 配置已移至识别页面，这里不需要处理
        }
    } catch (error) {
        console.error('加载配置错误:', error);
    }
}

/**
 * 更新配置
 */
async function updateConfig(e) {
    e.preventDefault();
    // 配置已移至识别页面，这里不需要处理
    showToast('提示', '阈值设置已移至人脸识别页面', 'info');
}

/**
 * 设置按钮加载状态
 */
function setButtonLoading(button, loading) {
    const spinner = button.querySelector('.loading-spinner');
    const icon = button.querySelector('i:not(.loading-spinner i)');
    
    if (loading) {
        button.disabled = true;
        spinner.style.display = 'inline-block';
        if (icon) icon.style.display = 'none';
    } else {
        button.disabled = false;
        spinner.style.display = 'none';
        if (icon) icon.style.display = 'inline';
    }
}

/**
 * 显示Toast通知
 */
function showToast(title, message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastTitle = document.getElementById('toastTitle');
    const toastBody = document.getElementById('toastBody');
    
    // 设置样式
    toast.className = 'toast';
    if (type === 'success') {
        toast.classList.add('bg-success', 'text-white');
    } else if (type === 'error') {
        toast.classList.add('bg-danger', 'text-white');
    } else if (type === 'warning') {
        toast.classList.add('bg-warning');
    } else {
        toast.classList.add('bg-info', 'text-white');
    }
    
    toastTitle.textContent = title;
    toastBody.textContent = message;
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// 系统状态管理
function initSystemStatus() {
    const statusElement = document.getElementById('systemStatus');
    
    // 网络状态检测
    function updateNetworkStatus() {
        if (navigator.onLine) {
            statusElement.className = 'badge bg-success';
            statusElement.innerHTML = '<i class="bi bi-wifi me-1"></i>在线';
        } else {
            statusElement.className = 'badge bg-danger';
            statusElement.innerHTML = '<i class="bi bi-wifi-off me-1"></i>离线';
        }
    }
    
    // 定期检查服务器连接
    async function checkServerHealth() {
        try {
            const response = await fetch('/api/health', { 
                method: 'HEAD',
                signal: AbortSignal.timeout(5000)
            });
            
            if (response.ok) {
                statusElement.className = 'badge bg-success';
                statusElement.innerHTML = '<i class="bi bi-wifi me-1"></i>在线';
            } else {
                statusElement.className = 'badge bg-warning';
                statusElement.innerHTML = '<i class="bi bi-exclamation-triangle me-1"></i>异常';
            }
        } catch (error) {
            statusElement.className = 'badge bg-danger';
            statusElement.innerHTML = '<i class="bi bi-x-circle me-1"></i>连接失败';
        }
    }
    
    // 监听网络状态变化
    window.addEventListener('online', updateNetworkStatus);
    window.addEventListener('offline', updateNetworkStatus);
    
    // 初始化状态
    updateNetworkStatus();
    
    // 定期检查服务器健康状态
    checkServerHealth();
    setInterval(checkServerHealth, 30000); // 每30秒检查一次
}

// 初始化系统增强功能
document.addEventListener('DOMContentLoaded', function() {
    initApp();
    initSystemStatus();
});

/**
 * 显示图片放大模态框
 */
function showImageModal(imageSrc, title) {
    const modal = document.getElementById('imageModal');
    const modalTitle = document.getElementById('imageModalTitle');
    const modalImg = document.getElementById('imageModalImg');
    
    modalTitle.textContent = title || '图片查看';
    modalImg.src = imageSrc;
    modalImg.alt = title || '放大图片';
    
    // 存储当前图片信息，用于下载功能
    modal.setAttribute('data-image-src', imageSrc);
    modal.setAttribute('data-image-title', title || 'image');
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

/**
 * 下载图片功能
 */
async function downloadImage() {
    const modal = document.getElementById('imageModal');
    const imageSrc = modal.getAttribute('data-image-src');
    const imageTitle = modal.getAttribute('data-image-title');
    
    if (!imageSrc) {
        showToast('错误', '无法获取图片信息', 'error');
        return;
    }
    
    try {
        showToast('提示', '正在下载图片...', 'info');
        
        // 获取图片数据
        const response = await fetch(imageSrc);
        if (!response.ok) {
            throw new Error('图片下载失败');
        }
        
        const blob = await response.blob();
        
        // 创建下载链接
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        // 生成文件名
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const extension = blob.type.split('/')[1] || 'jpg';
        a.download = `${imageTitle.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}_${timestamp}.${extension}`;
        
        document.body.appendChild(a);
        a.click();
        
        // 清理
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast('成功', '图片下载完成', 'success');
    } catch (error) {
        console.error('下载图片错误:', error);
        showToast('错误', '图片下载失败: ' + error.message, 'error');
    }
}

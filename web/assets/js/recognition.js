// 人脸识别模块
class FaceRecognition {
    constructor() {
        this.currentFile = null;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // 上传区域
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('imageFile');
        const recognizeBtn = document.getElementById('recognizeBtn');

        if (uploadZone && fileInput) {
            // 点击上传
            uploadZone.addEventListener('click', () => fileInput.click());
            
            // 文件选择
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFile(e.target.files[0]);
                }
            });

            // 拖拽上传
            DragDropHandler.init(uploadZone, (files) => {
                if (files.length > 0) {
                    this.handleFile(files[0]);
                }
            });
        }

        // 识别按钮
        if (recognizeBtn) {
            recognizeBtn.addEventListener('click', () => this.performRecognition());
        }

        // 重置按钮
        const resetBtn = document.querySelector('[onclick="clearRecognition()"]');
        if (resetBtn) {
            resetBtn.onclick = () => this.clearRecognition();
        }
    }

    handleFile(file) {
        const validation = FileValidator.validate(file);
        
        if (!validation.valid) {
            validation.errors.forEach(error => {
                ToastManager.show(error, 'error');
            });
            return;
        }

        this.currentFile = file;
        this.showPreview(file);
        this.enableRecognitionButton();
        this.showFileInfo(file);
    }

    showPreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = document.getElementById('previewImg');
            const preview = document.getElementById('imagePreview');
            
            if (img && preview) {
                img.src = e.target.result;
                preview.style.display = 'block';
                
                // 添加淡入动画
                preview.classList.add('fade-in');
            }
        };
        reader.readAsDataURL(file);
    }

    showFileInfo(file) {
        const infoDiv = document.getElementById('imageInfo');
        if (infoDiv) {
            const fileSize = (file.size / 1024 / 1024).toFixed(2);
            infoDiv.innerHTML = `
                <i class="bi bi-info-circle me-1"></i>
                文件名: ${file.name} | 
                大小: ${fileSize} MB | 
                类型: ${file.type}
            `;
        }
    }

    enableRecognitionButton() {
        const btn = document.getElementById('recognizeBtn');
        const clearBtn = document.getElementById('clearBtn');
        if (btn) {
            btn.disabled = false;
        }
        if (clearBtn) {
            clearBtn.style.display = 'block';
        }
    }

    async performRecognition() {
        if (!this.currentFile) {
            ToastManager.show('请先选择图片', 'warning');
            return;
        }

        const btn = document.getElementById('recognizeBtn');
        const loadingOverlay = document.getElementById('recognitionLoading');
        
        // 显示加载状态
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
        }
        
        LoadingManager.setButtonLoading(btn, true, '识别中...');

        try {
            const formData = new FormData();
            formData.append('file', this.currentFile);

            // 首先获取识别结果
            const result = await ApiClient.post('/api/recognize', formData);
            
            // 然后获取可视化图片
            const visualResponse = await fetch('/api/recognize_visual', {
                method: 'POST',
                body: formData
            });
            
            if (visualResponse.ok) {
                const blob = await visualResponse.blob();
                const visualUrl = URL.createObjectURL(blob);
                this.displayResults(result, visualUrl);
            } else {
                this.displayResults(result);
            }
            
            ToastManager.show('识别完成', 'success');
            this.showDownloadButton();

        } catch (error) {
            console.error('Recognition error:', error);
            ToastManager.show(`识别失败: ${error.message}`, 'error');
            this.displayError('识别失败，请重试');
        } finally {
            LoadingManager.setButtonLoading(btn, false);
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }
    }

    showDownloadButton() {
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.style.display = 'block';
        }
    }

    displayResults(result, visualUrl = null) {
        const container = document.getElementById('recognitionResults');
        if (!container) return;

        let resultsHtml = '';
        
        // 如果有可视化图片，先显示
        if (visualUrl) {
            resultsHtml += `
                <div class="mb-4">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="text-primary mb-0">
                            <i class="bi bi-image me-2"></i>识别可视化结果
                        </h6>
                        <button class="btn btn-outline-primary btn-sm" onclick="downloadVisualization('${visualUrl}')">
                            <i class="bi bi-download me-1"></i>下载
                        </button>
                    </div>
                    <div class="text-center">
                        <img src="${visualUrl}" class="img-fluid rounded shadow" alt="识别结果可视化" style="max-height: 350px; cursor: pointer;" onclick="showImageModal('${visualUrl}')">
                        <div class="small text-muted mt-2">点击图片查看大图</div>
                    </div>
                </div>
            `;
        }

        // 显示识别结果详情
        if (result.matches && result.matches.length > 0) {
            resultsHtml += `
                <div class="mb-3">
                    <h6 class="text-success mb-3">
                        <i class="bi bi-person-check me-2"></i>识别成功 - 找到 ${result.matches.length} 个匹配
                    </h6>
                    <div class="row">
                        ${result.matches.map((match, index) => `
                            <div class="col-12 mb-3">
                                ${this.createResultCard(match, index + 1)}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;

            // 显示总结信息
            resultsHtml += `
                <div class="alert alert-info">
                    <div class="row text-center">
                        <div class="col-4">
                            <div class="fw-bold">${result.total_faces || 1}</div>
                            <div class="small">检测人脸</div>
                        </div>
                        <div class="col-4">
                            <div class="fw-bold">${result.matches.length}</div>
                            <div class="small">匹配人员</div>
                        </div>
                        <div class="col-4">
                            <div class="fw-bold">${Math.max(...result.matches.map(m => m.match_score)).toFixed(1)}%</div>
                            <div class="small">最高相似度</div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            resultsHtml += `
                <div class="alert alert-warning text-center">
                    <i class="bi bi-exclamation-triangle fs-1 text-warning mb-3"></i>
                    <h5 class="mb-2">未找到匹配的人员</h5>
                    <p class="mb-3">该人脸在数据库中没有匹配记录</p>
                    <div class="d-grid gap-2">
                        <button class="btn btn-primary" onclick="showEnrollmentModal()">
                            <i class="bi bi-person-plus me-2"></i>注册此人员
                        </button>
                        <small class="text-muted">建议检查照片质量或先注册该人员</small>
                    </div>
                </div>
            `;
        }

        container.innerHTML = resultsHtml;
        container.classList.add('fade-in');
    }

    createResultCard(match, index) {
        const scoreClass = this.getScoreClass(match.match_score);
        return `
            <div class="result-card">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div class="d-flex align-items-center">
                        <div class="badge bg-primary me-2">#${index}</div>
                        <div>
                            <h6 class="mb-1 text-primary fw-bold">${match.name}</h6>
                            <small class="text-muted">人员ID: ${match.person_id}${match.face_encoding_id ? ` | 人脸ID: ${match.face_encoding_id}` : ''}</small>
                        </div>
                    </div>
                    <span class="match-score ${scoreClass}">
                        ${match.match_score.toFixed(1)}%
                    </span>
                </div>
                
                <div class="row g-3 text-sm">
                    <div class="col-md-6">
                        <div class="d-flex justify-content-between">
                            <span class="text-muted">相似度距离:</span>
                            <span class="fw-semibold">${match.distance.toFixed(4)}</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="d-flex justify-content-between">
                            <span class="text-muted">图像质量:</span>
                            <span class="fw-semibold">${((match.quality || 0) * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="d-flex justify-content-between">
                            <span class="text-muted">识别模型:</span>
                            <span class="fw-semibold">${match.model}</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="d-flex justify-content-between">
                            <span class="text-muted">检测框:</span>
                            <span class="fw-semibold">${match.bbox ? `${match.bbox[2]-match.bbox[0]}×${match.bbox[3]-match.bbox[1]}` : 'N/A'}</span>
                        </div>
                    </div>
                    ${match.age ? `
                        <div class="col-md-6">
                            <div class="d-flex justify-content-between">
                                <span class="text-muted">预估年龄:</span>
                                <span class="fw-semibold">${match.age}岁</span>
                            </div>
                        </div>
                    ` : ''}
                    ${match.gender ? `
                        <div class="col-md-6">
                            <div class="d-flex justify-content-between">
                                <span class="text-muted">性别:</span>
                                <span class="fw-semibold">${match.gender}</span>
                            </div>
                        </div>
                    ` : ''}
                </div>
                
                <div class="mt-3">
                    <div class="progress" style="height: 8px;">
                        <div class="progress-bar ${this.getProgressBarClass(match.match_score)}" 
                             style="width: ${match.match_score}%"></div>
                    </div>
                    <div class="d-flex justify-content-between mt-1">
                        <small class="text-muted">置信度</small>
                        <small class="text-muted">${this.getConfidenceText(match.match_score)}</small>
                    </div>
                </div>
            </div>
        `;
    }

    getScoreClass(score) {
        if (score >= 80) return 'match-high';
        if (score >= 60) return 'match-medium';
        return 'match-low';
    }

    getProgressBarClass(score) {
        if (score >= 80) return 'bg-success';
        if (score >= 60) return 'bg-warning';
        return 'bg-danger';
    }

    getConfidenceText(score) {
        if (score >= 90) return '非常高';
        if (score >= 80) return '高';
        if (score >= 60) return '中等';
        if (score >= 40) return '较低';
        return '低';
    }

    displayError(message) {
        const container = document.getElementById('recognitionResults');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    ${message}
                </div>
            `;
        }
    }

    clearRecognition() {
        this.currentFile = null;
        
        const fileInput = document.getElementById('imageFile');
        const preview = document.getElementById('imagePreview');
        const btn = document.getElementById('recognizeBtn');
        const clearBtn = document.getElementById('clearBtn');
        const downloadBtn = document.getElementById('downloadBtn');
        const results = document.getElementById('recognitionResults');
        const imageInfo = document.getElementById('imageInfo');

        if (fileInput) fileInput.value = '';
        if (preview) preview.style.display = 'none';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-search me-2"></i>开始识别';
        }
        if (clearBtn) clearBtn.style.display = 'none';
        if (downloadBtn) downloadBtn.style.display = 'none';
        if (imageInfo) imageInfo.innerHTML = '';
        
        if (results) {
            results.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-search"></i>
                    <h6>等待识别</h6>
                    <p class="mb-0">请上传照片开始识别</p>
                </div>
            `;
        }

        ToastManager.show('已重置识别界面', 'info');
    }
}

// 导出到全局作用域
window.FaceRecognition = FaceRecognition;

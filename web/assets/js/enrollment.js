// 人员注册模块
class PersonEnrollment {
    constructor() {
        this.enrollmentFiles = [];
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // 上传区域
        const uploadZone = document.getElementById('enrollmentUpload');
        const fileInput = document.getElementById('enrollmentFile');
        const enrollBtn = document.getElementById('enrollBtn');

        if (uploadZone && fileInput) {
            // 点击上传
            uploadZone.addEventListener('click', () => fileInput.click());
            
            // 文件选择
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFiles(e.target.files);
                }
            });

            // 拖拽上传
            DragDropHandler.init(uploadZone, (files) => {
                this.handleFiles(files);
            });
        }

        // 注册按钮
        if (enrollBtn) {
            enrollBtn.addEventListener('click', () => this.performEnrollment());
        }

        // 表单验证
        const nameInput = document.getElementById('personName');
        if (nameInput) {
            nameInput.addEventListener('input', () => this.updateEnrollmentButton());
        }

        // 重置按钮
        const resetBtn = document.querySelector('[onclick="clearEnrollment()"]');
        if (resetBtn) {
            resetBtn.onclick = () => this.clearEnrollment();
        }
    }

    handleFiles(files) {
        const validation = FileValidator.validateMultiple(files);
        
        if (validation.hasErrors) {
            validation.errors.forEach(error => {
                ToastManager.show(error, 'error');
            });
        }

        if (validation.validFiles.length > 0) {
            this.enrollmentFiles = validation.validFiles;
            this.showPreviews(validation.validFiles);
            this.updateEnrollmentButton();
            
            // 如果是单张图片且姓名为空，自动从文件名提取
            if (validation.validFiles.length === 1) {
                const nameInput = document.getElementById('personName');
                if (nameInput && !nameInput.value.trim()) {
                    const fileName = validation.validFiles[0].name;
                    const nameFromFile = fileName.replace(/\.(jpg|jpeg|png|gif|bmp|webp|avif)$/i, '')
                                                .replace(/[_-]/g, ' ')
                                                .trim();
                    if (nameFromFile) {
                        nameInput.value = nameFromFile;
                        ToastManager.show(`已从文件名自动填入姓名：${nameFromFile}`, 'info');
                        this.updateEnrollmentButton();
                    }
                }
            }
        }
    }

    async showPreviews(files) {
        const container = document.getElementById('enrollmentImages');
        const preview = document.getElementById('enrollmentPreview');
        
        if (!container || !preview) return;

        ImagePreview.clear(container);
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const col = document.createElement('div');
            col.className = 'col-md-4 col-sm-6 mb-3';
            
            try {
                await ImagePreview.createPreview(file, col, {
                    maxHeight: '150px',
                    className: 'img-fluid image-preview w-100',
                    onRemove: (element, file) => this.removeImage(element, file)
                });
                container.appendChild(col);
            } catch (error) {
                console.error('Preview error:', error);
                ToastManager.show('图片预览失败', 'error');
            }
        }
        
        preview.classList.remove('d-none');
    }

    removeImage(element, file) {
        // 从文件列表中移除
        const index = this.enrollmentFiles.indexOf(file);
        if (index > -1) {
            this.enrollmentFiles.splice(index, 1);
        }
        
        // 移除DOM元素
        element.remove();
        
        // 如果没有文件了，隐藏预览区域
        if (this.enrollmentFiles.length === 0) {
            const preview = document.getElementById('enrollmentPreview');
            if (preview) {
                preview.classList.add('d-none');
            }
            
            // 重置文件输入
            const fileInput = document.getElementById('enrollmentFile');
            if (fileInput) {
                fileInput.value = '';
            }
        }
        
        this.updateEnrollmentButton();
    }

    updateEnrollmentButton() {
        const btn = document.getElementById('enrollBtn');
        const nameInput = document.getElementById('personName');
        
        if (btn && nameInput) {
            const hasName = nameInput.value.trim().length > 0;
            const hasFiles = this.enrollmentFiles.length > 0;
            
            // 如果有多张照片，只要有文件就可以执行批量入库（不强制要求名称）
            if (this.enrollmentFiles.length > 1) {
                btn.disabled = !hasFiles;
                btn.textContent = `批量注册 (${this.enrollmentFiles.length}张)`;
            } else if (this.enrollmentFiles.length === 1) {
                // 单张照片：有文件即可，如果没有姓名会从文件名提取
                btn.disabled = !hasFiles;
                btn.textContent = hasName ? '注册人员' : '注册人员 (使用文件名)';
            } else {
                btn.disabled = true;
                btn.textContent = '注册人员';
            }
        }
    }

    async performEnrollment() {
        const nameInput = document.getElementById('personName');
        const descInput = document.getElementById('personDescription');
        
        if (!nameInput) {
            ToastManager.show('页面元素缺失', 'error');
            return;
        }

        const name = nameInput.value.trim();
        const description = descInput ? descInput.value.trim() : '';

        if (this.enrollmentFiles.length === 0) {
            ToastManager.show('请上传至少一张照片', 'warning');
            return;
        }

        const btn = document.getElementById('enrollBtn');

        try {
            if (this.enrollmentFiles.length === 1) {
                // 单张照片注册
                let finalName = name;
                
                // 如果姓名为空，从文件名提取
                if (!finalName) {
                    const fileName = this.enrollmentFiles[0].name;
                    finalName = fileName.replace(/\.(jpg|jpeg|png|gif|bmp|webp|avif)$/i, '')
                                       .replace(/[_-]/g, ' ')
                                       .trim();
                    if (!finalName) {
                        ToastManager.show('无法从文件名提取姓名，请手动输入', 'warning');
                        nameInput.focus();
                        return;
                    }
                }

                LoadingManager.setButtonLoading(btn, true, '注册中...');

                const formData = new FormData();
                formData.append('name', finalName);
                if (description) formData.append('description', description);
                formData.append('file', this.enrollmentFiles[0]);

                const result = await ApiClient.post('/api/enroll', formData);
                this.displayResults(result);
                ToastManager.show('人员注册成功', 'success');
            } else {
                // 批量注册
                LoadingManager.setButtonLoading(btn, true, `批量注册中 (${this.enrollmentFiles.length}张)...`);

                const formData = new FormData();
                
                // 添加所有文件
                this.enrollmentFiles.forEach((file, index) => {
                    formData.append('files', file);
                });

                // 如果填写了名称，所有文件都将使用这个名称
                // 如果没有填写名称，每个文件将使用各自的文件名作为姓名
                if (name) {
                    formData.append('names', name);
                }

                // 如果填写了描述，则使用该描述作为第一个文件的描述
                if (description) {
                    formData.append('descriptions', description);
                }

                const result = await ApiClient.post('/api/batch_enroll', formData);
                this.displayBatchResults(result);
                
                if (result.success && result.success_count > 0) {
                    ToastManager.show(`批量注册完成：成功 ${result.success_count} 个，失败 ${result.error_count} 个`, 
                        result.error_count === 0 ? 'success' : 'warning');
                } else {
                    ToastManager.show('批量注册失败', 'error');
                }
            }

        } catch (error) {
            console.error('Enrollment error:', error);
            ToastManager.show(`注册失败: ${error.message}`, 'error');
            this.displayError(error.message);
        } finally {
            LoadingManager.setButtonLoading(btn, false);
            // 恢复按钮文本
            if (this.enrollmentFiles.length > 1) {
                btn.textContent = `批量注册 (${this.enrollmentFiles.length}张)`;
            } else {
                btn.textContent = '注册人员';
            }
        }
    }

    displayBatchResults(result) {
        const container = document.getElementById('enrollmentResults');
        if (!container) return;

        if (result.success) {
            let html = `
                <div class="alert alert-${result.error_count === 0 ? 'success' : 'warning'}">
                    <i class="bi bi-${result.error_count === 0 ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
                    <strong>批量注册完成</strong>
                    <br>总计 ${result.total_files} 个文件，成功 ${result.success_count} 个，失败 ${result.error_count} 个
                    <br><small class="text-muted">💡 系统已自动按文件名排序处理，确保数据顺序一致性</small>
                </div>
            `;

            if (result.results && result.results.length > 0) {
                html += `<div class="mt-3"><h6 class="mb-2">详细结果：</h6><div class="row">`;
                
                result.results.forEach((item, index) => {
                    const statusClass = item.success ? 'success' : 'danger';
                    const statusIcon = item.success ? 'check-circle-fill' : 'x-circle-fill';
                    
                    // 检查文件名和人员名是否匹配（用于突出显示）
                    const fileBaseName = item.file_name ? item.file_name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ') : '';
                    const isMatching = item.name && fileBaseName.toLowerCase().includes(item.name.toLowerCase().replace(' ', ''));
                    const matchIcon = isMatching ? '<i class="bi bi-link-45deg text-success ms-1" title="文件名与人员名匹配"></i>' : '';
                    
                    html += `
                        <div class="col-12 mb-2">
                            <div class="card border-${statusClass}">
                                <div class="card-body p-2">
                                    <div class="d-flex align-items-center">
                                        <i class="bi bi-${statusIcon} text-${statusClass} me-2"></i>
                                        <div class="flex-grow-1">
                                            <div class="fw-bold">
                                                📁 ${item.file_name} ${matchIcon}
                                            </div>
                                            <div class="small text-muted">
                                                ${item.name ? `👤 姓名: <strong>${item.name}</strong>` : ''}
                                                ${item.success ? 
                                                    `${item.person_id ? ` | 🆔 ID: ${item.person_id}` : ''}${item.quality_score ? ` | 📊 质量: ${(item.quality_score * 100).toFixed(1)}%` : ''}` :
                                                    ` | ❌ 错误: ${item.error}`
                                                }
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                html += `</div></div>`;
            }

            html += `
                <div class="small text-muted mt-3">
                    <div><strong>处理时间:</strong> ${new Date().toLocaleString()}</div>
                    <div><strong>状态:</strong> ${result.message}</div>
                </div>
            `;

            container.innerHTML = html;
        } else {
            this.displayError(result.error || '批量注册失败');
        }
    }

    displayResults(result) {
        const container = document.getElementById('enrollmentResults');
        if (!container) return;

        if (result.success) {
            // 从API结果中获取正确的人脸数量
            const facesDetected = result.faces_detected || 1;
            const faceQuality = result.face_quality ? (result.face_quality * 100).toFixed(1) : 'N/A';
            
            container.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle me-2"></i>
                    <strong>注册成功！</strong>
                    <br>成功注册 ${facesDetected} 张人脸${result.face_quality ? `，质量评分: ${faceQuality}%` : ''}
                </div>
                <div class="small text-muted mt-2">
                    <div><strong>人员ID:</strong> ${result.person_id}</div>
                    ${result.face_encoding_id ? `<div><strong>人脸ID:</strong> ${result.face_encoding_id}</div>` : ''}
                    <div><strong>姓名:</strong> ${result.person_name || result.name}</div>
                    ${result.description ? `<div><strong>描述:</strong> ${result.description}</div>` : ''}
                    <div><strong>处理时间:</strong> ${result.processing_time ? (result.processing_time * 1000).toFixed(0) + 'ms' : 'N/A'}</div>
                    <div><strong>注册时间:</strong> ${new Date().toLocaleString()}</div>
                </div>
                ${result.visualized_image ? `
                    <div class="mt-3">
                        <h6 class="small text-muted mb-2">人脸检测结果:</h6>
                        <img src="data:image/jpeg;base64,${result.visualized_image}" 
                             class="img-fluid rounded border" 
                             style="max-height: 200px;" 
                             alt="人脸检测可视化">
                    </div>
                ` : ''}
            `;
        } else {
            this.displayError(result.error || '注册失败');
        }
    }

    displayError(message) {
        const container = document.getElementById('enrollmentResults');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    <strong>注册失败</strong>
                    <br><small>${message}</small>
                </div>
            `;
        }
    }

    clearEnrollment() {
        this.enrollmentFiles = [];
        
        const fileInput = document.getElementById('enrollmentFile');
        const preview = document.getElementById('enrollmentPreview');
        const nameInput = document.getElementById('personName');
        const descInput = document.getElementById('personDescription');
        const btn = document.getElementById('enrollBtn');
        const results = document.getElementById('enrollmentResults');

        if (fileInput) fileInput.value = '';
        if (preview) preview.classList.add('d-none');
        if (nameInput) nameInput.value = '';
        if (descInput) descInput.value = '';
        if (btn) {
            btn.disabled = true;
            btn.textContent = '注册人员';
        }
        
        if (results) {
            results.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-person-plus"></i>
                    <h6>等待注册信息</h6>
                    <p class="mb-0">请上传照片并填写信息</p>
                </div>
            `;
        }
    }
}

// 导出到全局作用域
window.PersonEnrollment = PersonEnrollment;

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
            btn.disabled = !hasName || !hasFiles;
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

        if (!name) {
            ToastManager.show('请输入人员姓名', 'warning');
            nameInput.focus();
            return;
        }

        if (this.enrollmentFiles.length === 0) {
            ToastManager.show('请上传至少一张照片', 'warning');
            return;
        }

        const btn = document.getElementById('enrollBtn');
        LoadingManager.setButtonLoading(btn, true, '注册中...');

        try {
            if (this.enrollmentFiles.length === 1) {
                // 单张照片，直接注册
                const formData = new FormData();
                formData.append('name', name);
                if (description) formData.append('description', description);
                formData.append('file', this.enrollmentFiles[0]);

                const result = await ApiClient.post('/api/enroll', formData);
                this.displayResults(result);
                ToastManager.show('人员注册成功', 'success');
            } else {
                // 多张照片，提示用户一次只能注册一张
                ToastManager.show(`检测到 ${this.enrollmentFiles.length} 张照片，目前每次只能注册一张照片。请选择最清晰的一张照片进行注册，注册后可在人员管理中添加更多照片。`, 'warning');
                return;
            }
            
            // 3秒后清空表单
            setTimeout(() => this.clearEnrollment(), 3000);

        } catch (error) {
            console.error('Enrollment error:', error);
            ToastManager.show(`注册失败: ${error.message}`, 'error');
            this.displayError(error.message);
        } finally {
            LoadingManager.setButtonLoading(btn, false);
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
        if (btn) btn.disabled = true;
        
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

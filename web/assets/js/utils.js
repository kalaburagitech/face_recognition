// 全局配置和常量
const CONFIG = {
    API_BASE: '',
    SUPPORTED_IMAGE_TYPES: [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
        'image/webp', 'image/bmp', 'image/tiff', 'image/avif',
        'image/svg+xml', 'image/x-icon', 'image/heic', 'image/heif'
    ],
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    TOAST_DURATION: {
        success: 3000,
        error: 5000,
        warning: 4000,
        info: 3000
    }
};

// API 调用封装
class ApiClient {
    static async get(endpoint) {
        try {
            const response = await fetch(`${CONFIG.API_BASE}${endpoint}`);
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`GET ${endpoint} failed:`, error);
            throw error;
        }
    }

    static async post(endpoint, data) {
        try {
            const options = {
                method: 'POST'
            };

            if (data instanceof FormData) {
                options.body = data;
            } else {
                options.headers = { 'Content-Type': 'application/json' };
                options.body = JSON.stringify(data);
            }

            const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, options);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`POST ${endpoint} failed:`, error);
            throw error;
        }
    }

    static async delete(endpoint) {
        try {
            const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
            
            return response.status === 204 ? null : await response.json();
        } catch (error) {
            console.error(`DELETE ${endpoint} failed:`, error);
            throw error;
        }
    }
}

// 文件验证工具
class FileValidator {
    static validate(file) {
        const errors = [];

        // 检查文件类型
        if (!CONFIG.SUPPORTED_IMAGE_TYPES.includes(file.type)) {
            errors.push(`不支持的文件格式: ${file.type}`);
        }

        // 检查文件大小
        if (file.size > CONFIG.MAX_FILE_SIZE) {
            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            const maxSizeMB = (CONFIG.MAX_FILE_SIZE / (1024 * 1024)).toFixed(0);
            errors.push(`文件过大: ${sizeMB}MB，最大支持 ${maxSizeMB}MB`);
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    static validateMultiple(files) {
        const results = Array.from(files).map(file => ({
            file,
            ...this.validate(file)
        }));

        const validFiles = results.filter(r => r.valid).map(r => r.file);
        const allErrors = results.filter(r => !r.valid).flatMap(r => r.errors);

        return {
            validFiles,
            errors: allErrors,
            hasErrors: allErrors.length > 0
        };
    }
}

// Toast 通知系统
class ToastManager {
    static container = null;

    static init() {
        if (!this.container) {
            this.container = document.getElementById('toastContainer');
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.id = 'toastContainer';
                this.container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
                document.body.appendChild(this.container);
            }
        }
    }

    static show(message, type = 'info') {
        this.init();
        
        const toastId = `toast-${Date.now()}`;
        const bgClass = this.getBgClass(type);
        const icon = this.getIcon(type);
        
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-white ${bgClass} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${icon} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        this.container.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: CONFIG.TOAST_DURATION[type] || 3000
        });
        
        bsToast.show();
        
        // 清理
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    static getBgClass(type) {
        const classes = {
            success: 'bg-success',
            error: 'bg-danger',
            warning: 'bg-warning',
            info: 'bg-info'
        };
        return classes[type] || 'bg-primary';
    }

    static getIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// 导航管理
class NavigationManager {
    static init() {
        // 监听导航点击
        document.querySelectorAll('.nav-link[data-section]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.dataset.section;
                this.showSection(section);
            });
        });
    }

    static showSection(sectionName) {
        // 隐藏所有section
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        
        // 移除所有nav-link的active状态
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // 显示目标section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        // 激活对应的nav-link
        const targetLink = document.querySelector(`[data-section="${sectionName}"]`);
        if (targetLink) {
            targetLink.classList.add('active');
        }

        // 触发section特定的加载逻辑
        this.triggerSectionLoad(sectionName);
    }

    static triggerSectionLoad(sectionName) {
        const events = {
            management: () => window.PersonManagement?.loadPersonList(),
            analytics: () => window.Analytics?.loadStatistics()
        };

        if (events[sectionName]) {
            events[sectionName]();
        }
    }
}

// 拖拽上传处理
class DragDropHandler {
    static init(element, onFilesCallback) {
        if (!element || typeof onFilesCallback !== 'function') {
            console.error('DragDropHandler: 缺少必要参数');
            return;
        }

        // 阻止默认拖拽行为
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            element.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // 拖拽进入和悬停
        ['dragenter', 'dragover'].forEach(eventName => {
            element.addEventListener(eventName, () => {
                element.classList.add('dragover');
            }, false);
        });

        // 拖拽离开
        ['dragleave', 'drop'].forEach(eventName => {
            element.addEventListener(eventName, () => {
                element.classList.remove('dragover');
            }, false);
        });

        // 文件放置
        element.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                onFilesCallback(files);
            }
        }, false);
    }

    static preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
}

// 图片预览工具
class ImagePreview {
    static createPreview(file, container, options = {}) {
        const {
            maxWidth = '100%',
            maxHeight = '400px',
            className = 'img-fluid image-preview',
            onRemove = null
        } = options;

        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const div = document.createElement('div');
                div.className = 'position-relative mb-3';
                
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = className;
                img.style.maxWidth = maxWidth;
                img.style.maxHeight = maxHeight;
                img.style.objectFit = 'cover';
                
                div.appendChild(img);
                
                // 添加删除按钮
                if (onRemove) {
                    const removeBtn = document.createElement('button');
                    removeBtn.className = 'btn btn-outline-danger btn-sm position-absolute top-0 end-0 m-2';
                    removeBtn.innerHTML = '<i class="bi bi-x"></i>';
                    removeBtn.onclick = () => onRemove(div, file);
                    div.appendChild(removeBtn);
                }
                
                container.appendChild(div);
                resolve(div);
            };
            
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    static clear(container) {
        container.innerHTML = '';
    }
}

// 加载状态管理
class LoadingManager {
    static setButtonLoading(button, isLoading, loadingText = '处理中...') {
        if (!button) return;

        if (isLoading) {
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${loadingText}`;
            button.disabled = true;
            button.classList.add('loading');
        } else {
            button.innerHTML = button.dataset.originalText || button.innerHTML;
            button.disabled = false;
            button.classList.remove('loading');
        }
    }

    static showSpinner(container, message = '加载中...') {
        container.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2 text-muted">${message}</p>
            </div>
        `;
    }
}

// 数字动画
class NumberAnimator {
    static animate(elementId, targetValue, duration = 1000) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const startValue = parseInt(element.textContent) || 0;
        const difference = targetValue - startValue;
        const steps = 20;
        const stepTime = duration / steps;
        const increment = difference / steps;
        
        let currentValue = startValue;
        let currentStep = 0;
        
        const timer = setInterval(() => {
            currentStep++;
            currentValue += increment;
            
            if (currentStep >= steps) {
                currentValue = targetValue;
                clearInterval(timer);
            }
            
            element.textContent = Math.round(currentValue);
        }, stepTime);
    }
}

// 导出到全局作用域
window.CONFIG = CONFIG;
window.ApiClient = ApiClient;
window.FileValidator = FileValidator;
window.ToastManager = ToastManager;
window.NavigationManager = NavigationManager;
window.DragDropHandler = DragDropHandler;
window.ImagePreview = ImagePreview;
window.LoadingManager = LoadingManager;
window.NumberAnimator = NumberAnimator;

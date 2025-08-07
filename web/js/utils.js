/**
 * 核心工具模块 - utils.js
 * 包含通用工具函数、API调用、加载状态管理等
 */

// API配置
const API_BASE_URL = '/api';

// 全局变量
let loadingCount = 0;

// ============= 加载状态管理 =============
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
            setTimeout(() => {
                loadingBar.style.transform = 'scaleX(1)';
                setTimeout(() => {
                    loadingBar.style.display = 'none';
                    loadingBar.style.transform = 'scaleX(0)';
                }, 200);
            }, 100);
        }
    }
}

// ============= Toast通知系统 =============
function showToast(title, message, type = 'success', duration = 5000) {
    console.log(`[${type.toUpperCase()}] ${title}: ${message}`);
    
    // 创建Toast容器（如果不存在）
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // 创建Toast元素
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    const toastId = 'toast_' + Date.now();
    toast.id = toastId;
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}</strong><br>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                    data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // 使用Bootstrap Toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: duration
    });
    bsToast.show();
    
    // 清理
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
    
    return toastId;
}

// ============= HTTP请求工具 =============
async function fetchWithRetry(url, options = {}, retries = 3, delay = 1000) {
    for (let i = 0; i < retries; i++) {
        try {
            console.log(`[API] 请求: ${url}`, options.method || 'GET');
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000);
            
            // 正确处理FormData的headers
            const headers = { ...options.headers };
            if (options.body instanceof FormData) {
                // 对于FormData，不设置Content-Type，让浏览器自动设置
                delete headers['Content-Type'];
            } else {
                // 对于非FormData，设置为application/json
                headers['Content-Type'] = headers['Content-Type'] || 'application/json';
            }
            
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                headers: headers
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                console.log(`[API] 成功: ${url} - ${response.status}`);
                return response;
            }
            
            // 如果是最后一次尝试
            if (i === retries - 1) {
                const errorText = await response.text().catch(() => '');
                const error = new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
                error.status = response.status;
                error.response = response;
                throw error;
            }
            
            console.warn(`[API] 重试 ${i + 1}/${retries}: ${url} - ${response.status}`);
            
        } catch (error) {
            if (i === retries - 1) {
                console.error(`[API] 失败: ${url}`, error);
                
                if (error.name === 'AbortError') {
                    throw new Error('请求超时，请检查网络连接');
                } else if (error.message.includes('Failed to fetch')) {
                    throw new Error('网络连接失败，请检查服务器状态');
                }
                throw error;
            }
            
            // 重试延迟
            await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
        }
    }
}

// ============= 文件处理工具 =============
function validateImageFile(file) {
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff'];
    const maxSize = 16 * 1024 * 1024; // 16MB
    
    if (!allowedTypes.includes(file.type)) {
        throw new Error(`不支持的文件格式: ${file.type}。支持的格式: JPG, PNG, BMP, TIFF`);
    }
    
    if (file.size > maxSize) {
        throw new Error(`文件太大: ${(file.size / 1024 / 1024).toFixed(2)}MB。最大支持: 16MB`);
    }
    
    return true;
}

function createImagePreview(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = () => reject(new Error('文件读取失败'));
        reader.readAsDataURL(file);
    });
}

// ============= DOM工具函数 =============
function updateElement(id, value, attribute = 'textContent') {
    const element = document.getElementById(id);
    if (element) {
        if (attribute === 'textContent') {
            element.textContent = value;
        } else if (attribute === 'innerHTML') {
            element.innerHTML = value;
        } else if (attribute === 'value') {
            element.value = value;
        } else {
            element.setAttribute(attribute, value);
        }
        return true;
    }
    return false;
}

function showElement(id, display = 'block') {
    const element = document.getElementById(id);
    if (element) {
        element.style.display = display;
        return true;
    }
    return false;
}

function hideElement(id) {
    const element = document.getElementById(id);
    if (element) {
        element.style.display = 'none';
        return true;
    }
    return false;
}

function toggleElement(id, force = null) {
    const element = document.getElementById(id);
    if (element) {
        if (force !== null) {
            element.style.display = force ? 'block' : 'none';
        } else {
            element.style.display = element.style.display === 'none' ? 'block' : 'none';
        }
        return true;
    }
    return false;
}

// ============= 格式化工具 =============
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function formatConfidence(confidence) {
    return `${(confidence * 100).toFixed(1)}%`;
}

// ============= 错误处理 =============
function handleError(error, context = '') {
    console.error(`[错误] ${context}:`, error);
    
    let message = error.message || '未知错误';
    let title = '错误';
    
    if (error.status) {
        switch (error.status) {
            case 400:
                title = '请求错误';
                break;
            case 401:
                title = '未授权';
                break;
            case 403:
                title = '禁止访问';
                break;
            case 404:
                title = '资源不存在';
                break;
            case 500:
                title = '服务器错误';
                break;
            default:
                title = `HTTP ${error.status}`;
        }
    }
    
    showToast(title, message, 'error');
    return { title, message };
}

// ============= 调试工具 =============
function debugLog(message, data = null) {
    if (window.DEBUG_MODE) {
        console.log(`[DEBUG] ${message}`, data);
    }
}

// ============= 导出全局函数 =============
window.showGlobalSpinner = showGlobalSpinner;
window.hideGlobalSpinner = hideGlobalSpinner;
window.showToast = showToast;
window.fetchWithRetry = fetchWithRetry;
window.validateImageFile = validateImageFile;
window.createImagePreview = createImagePreview;
window.updateElement = updateElement;
window.showElement = showElement;
window.hideElement = hideElement;
window.toggleElement = toggleElement;
window.formatFileSize = formatFileSize;
window.formatDate = formatDate;
window.formatConfidence = formatConfidence;
window.handleError = handleError;
window.debugLog = debugLog;
window.API_BASE_URL = API_BASE_URL;

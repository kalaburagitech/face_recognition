/**
 * UI组件库
 * @description 提供通用的UI组件和交互功能
 */

import { CONFIG } from '../config.js';
import { generateId, $, addClass, removeClass } from '../utils/helpers.js';
import { eventManager, APP_EVENTS } from '../services/event-manager.js';

/**
 * Toast通知组件
 */
export class Toast {
  constructor() {
    this.container = this._createContainer();
  }

  /**
   * 显示Toast
   * @param {string} title - 标题
   * @param {string} message - 消息
   * @param {string} type - 类型 (success, error, warning, info)
   * @param {number} duration - 持续时间
   */
  show(title, message, type = 'info', duration = CONFIG.UI.TOAST_DEFAULT_DURATION) {
    const toast = this._createToast(title, message, type);
    this.container.appendChild(toast);

    // 触发动画
    requestAnimationFrame(() => {
      addClass(toast, 'show');
    });

    // 发布事件
    eventManager.emit(APP_EVENTS.TOAST_SHOW, { title, message, type });

    // 自动隐藏
    if (duration > 0) {
      setTimeout(() => this.hide(toast), duration);
    }

    return toast;
  }

  /**
   * 隐藏Toast
   * @param {Element} toast - Toast元素
   */
  hide(toast) {
    if (!toast) return;

    removeClass(toast, 'show');
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }

  /**
   * 创建Toast容器
   * @private
   */
  _createContainer() {
    let container = $('#toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  /**
   * 创建Toast元素
   * @private
   */
  _createToast(title, message, type) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div class="toast-header">
        <i class="toast-icon bi ${this._getIcon(type)}"></i>
        <strong class="toast-title">${title}</strong>
        <button type="button" class="toast-close" onclick="this.parentElement.parentElement.remove()">
          <i class="bi bi-x"></i>
        </button>
      </div>
      <div class="toast-body">${message}</div>
    `;
    return toast;
  }

  /**
   * 根据类型获取图标
   * @private
   */
  _getIcon(type) {
    const icons = {
      success: 'bi-check-circle',
      error: 'bi-exclamation-triangle',
      warning: 'bi-exclamation-circle',
      info: 'bi-info-circle'
    };
    return icons[type] || icons.info;
  }
}

/**
 * 加载器组件
 */
export class Loader {
  constructor() {
    this.overlay = null;
    this.isVisible = false;
  }

  /**
   * 显示加载器
   * @param {string} message - 加载消息
   */
  show(message = '加载中...') {
    if (this.isVisible) return;

    this.overlay = this._createOverlay(message);
    document.body.appendChild(this.overlay);
    
    setTimeout(() => {
      addClass(this.overlay, 'show');
      this.isVisible = true;
    }, 10);
  }

  /**
   * 隐藏加载器
   */
  hide() {
    if (!this.isVisible || !this.overlay) return;

    removeClass(this.overlay, 'show');
    
    setTimeout(() => {
      if (this.overlay && this.overlay.parentNode) {
        this.overlay.parentNode.removeChild(this.overlay);
      }
      this.overlay = null;
      this.isVisible = false;
    }, 300);
  }

  /**
   * 创建遮罩层
   * @private
   */
  _createOverlay(message) {
    const overlay = document.createElement('div');
    overlay.className = 'loader-overlay';
    overlay.innerHTML = `
      <div class="loader-content">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <div class="loader-message">${message}</div>
      </div>
    `;
    return overlay;
  }
}

/**
 * 模态框组件
 */
export class Modal {
  constructor(id, options = {}) {
    this.id = id;
    this.options = {
      backdrop: true,
      keyboard: true,
      focus: true,
      ...options
    };
    this.element = null;
    this.isVisible = false;
  }

  /**
   * 显示模态框
   * @param {object} data - 模态框数据
   */
  show(data = {}) {
    if (this.isVisible) return;

    this.element = this._createModal(data);
    document.body.appendChild(this.element);

    // 事件监听
    this._bindEvents();

    // 显示动画
    setTimeout(() => {
      addClass(this.element, 'show');
      this.isVisible = true;
      
      // 发布事件
      eventManager.emit(APP_EVENTS.MODAL_OPEN, { id: this.id, data });
    }, 10);
  }

  /**
   * 隐藏模态框
   */
  hide() {
    if (!this.isVisible || !this.element) return;

    removeClass(this.element, 'show');
    
    setTimeout(() => {
      if (this.element && this.element.parentNode) {
        this.element.parentNode.removeChild(this.element);
      }
      this.element = null;
      this.isVisible = false;
      
      // 发布事件
      eventManager.emit(APP_EVENTS.MODAL_CLOSE, { id: this.id });
    }, 300);
  }

  /**
   * 创建模态框元素
   * @private
   */
  _createModal(data) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = this._getModalTemplate(data);
    return modal;
  }

  /**
   * 获取模态框模板
   * @private
   */
  _getModalTemplate(data) {
    return `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${data.title || '模态框'}</h5>
            <button type="button" class="btn-close modal-close"></button>
          </div>
          <div class="modal-body">
            ${data.content || ''}
          </div>
          <div class="modal-footer">
            ${data.footer || '<button type="button" class="btn btn-secondary modal-close">关闭</button>'}
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 绑定事件
   * @private
   */
  _bindEvents() {
    if (!this.element) return;

    // 关闭按钮
    const closeButtons = this.element.querySelectorAll('.modal-close');
    closeButtons.forEach(btn => {
      btn.addEventListener('click', () => this.hide());
    });

    // 背景点击关闭
    if (this.options.backdrop) {
      this.element.addEventListener('click', (e) => {
        if (e.target === this.element) {
          this.hide();
        }
      });
    }

    // ESC键关闭
    if (this.options.keyboard) {
      this._keydownHandler = (e) => {
        if (e.key === 'Escape') {
          this.hide();
        }
      };
      document.addEventListener('keydown', this._keydownHandler);
    }
  }

  /**
   * 销毁模态框
   */
  destroy() {
    this.hide();
    if (this._keydownHandler) {
      document.removeEventListener('keydown', this._keydownHandler);
    }
  }
}

/**
 * 文件上传组件
 */
export class FileUploader {
  constructor(element, options = {}) {
    this.element = typeof element === 'string' ? $(element) : element;
    this.options = {
      multiple: false,
      accept: CONFIG.UPLOAD.ACCEPTED_TYPES.join(','),
      maxSize: CONFIG.UPLOAD.MAX_FILE_SIZE,
      dropZone: null,
      preview: true,
      ...options
    };
    
    this.files = [];
    this.isUploading = false;
    
    this._init();
  }

  /**
   * 初始化上传组件
   * @private
   */
  _init() {
    if (!this.element) return;

    // 设置input属性
    this.element.type = 'file';
    if (this.options.multiple) {
      this.element.multiple = true;
    }
    if (this.options.accept) {
      this.element.accept = this.options.accept;
    }

    // 绑定事件
    this.element.addEventListener('change', (e) => this._handleFileSelect(e));

    // 拖拽支持
    if (this.options.dropZone) {
      this._setupDropZone();
    }
  }

  /**
   * 设置拖拽区域
   * @private
   */
  _setupDropZone() {
    const dropZone = typeof this.options.dropZone === 'string' 
      ? $(this.options.dropZone) 
      : this.options.dropZone;
    
    if (!dropZone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, () => {
        addClass(dropZone, 'drag-over');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, () => {
        removeClass(dropZone, 'drag-over');
      });
    });

    dropZone.addEventListener('drop', (e) => {
      const files = Array.from(e.dataTransfer.files);
      this._processFiles(files);
    });

    // 点击触发文件选择
    dropZone.addEventListener('click', () => {
      this.element.click();
    });
  }

  /**
   * 处理文件选择
   * @private
   */
  _handleFileSelect(e) {
    const files = Array.from(e.target.files);
    this._processFiles(files);
  }

  /**
   * 处理文件
   * @private
   */
  _processFiles(files) {
    const validFiles = [];
    const errors = [];

    files.forEach(file => {
      try {
        this._validateFile(file);
        validFiles.push(file);
      } catch (error) {
        errors.push({ file, error: error.message });
      }
    });

    if (errors.length > 0) {
      eventManager.emit(APP_EVENTS.FILE_UPLOAD_ERROR, { errors });
    }

    if (validFiles.length > 0) {
      this.files = this.options.multiple ? [...this.files, ...validFiles] : validFiles;
      eventManager.emit(APP_EVENTS.FILE_SELECT, { files: validFiles });
      
      if (this.options.preview) {
        this._showPreview(validFiles);
      }
    }
  }

  /**
   * 验证文件
   * @private
   */
  _validateFile(file) {
    if (!this.options.accept.includes(file.type)) {
      throw new Error(`不支持的文件类型: ${file.type}`);
    }

    if (file.size > this.options.maxSize) {
      const maxSizeMB = (this.options.maxSize / 1024 / 1024).toFixed(0);
      throw new Error(`文件太大，最大支持 ${maxSizeMB}MB`);
    }
  }

  /**
   * 显示预览
   * @private
   */
  _showPreview(files) {
    // 这里可以实现文件预览逻辑
    // 具体实现取决于需求
  }

  /**
   * 获取选中的文件
   */
  getFiles() {
    return this.files;
  }

  /**
   * 清除选中的文件
   */
  clear() {
    this.files = [];
    this.element.value = '';
  }

  /**
   * 销毁组件
   */
  destroy() {
    this.clear();
    // 移除事件监听器...
  }
}

// 创建全局实例
export const toast = new Toast();
export const loader = new Loader();

// 全局方法
export function showToast(title, message, type, duration) {
  return toast.show(title, message, type, duration);
}

export function showLoader(message) {
  loader.show(message);
}

export function hideLoader() {
  loader.hide();
}

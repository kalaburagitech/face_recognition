/**
 * 人脸入库模块
 * @description 处理人脸入库相关的所有功能
 */

import { eventManager, APP_EVENTS } from '../services/event-manager.js';
import { faceRecognitionService } from '../services/face-recognition-api.js';
import { FileUploader, showToast, showLoader, hideLoader } from '../utils/ui-components.js';
import { $, validateFile, formatFileSize } from '../utils/helpers.js';
import { CONFIG } from '../config.js';

/**
 * 人脸入库模块类
 */
class EnrollmentModule {
  constructor() {
    this.fileUploader = null;
    this.selectedFiles = [];
    this.uploadMode = 'single'; // 'single' or 'batch'
    this.isEnrolling = false;
    
    this.init();
  }

  /**
   * 初始化模块
   */
  init() {
    console.log('📝 初始化人脸入库模块...');
    
    this._setupElements();
    this._setupEventListeners();
    this._setupFileUploader();
    
    console.log('✅ 人脸入库模块初始化完成');
  }

  /**
   * 设置DOM元素引用
   * @private
   */
  _setupElements() {
    this.elements = {
      form: $('#enrollmentForm'),
      nameInput: $('#personName'),
      descriptionInput: $('#personDescription'),
      uploadArea: $('#enrollmentUploadArea'),
      fileInput: $('#enrollmentFileInput'),
      previewContainer: $('#enrollmentPreview'),
      previewImages: $('#enrollmentPreviewImages'),
      submitBtn: $('#enrollmentBtn'),
      resultsContainer: $('#enrollmentResults'),
      errorContainer: $('#enrollmentError'),
      singleRadio: $('#singleUpload'),
      batchRadio: $('#batchUpload'),
      nameRequiredIndicator: $('#nameRequiredIndicator'),
      nameHelpText: $('#nameHelpText'),
      batchUploadHelp: $('#batchUploadHelp'),
      uploadText: $('#uploadText')
    };
  }

  /**
   * 设置事件监听器
   * @private
   */
  _setupEventListeners() {
    // 表单提交
    if (this.elements.form) {
      this.elements.form.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleEnrollment();
      });
    }

    // 上传模式切换
    if (this.elements.singleRadio) {
      this.elements.singleRadio.addEventListener('change', () => {
        this.setUploadMode('single');
      });
    }

    if (this.elements.batchRadio) {
      this.elements.batchRadio.addEventListener('change', () => {
        this.setUploadMode('batch');
      });
    }

    // Tab切换事件
    eventManager.on(APP_EVENTS.TAB_CHANGE, (data) => {
      if (data.tab === 'enrollment') {
        this._onTabActivated();
      }
    });
  }

  /**
   * 设置文件上传器
   * @private
   */
  _setupFileUploader() {
    if (!this.elements.uploadArea) return;

    this.fileUploader = new FileUploader(this.elements.uploadArea, {
      accept: CONFIG.UPLOAD.ALLOWED_TYPES,
      multiple: true,
      maxFileSize: CONFIG.UPLOAD.MAX_FILE_SIZE,
      maxFiles: CONFIG.UPLOAD.MAX_FILES,
      onFilesSelected: (files) => this._handleFilesSelected(files),
      onFileValidationError: (error) => this._handleFileError(error),
      customFileInput: this.elements.fileInput
    });
  }

  /**
   * 设置上传模式
   * @param {string} mode - 'single' 或 'batch'
   */
  setUploadMode(mode) {
    this.uploadMode = mode;
    this._updateUIForMode();
  }

  /**
   * 根据模式更新UI
   * @private
   */
  _updateUIForMode() {
    const isBatch = this.uploadMode === 'batch';
    
    // 更新必填指示器
    if (this.elements.nameRequiredIndicator) {
      this.elements.nameRequiredIndicator.style.display = isBatch ? 'none' : 'inline';
    }
    
    // 更新帮助文本
    if (this.elements.nameHelpText) {
      this.elements.nameHelpText.textContent = isBatch 
        ? '批量模式：姓名可选，文件名将作为人员姓名' 
        : '单张模式：必须填写人员姓名';
    }
    
    // 显示/隐藏批量上传说明
    if (this.elements.batchUploadHelp) {
      this.elements.batchUploadHelp.style.display = isBatch ? 'block' : 'none';
    }
    
    // 更新上传文本
    if (this.elements.uploadText) {
      this.elements.uploadText.textContent = isBatch 
        ? '点击选择多张图片或拖拽图片到此处' 
        : '点击选择图片或拖拽图片到此处';
    }
    
    // 更新文件上传器配置
    if (this.fileUploader) {
      this.fileUploader.setMultiple(isBatch);
    }
    
    // 更新name字段的required属性
    if (this.elements.nameInput) {
      this.elements.nameInput.required = !isBatch;
    }
  }

  /**
   * 处理文件选择
   * @private
   */
  _handleFilesSelected(files) {
    this.selectedFiles = Array.from(files);
    this._updatePreview();
    this._updateSubmitButton();
  }

  /**
   * 处理文件错误
   * @private
   */
  _handleFileError(error) {
    showToast('文件错误', error.message, 'error');
  }

  /**
   * 更新预览
   * @private
   */
  _updatePreview() {
    if (!this.elements.previewContainer || !this.elements.previewImages) return;

    if (this.selectedFiles.length === 0) {
      this.elements.previewContainer.style.display = 'none';
      return;
    }

    this.elements.previewContainer.style.display = 'block';
    this.elements.previewImages.innerHTML = '';

    this.selectedFiles.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const col = document.createElement('div');
        col.className = 'col-md-4 col-sm-6 mb-3';
        
        col.innerHTML = `
          <div class="card">
            <img src="${e.target.result}" class="card-img-top preview-image" 
                 style="height: 150px; object-fit: cover;" alt="预览图片 ${index + 1}">
            <div class="card-body p-2">
              <small class="text-muted d-block">${file.name}</small>
              <small class="text-muted">${formatFileSize(file.size)}</small>
              <button type="button" class="btn btn-sm btn-outline-danger float-end" 
                      onclick="enrollmentModule.removeFile(${index})">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>
        `;
        
        this.elements.previewImages.appendChild(col);
      };
      reader.readAsDataURL(file);
    });
  }

  /**
   * 移除文件
   * @param {number} index - 文件索引
   */
  removeFile(index) {
    this.selectedFiles.splice(index, 1);
    this._updatePreview();
    this._updateSubmitButton();
  }

  /**
   * 更新提交按钮状态
   * @private
   */
  _updateSubmitButton() {
    if (!this.elements.submitBtn) return;

    const hasFiles = this.selectedFiles.length > 0;
    const hasName = this.uploadMode === 'batch' || 
                   (this.elements.nameInput && this.elements.nameInput.value.trim());
    
    this.elements.submitBtn.disabled = !hasFiles || (!hasName && this.uploadMode === 'single');
  }

  /**
   * 处理人脸入库
   */
  async handleEnrollment() {
    if (this.isEnrolling) return;

    try {
      this.isEnrolling = true;
      this._updateSubmitButtonState(true);
      
      // 清除之前的结果
      this._clearResults();
      
      // 显示加载器
      showLoader('正在处理人脸入库...');
      
      // 获取表单数据
      const formData = this._prepareFormData();
      
      // 执行入库
      const results = await this._performEnrollment(formData);
      
      // 显示结果
      this._displayResults(results);
      
      // 发布成功事件
      eventManager.emit(APP_EVENTS.ENROLLMENT_SUCCESS, { results });
      
      showToast('入库成功', `成功处理 ${results.length} 个文件`, 'success');
      
      // 重置表单
      this._resetForm();
      
    } catch (error) {
      console.error('人脸入库失败:', error);
      this._displayError(error);
      eventManager.emit(APP_EVENTS.ENROLLMENT_ERROR, { error });
      showToast('入库失败', error.message || '未知错误', 'error');
    } finally {
      this.isEnrolling = false;
      this._updateSubmitButtonState(false);
      hideLoader();
    }
  }

  /**
   * 准备表单数据
   * @private
   */
  _prepareFormData() {
    const personName = this.elements.nameInput?.value.trim() || '';
    const description = this.elements.descriptionInput?.value.trim() || '';
    
    return this.selectedFiles.map(file => {
      const formData = new FormData();
      formData.append('file', file);
      
      if (this.uploadMode === 'single') {
        formData.append('name', personName);
        if (description) {
          formData.append('description', description);
        }
      } else {
        // 批量模式：使用文件名作为人员姓名（如果没有提供姓名）
        const fileName = file.name.replace(/\.[^/.]+$/, ''); // 移除扩展名
        formData.append('name', personName || fileName);
        if (description) {
          formData.append('description', description);
        }
      }
      
      return formData;
    });
  }

  /**
   * 执行入库操作
   * @private
   */
  async _performEnrollment(formDataArray) {
    const results = [];
    
    for (let i = 0; i < formDataArray.length; i++) {
      try {
        showLoader(`正在处理第 ${i + 1}/${formDataArray.length} 个文件...`);
        
        const result = await faceRecognitionService.enrollFace(formDataArray[i]);
        results.push({
          index: i,
          success: true,
          result: result,
          fileName: this.selectedFiles[i].name
        });
        
      } catch (error) {
        console.error(`文件 ${i + 1} 处理失败:`, error);
        results.push({
          index: i,
          success: false,
          error: error,
          fileName: this.selectedFiles[i].name
        });
      }
    }
    
    return results;
  }

  /**
   * 显示结果
   * @private
   */
  _displayResults(results) {
    if (!this.elements.resultsContainer) return;

    const successCount = results.filter(r => r.success).length;
    const failCount = results.length - successCount;
    
    let html = `
      <div class="alert alert-info">
        <h6><i class="bi bi-info-circle me-2"></i>处理结果</h6>
        <p class="mb-0">
          总共 ${results.length} 个文件，
          成功 ${successCount} 个，
          失败 ${failCount} 个
        </p>
      </div>
    `;
    
    results.forEach((result, index) => {
      if (result.success) {
        html += `
          <div class="alert alert-success">
            <strong>${result.fileName}</strong> - 入库成功
            <br><small>人员ID: ${result.result.person_id}</small>
          </div>
        `;
      } else {
        html += `
          <div class="alert alert-danger">
            <strong>${result.fileName}</strong> - 入库失败
            <br><small>${result.error.message || '未知错误'}</small>
          </div>
        `;
      }
    });
    
    this.elements.resultsContainer.innerHTML = html;
    this.elements.resultsContainer.style.display = 'block';
  }

  /**
   * 显示错误
   * @private
   */
  _displayError(error) {
    if (!this.elements.errorContainer) return;

    this.elements.errorContainer.innerHTML = `
      <div class="alert alert-danger">
        <h6><i class="bi bi-exclamation-triangle me-2"></i>入库失败</h6>
        <p class="mb-0">${error.message || '发生未知错误，请稍后重试'}</p>
      </div>
    `;
    this.elements.errorContainer.style.display = 'block';
  }

  /**
   * 清除结果显示
   * @private
   */
  _clearResults() {
    if (this.elements.resultsContainer) {
      this.elements.resultsContainer.style.display = 'none';
      this.elements.resultsContainer.innerHTML = '';
    }
    
    if (this.elements.errorContainer) {
      this.elements.errorContainer.style.display = 'none';
      this.elements.errorContainer.innerHTML = '';
    }
  }

  /**
   * 更新提交按钮状态
   * @private
   */
  _updateSubmitButtonState(loading) {
    if (!this.elements.submitBtn) return;

    const spinner = this.elements.submitBtn.querySelector('.loading-spinner');
    const icon = this.elements.submitBtn.querySelector('.bi-person-plus');
    
    if (loading) {
      this.elements.submitBtn.disabled = true;
      if (spinner) spinner.style.display = 'inline-block';
      if (icon) icon.style.display = 'none';
    } else {
      this.elements.submitBtn.disabled = false;
      if (spinner) spinner.style.display = 'none';
      if (icon) icon.style.display = 'inline';
    }
  }

  /**
   * 重置表单
   * @private
   */
  _resetForm() {
    // 清除文件选择
    this.selectedFiles = [];
    if (this.elements.fileInput) {
      this.elements.fileInput.value = '';
    }
    
    // 隐藏预览
    if (this.elements.previewContainer) {
      this.elements.previewContainer.style.display = 'none';
    }
    
    // 重置表单字段（保留模式选择）
    if (this.uploadMode === 'single') {
      if (this.elements.nameInput) this.elements.nameInput.value = '';
      if (this.elements.descriptionInput) this.elements.descriptionInput.value = '';
    }
    
    // 更新按钮状态
    this._updateSubmitButton();
  }

  /**
   * Tab激活时的处理
   * @private
   */
  _onTabActivated() {
    // 可以在这里添加Tab激活时的特殊处理
    console.log('人脸入库Tab已激活');
  }

  /**
   * 获取模块状态
   */
  getStatus() {
    return {
      isEnrolling: this.isEnrolling,
      selectedFiles: this.selectedFiles.length,
      uploadMode: this.uploadMode
    };
  }
}

// 创建并导出模块实例
const enrollmentModule = new EnrollmentModule();

// 将模块实例添加到全局对象以便调试和HTML中使用
window.enrollmentModule = enrollmentModule;

export { EnrollmentModule };
export default enrollmentModule;

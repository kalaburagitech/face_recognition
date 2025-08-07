/**
 * 人脸识别模块
 * @description 处理人脸识别相关的业务逻辑
 */

import { faceRecognitionService } from '../services/face-recognition-api.js';
import { eventManager, APP_EVENTS } from '../services/event-manager.js';
import { showToast, showLoader, hideLoader } from '../utils/ui-components.js';
import { validateImageFile, createImagePreview, cloneFile, formatFileSize, formatDate, $ } from '../utils/helpers.js';

/**
 * 人脸识别模块类
 */
export class RecognitionModule {
  constructor() {
    this.currentFile = null;
    this.isProcessing = false;
    this.lastResult = null;
    
    this._init();
  }

  /**
   * 初始化模块
   * @private
   */
  _init() {
    this._bindEvents();
    this._setupElements();
  }

  /**
   * 绑定事件
   * @private
   */
  _bindEvents() {
    // 监听文件选择事件
    eventManager.on(APP_EVENTS.FILE_SELECT, (data) => {
      if (data.files && data.files.length > 0) {
        this.handleFileSelect(data.files[0]);
      }
    });

    // 识别按钮点击事件
    const recognitionBtn = $('#recognitionBtn');
    if (recognitionBtn) {
      recognitionBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.performRecognition();
      });
    }
  }

  /**
   * 设置页面元素
   * @private
   */
  _setupElements() {
    // 设置文件输入和拖拽区域
    const fileInput = $('#recognitionFileInput');
    const dropZone = $('#recognitionUploadArea');
    
    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
          this.handleFileSelect(e.target.files[0]);
        }
      });
    }

    if (dropZone) {
      this._setupDropZone(dropZone, fileInput);
    }
  }

  /**
   * 设置拖拽区域
   * @private
   */
  _setupDropZone(dropZone, fileInput) {
    // 阻止默认行为
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
    });

    // 拖拽进入和悬停
    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, () => {
        dropZone.classList.add('dragover');
      });
    });

    // 拖拽离开和放下
    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, () => {
        dropZone.classList.remove('dragover');
      });
    });

    // 文件放下处理
    dropZone.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        this.handleFileSelect(files[0]);
      }
    });

    // 点击触发文件选择
    dropZone.addEventListener('click', () => {
      if (fileInput) {
        fileInput.click();
      }
    });
  }

  /**
   * 处理文件选择
   * @param {File} file - 选择的文件
   */
  async handleFileSelect(file) {
    try {
      // 验证文件
      validateImageFile(file);
      
      // 保存文件引用
      this.currentFile = cloneFile(file);
      
      // 显示预览
      await this._showPreview(file);
      
      // 启用识别按钮
      this._enableRecognitionButton();
      
      // 清除之前的结果
      this._clearResults();
      
      // 显示文件信息
      this._showFileInfo(file);
      
      showToast('文件选择', `已选择文件: ${file.name} (${formatFileSize(file.size)})`, 'info');
      
    } catch (error) {
      console.error('文件选择错误:', error);
      showToast('文件选择失败', error.message, 'error');
      this._clearFile();
    }
  }

  /**
   * 执行人脸识别
   */
  async performRecognition() {
    if (this.isProcessing) {
      showToast('操作提示', '识别正在进行中，请稍候...', 'warning');
      return;
    }

    if (!this.currentFile) {
      showToast('错误', '请先选择图片文件', 'error');
      return;
    }

    try {
      this.isProcessing = true;
      showLoader('正在识别人脸，请稍候...');
      
      // 显示加载状态
      this._showLoadingState();
      
      // 获取当前阈值
      const stats = await faceRecognitionService.getStatistics();
      const threshold = stats.recognition_threshold || 0.6;
      
      console.log('开始人脸识别，使用阈值:', threshold);
      
      // 发布识别开始事件
      eventManager.emit(APP_EVENTS.RECOGNITION_START, {
        file: this.currentFile,
        threshold
      });
      
      // 执行识别
      const result = await faceRecognitionService.recognizeFace(this.currentFile, threshold);
      
      console.log('识别结果:', result);
      this.lastResult = result;
      
      // 获取可视化图像
      let visualizationBlob = null;
      if (result.total_faces && result.total_faces > 0) {
        try {
          visualizationBlob = await faceRecognitionService.recognizeFaceWithVisualization(
            this.currentFile, 
            threshold
          );
        } catch (error) {
          console.warn('获取可视化图像失败:', error);
        }
      }
      
      // 显示结果
      this._displayResults(result, visualizationBlob);
      
      // 发布识别成功事件
      eventManager.emit(APP_EVENTS.RECOGNITION_SUCCESS, {
        result,
        visualization: visualizationBlob
      });
      
      showToast('识别完成', result.message || '人脸识别已完成', 'success');
      
    } catch (error) {
      console.error('识别错误:', error);
      
      this._showErrorState(error.message);
      
      // 发布识别错误事件
      eventManager.emit(APP_EVENTS.RECOGNITION_ERROR, { error });
      
      showToast('识别失败', error.message, 'error');
    } finally {
      this.isProcessing = false;
      hideLoader();
    }
  }

  /**
   * 显示预览
   * @private
   */
  async _showPreview(file) {
    try {
      const preview = $('#recognitionPreview');
      const previewImg = $('#recognitionPreviewImg');
      
      if (preview && previewImg) {
        const imageSrc = await createImagePreview(file);
        previewImg.src = imageSrc;
        preview.style.display = 'block';
      }
    } catch (error) {
      console.error('预览显示失败:', error);
    }
  }

  /**
   * 显示文件信息
   * @private
   */
  _showFileInfo(file) {
    const fileInfo = $('#recognitionFileInfo');
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
  }

  /**
   * 启用识别按钮
   * @private
   */
  _enableRecognitionButton() {
    const recognitionBtn = $('#recognitionBtn');
    if (recognitionBtn) {
      recognitionBtn.disabled = false;
    }
  }

  /**
   * 显示加载状态
   * @private
   */
  _showLoadingState() {
    const resultsDiv = $('#recognitionResults');
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
  }

  /**
   * 显示错误状态
   * @private
   */
  _showErrorState(errorMessage) {
    const resultsDiv = $('#recognitionResults');
    if (resultsDiv) {
      resultsDiv.innerHTML = `
        <div class="alert alert-danger">
          <i class="bi bi-exclamation-triangle me-2"></i>
          <strong>识别失败:</strong> ${errorMessage}
        </div>
      `;
    }
  }

  /**
   * 显示识别结果
   * @private
   */
  _displayResults(result, visualizationBlob) {
    const resultsDiv = $('#recognitionResults');
    if (!resultsDiv) return;

    if (!result.matches || result.matches.length === 0) {
      this._displayNoMatches(result, visualizationBlob);
    } else {
      this._displayMatches(result, visualizationBlob);
    }
  }

  /**
   * 显示无匹配结果
   * @private
   */
  _displayNoMatches(result, visualizationBlob) {
    const resultsDiv = $('#recognitionResults');
    let visualizationHtml = '';
    
    if (visualizationBlob) {
      const imageUrl = URL.createObjectURL(visualizationBlob);
      visualizationHtml = `
        <div class="col-md-6 mb-3">
          <div class="card">
            <div class="card-header">
              <h6 class="mb-0">
                <i class="bi bi-image me-2"></i>检测结果可视化
              </h6>
            </div>
            <div class="card-body text-center">
              <img src="${imageUrl}" class="img-fluid rounded" 
                   style="max-height: 400px; cursor: pointer;" 
                   onclick="this.requestFullscreen()">
              <div class="mt-2">
                <small class="text-muted">
                  <i class="bi bi-zoom-in me-1"></i>点击图片可全屏查看
                </small>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    resultsDiv.innerHTML = `
      <div class="row">
        ${visualizationHtml}
        <div class="col-md-${visualizationBlob ? '6' : '12'} mb-3">
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

  /**
   * 显示匹配结果
   * @private
   */
  _displayMatches(result, visualizationBlob) {
    const resultsDiv = $('#recognitionResults');
    
    let visualizationHtml = '';
    if (visualizationBlob) {
      const imageUrl = URL.createObjectURL(visualizationBlob);
      visualizationHtml = `
        <div class="col-md-6 mb-3">
          <div class="card">
            <div class="card-header">
              <h6 class="mb-0">
                <i class="bi bi-image me-2"></i>检测结果可视化
              </h6>
            </div>
            <div class="card-body text-center">
              <img src="${imageUrl}" class="img-fluid rounded" 
                   style="max-height: 400px; cursor: pointer;" 
                   onclick="this.requestFullscreen()">
              <div class="mt-2">
                <small class="text-muted">
                  <i class="bi bi-zoom-in me-1"></i>点击图片可全屏查看
                </small>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    const matchesHtml = result.matches.map(match => {
      const matchScore = match.match_score ? match.match_score.toFixed(1) : '0.0';
      const distance = match.distance ? match.distance.toFixed(3) : 'N/A';
      const badgeClass = parseFloat(matchScore) > 80 ? 'bg-success' : 
                        parseFloat(matchScore) > 60 ? 'bg-warning text-dark' : 'bg-secondary';
      
      const isUnknown = match.person_id === -1 || match.name === '未知人员';
      const cardClass = isUnknown ? 'border-warning' : 'border-success';
      
      return `
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
    }).join('');

    resultsDiv.innerHTML = `
      <div class="row">
        ${visualizationHtml}
        <div class="col-md-${visualizationBlob ? '6' : '12'}">
          <div class="alert alert-info mb-3">
            <i class="bi bi-info-circle me-2"></i>
            <strong>识别统计：</strong> 检测到 ${result.total_faces} 张人脸，识别出 ${result.matches.length} 个已知人员
          </div>
          ${matchesHtml}
        </div>
      </div>
    `;
  }

  /**
   * 清除结果
   * @private
   */
  _clearResults() {
    const resultsDiv = $('#recognitionResults');
    if (resultsDiv) {
      resultsDiv.innerHTML = `
        <div class="text-center text-muted">
          <i class="bi bi-image fs-1"></i>
          <p class="mt-3">上传图片开始识别</p>
        </div>
      `;
    }
  }

  /**
   * 清除文件
   * @private
   */
  _clearFile() {
    this.currentFile = null;
    
    // 重置文件输入
    const fileInput = $('#recognitionFileInput');
    if (fileInput) {
      fileInput.value = '';
    }
    
    // 隐藏预览
    const preview = $('#recognitionPreview');
    if (preview) {
      preview.style.display = 'none';
    }
    
    // 隐藏文件信息
    const fileInfo = $('#recognitionFileInfo');
    if (fileInfo) {
      fileInfo.style.display = 'none';
    }
    
    // 禁用识别按钮
    const recognitionBtn = $('#recognitionBtn');
    if (recognitionBtn) {
      recognitionBtn.disabled = true;
    }
    
    // 清除结果
    this._clearResults();
  }

  /**
   * 获取当前选择的文件
   */
  getCurrentFile() {
    return this.currentFile;
  }

  /**
   * 获取最后的识别结果
   */
  getLastResult() {
    return this.lastResult;
  }

  /**
   * 清除模块状态
   */
  clear() {
    this._clearFile();
    this.lastResult = null;
    this.isProcessing = false;
  }
}

// 创建默认实例
export const recognitionModule = new RecognitionModule();

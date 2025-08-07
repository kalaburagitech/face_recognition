/**
 * 统计信息模块
 * @description 处理系统统计信息和配置管理
 */

import { eventManager, APP_EVENTS } from '../services/event-manager.js';
import { faceRecognitionService } from '../services/face-recognition-api.js';
import { showToast, showLoader, hideLoader } from '../utils/ui-components.js';
import { $, formatNumber } from '../utils/helpers.js';
import { CONFIG } from '../config.js';

/**
 * 统计信息模块类
 */
class StatisticsModule {
  constructor() {
    this.statistics = null;
    this.systemConfig = null;
    this.updateTimer = null;
    this.isLoading = false;
    
    this.init();
  }

  /**
   * 初始化模块
   */
  init() {
    console.log('📊 初始化统计信息模块...');
    
    this._setupElements();
    this._setupEventListeners();
    
    console.log('✅ 统计信息模块初始化完成');
  }

  /**
   * 设置DOM元素引用
   * @private
   */
  _setupElements() {
    this.elements = {
      totalPersons: $('#totalPersons'),
      totalEncodings: $('#totalEncodings'),
      tolerance: $('#tolerance'),
      loadedEncodings: $('#loadedEncodings'),
      systemConfigContainer: $('#systemConfigContainer'),
      messagesContainer: $('#messagesContainer')
    };
  }

  /**
   * 设置事件监听器
   * @private
   */
  _setupEventListeners() {
    // Tab切换事件
    eventManager.on(APP_EVENTS.TAB_CHANGE, (data) => {
      if (data.tab === 'statistics') {
        this._onTabActivated();
      }
    });

    // 监听统计数据更新事件
    eventManager.on(APP_EVENTS.STATISTICS_UPDATE, (data) => {
      this.statistics = data;
      this._updateStatisticsDisplay();
    });

    // 监听其他模块的成功事件，刷新统计
    eventManager.on(APP_EVENTS.ENROLLMENT_SUCCESS, () => {
      this.loadStatistics();
    });

    eventManager.on(APP_EVENTS.RECOGNITION_SUCCESS, () => {
      this.loadStatistics();
    });
  }

  /**
   * Tab激活时的处理
   * @private
   */
  async _onTabActivated() {
    console.log('统计信息Tab已激活');
    if (!this.statistics) {
      await this.loadStatistics();
    }
    if (!this.systemConfig) {
      await this.loadSystemConfig();
    }
  }

  /**
   * 加载统计信息
   */
  async loadStatistics() {
    if (this.isLoading) return;

    try {
      this.isLoading = true;
      console.log('📊 加载统计信息...');
      
      const stats = await faceRecognitionService.getStatistics();
      this.statistics = stats;
      this._updateStatisticsDisplay();
      
      console.log('✅ 统计信息加载完成');
      
    } catch (error) {
      console.error('❌ 加载统计信息失败:', error);
      this._showError('统计信息', '加载统计信息失败: ' + (error.message || '未知错误'));
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * 加载系统配置
   */
  async loadSystemConfig() {
    try {
      console.log('⚙️ 加载系统配置...');
      
      // 这里可以调用获取系统配置的API
      // const config = await faceRecognitionService.getSystemConfig();
      
      // 暂时使用静态配置
      this.systemConfig = {
        model_name: 'buffalo_l',
        recognition_threshold: 0.6,
        max_face_size: 10 * 1024 * 1024, // 10MB
        supported_formats: ['jpg', 'jpeg', 'png', 'bmp'],
        max_batch_size: 10,
        face_detection_confidence: 0.5,
        face_alignment: true,
        feature_extraction_model: 'arcface',
        database_type: 'sqlite',
        cache_enabled: true
      };
      
      this._updateSystemConfigDisplay();
      
      console.log('✅ 系统配置加载完成');
      
    } catch (error) {
      console.error('❌ 加载系统配置失败:', error);
      this._showError('系统配置', '加载系统配置失败: ' + (error.message || '未知错误'));
    }
  }

  /**
   * 更新统计信息显示
   * @private
   */
  _updateStatisticsDisplay() {
    if (!this.statistics) return;

    // 更新统计卡片
    if (this.elements.totalPersons) {
      this.elements.totalPersons.textContent = formatNumber(this.statistics.total_persons || 0);
    }
    
    if (this.elements.totalEncodings) {
      this.elements.totalEncodings.textContent = formatNumber(this.statistics.total_encodings || 0);
    }
    
    if (this.elements.tolerance) {
      const tolerance = this.statistics.recognition_threshold || 0.6;
      this.elements.tolerance.textContent = (tolerance * 100).toFixed(0) + '%';
    }
    
    if (this.elements.loadedEncodings) {
      this.elements.loadedEncodings.textContent = formatNumber(this.statistics.loaded_encodings || 0);
    }

    // 添加动画效果
    this._animateNumbers();
  }

  /**
   * 更新系统配置显示
   * @private
   */
  _updateSystemConfigDisplay() {
    if (!this.elements.systemConfigContainer || !this.systemConfig) return;

    const configHtml = `
      <div class="row">
        <div class="col-md-6">
          <h6 class="text-primary mb-3">
            <i class="bi bi-gear me-2"></i>核心配置
          </h6>
          <div class="table-responsive">
            <table class="table table-sm">
              <tbody>
                <tr>
                  <td><strong>识别模型</strong></td>
                  <td>
                    <span class="badge bg-primary">${this.systemConfig.model_name}</span>
                  </td>
                </tr>
                <tr>
                  <td><strong>识别阈值</strong></td>
                  <td>
                    <div class="d-flex align-items-center">
                      <span class="me-2">${(this.systemConfig.recognition_threshold * 100).toFixed(0)}%</span>
                      <div class="progress flex-grow-1" style="height: 6px;">
                        <div class="progress-bar" role="progressbar" 
                             style="width: ${this.systemConfig.recognition_threshold * 100}%"></div>
                      </div>
                    </div>
                  </td>
                </tr>
                <tr>
                  <td><strong>检测置信度</strong></td>
                  <td>${(this.systemConfig.face_detection_confidence * 100).toFixed(0)}%</td>
                </tr>
                <tr>
                  <td><strong>特征提取</strong></td>
                  <td>
                    <span class="badge bg-success">${this.systemConfig.feature_extraction_model}</span>
                  </td>
                </tr>
                <tr>
                  <td><strong>人脸对齐</strong></td>
                  <td>
                    <i class="bi bi-${this.systemConfig.face_alignment ? 'check-circle text-success' : 'x-circle text-danger'}"></i>
                    ${this.systemConfig.face_alignment ? '启用' : '禁用'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <div class="col-md-6">
          <h6 class="text-primary mb-3">
            <i class="bi bi-upload me-2"></i>上传配置
          </h6>
          <div class="table-responsive">
            <table class="table table-sm">
              <tbody>
                <tr>
                  <td><strong>最大文件大小</strong></td>
                  <td>${this._formatFileSize(this.systemConfig.max_face_size)}</td>
                </tr>
                <tr>
                  <td><strong>支持格式</strong></td>
                  <td>
                    ${this.systemConfig.supported_formats.map(format => 
                      `<span class="badge bg-secondary me-1">${format.toUpperCase()}</span>`
                    ).join('')}
                  </td>
                </tr>
                <tr>
                  <td><strong>批量上传限制</strong></td>
                  <td>${this.systemConfig.max_batch_size} 个文件</td>
                </tr>
                <tr>
                  <td><strong>数据库类型</strong></td>
                  <td>
                    <span class="badge bg-info">${this.systemConfig.database_type.toUpperCase()}</span>
                  </td>
                </tr>
                <tr>
                  <td><strong>缓存状态</strong></td>
                  <td>
                    <i class="bi bi-${this.systemConfig.cache_enabled ? 'check-circle text-success' : 'x-circle text-danger'}"></i>
                    ${this.systemConfig.cache_enabled ? '启用' : '禁用'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <div class="row mt-4">
        <div class="col-12">
          <h6 class="text-primary mb-3">
            <i class="bi bi-speedometer2 me-2"></i>性能指标
          </h6>
          <div class="row">
            <div class="col-md-3">
              <div class="card bg-light">
                <div class="card-body text-center">
                  <i class="bi bi-stopwatch fs-4 text-primary"></i>
                  <h6 class="mt-2">平均识别时间</h6>
                  <p class="mb-0">${this.statistics?.avg_recognition_time || 0}ms</p>
                </div>
              </div>
            </div>
            <div class="col-md-3">
              <div class="card bg-light">
                <div class="card-body text-center">
                  <i class="bi bi-cpu fs-4 text-success"></i>
                  <h6 class="mt-2">CPU使用率</h6>
                  <p class="mb-0">${this.statistics?.cpu_usage || 0}%</p>
                </div>
              </div>
            </div>
            <div class="col-md-3">
              <div class="card bg-light">
                <div class="card-body text-center">
                  <i class="bi bi-memory fs-4 text-warning"></i>
                  <h6 class="mt-2">内存使用</h6>
                  <p class="mb-0">${this._formatFileSize(this.statistics?.memory_usage || 0)}</p>
                </div>
              </div>
            </div>
            <div class="col-md-3">
              <div class="card bg-light">
                <div class="card-body text-center">
                  <i class="bi bi-hdd fs-4 text-info"></i>
                  <h6 class="mt-2">存储使用</h6>
                  <p class="mb-0">${this._formatFileSize(this.statistics?.storage_usage || 0)}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="row mt-4">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <h6 class="text-primary mb-0">
              <i class="bi bi-arrow-clockwise me-2"></i>操作
            </h6>
            <small class="text-muted">
              最后更新: ${new Date().toLocaleString()}
            </small>
          </div>
          <hr>
          <div class="btn-group" role="group">
            <button class="btn btn-outline-primary btn-sm" onclick="statisticsModule.loadStatistics()">
              <i class="bi bi-arrow-clockwise me-1"></i>刷新统计
            </button>
            <button class="btn btn-outline-secondary btn-sm" onclick="statisticsModule.exportStatistics()">
              <i class="bi bi-download me-1"></i>导出数据
            </button>
            <button class="btn btn-outline-info btn-sm" onclick="statisticsModule.checkSystemHealth()">
              <i class="bi bi-shield-check me-1"></i>健康检查
            </button>
          </div>
        </div>
      </div>
    `;

    this.elements.systemConfigContainer.innerHTML = configHtml;
  }

  /**
   * 数字动画效果
   * @private
   */
  _animateNumbers() {
    const numberElements = [
      this.elements.totalPersons,
      this.elements.totalEncodings,
      this.elements.loadedEncodings
    ];

    numberElements.forEach(element => {
      if (element && element.textContent) {
        element.style.transform = 'scale(1.1)';
        element.style.transition = 'transform 0.2s ease';
        
        setTimeout(() => {
          element.style.transform = 'scale(1)';
        }, 200);
      }
    });
  }

  /**
   * 格式化文件大小
   * @private
   */
  _formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * 显示错误信息
   * @private
   */
  _showError(title, message) {
    if (this.elements.messagesContainer) {
      this.elements.messagesContainer.innerHTML = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
          <h6 class="alert-heading">
            <i class="bi bi-exclamation-triangle me-2"></i>${title}
          </h6>
          <p class="mb-0">${message}</p>
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      `;
      this.elements.messagesContainer.style.display = 'block';
    }
  }

  /**
   * 导出统计数据
   */
  async exportStatistics() {
    try {
      showLoader('准备导出统计数据...');
      
      const exportData = {
        export_time: new Date().toISOString(),
        statistics: this.statistics,
        system_config: this.systemConfig,
        app_version: CONFIG.APP.VERSION
      };
      
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
        type: 'application/json' 
      });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `statistics_export_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      showToast('导出成功', '统计数据已导出', 'success');
      
    } catch (error) {
      console.error('导出统计数据失败:', error);
      showToast('导出失败', '导出统计数据时发生错误', 'error');
    } finally {
      hideLoader();
    }
  }

  /**
   * 检查系统健康状态
   */
  async checkSystemHealth() {
    try {
      showLoader('检查系统健康状态...');
      
      // 这里可以调用健康检查API
      // const health = await faceRecognitionService.healthCheck();
      
      // 暂时模拟健康检查结果
      const health = {
        status: 'healthy',
        database: 'connected',
        model: 'loaded',
        memory_usage: 'normal',
        disk_space: 'sufficient',
        last_check: new Date().toISOString()
      };
      
      this._showHealthResults(health);
      
    } catch (error) {
      console.error('健康检查失败:', error);
      showToast('检查失败', '系统健康检查失败', 'error');
    } finally {
      hideLoader();
    }
  }

  /**
   * 显示健康检查结果
   * @private
   */
  _showHealthResults(health) {
    if (!this.elements.messagesContainer) return;

    const statusClass = health.status === 'healthy' ? 'success' : 'warning';
    const statusIcon = health.status === 'healthy' ? 'check-circle' : 'exclamation-triangle';
    
    this.elements.messagesContainer.innerHTML = `
      <div class="alert alert-${statusClass} alert-dismissible fade show" role="alert">
        <h6 class="alert-heading">
          <i class="bi bi-${statusIcon} me-2"></i>系统健康检查结果
        </h6>
        <div class="row">
          <div class="col-md-6">
            <ul class="list-unstyled mb-0">
              <li><i class="bi bi-database me-2"></i>数据库: ${health.database}</li>
              <li><i class="bi bi-cpu me-2"></i>模型: ${health.model}</li>
            </ul>
          </div>
          <div class="col-md-6">
            <ul class="list-unstyled mb-0">
              <li><i class="bi bi-memory me-2"></i>内存: ${health.memory_usage}</li>
              <li><i class="bi bi-hdd me-2"></i>磁盘: ${health.disk_space}</li>
            </ul>
          </div>
        </div>
        <hr class="my-2">
        <small class="text-muted">检查时间: ${new Date(health.last_check).toLocaleString()}</small>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
    this.elements.messagesContainer.style.display = 'block';
  }

  /**
   * 设置自动更新
   * @param {number} interval - 更新间隔(毫秒)
   */
  setAutoUpdate(interval = 30000) {
    this.clearAutoUpdate();
    
    this.updateTimer = setInterval(() => {
      if (document.getElementById('statistics').classList.contains('active')) {
        this.loadStatistics();
      }
    }, interval);
  }

  /**
   * 清除自动更新
   */
  clearAutoUpdate() {
    if (this.updateTimer) {
      clearInterval(this.updateTimer);
      this.updateTimer = null;
    }
  }

  /**
   * 获取模块状态
   */
  getStatus() {
    return {
      isLoading: this.isLoading,
      hasStatistics: !!this.statistics,
      hasSystemConfig: !!this.systemConfig,
      autoUpdateEnabled: !!this.updateTimer
    };
  }

  /**
   * 销毁模块
   */
  destroy() {
    this.clearAutoUpdate();
    this.statistics = null;
    this.systemConfig = null;
  }
}

// 创建并导出模块实例
const statisticsModule = new StatisticsModule();

// 将模块实例添加到全局对象以便调试和HTML中使用
window.statisticsModule = statisticsModule;

export { StatisticsModule };
export default statisticsModule;

/**
 * 主应用程序
 * @description 应用程序的入口点和主控制器
 */

import { CONFIG, ENV } from './config.js';
import { eventManager, APP_EVENTS } from './services/event-manager.js';
import { faceRecognitionService } from './services/face-recognition-api.js';
import { showToast, showLoader, hideLoader } from './utils/ui-components.js';
import { debounce, $ } from './utils/helpers.js';

// 导入模块
import { recognitionModule } from './modules/recognition.js';
import enrollmentModule from './modules/enrollment.js';
import managementModule from './modules/management.js';
import statisticsModule from './modules/statistics.js';

/**
 * 主应用程序类
 */
class FaceRecognitionApp {
  constructor() {
    this.isInitialized = false;
    this.currentTab = 'recognition';
    this.statisticsUpdateTimer = null;
    this.modules = new Map();
    
    // 绑定方法到实例
    this.updateStatistics = debounce(this.updateStatistics.bind(this), 1000);
  }

  /**
   * 初始化应用程序
   */
  async init() {
    if (this.isInitialized) {
      console.warn('应用程序已经初始化');
      return;
    }

    try {
      console.log('🚀 初始化人脸识别系统...');
      
      // 发布初始化事件
      eventManager.emit(APP_EVENTS.APP_INIT);
      
      // 设置全局错误处理
      this._setupGlobalErrorHandling();
      
      // 初始化模块
      await this._initializeModules();
      
      // 设置事件监听
      this._setupEventListeners();
      
      // 初始化UI
      this._initializeUI();
      
      // 加载初始数据
      await this._loadInitialData();
      
      // 设置定时任务
      this._setupTimers();
      
      // 标记为已初始化
      this.isInitialized = true;
      
      console.log('✅ 人脸识别系统初始化完成');
      
      // 发布就绪事件
      eventManager.emit(APP_EVENTS.APP_READY);
      
      // 显示欢迎消息
      setTimeout(() => {
        showToast('系统初始化', '人脸识别系统已就绪', 'success');
      }, 1000);
      
    } catch (error) {
      console.error('❌ 应用程序初始化失败:', error);
      eventManager.emit(APP_EVENTS.APP_ERROR, { error });
      showToast('初始化失败', '系统初始化过程中出现错误', 'error');
    }
  }

  /**
   * 初始化模块
   * @private
   */
  async _initializeModules() {
    console.log('📦 初始化模块...');
    
    // 注册识别模块
    this.modules.set('recognition', recognitionModule);
    
    // 注册人脸入库模块
    this.modules.set('enrollment', enrollmentModule);
    
    // 注册人员管理模块
    this.modules.set('management', managementModule);
    
    // 注册统计信息模块
    this.modules.set('statistics', statisticsModule);
    
    console.log(`✅ 已加载 ${this.modules.size} 个模块`);
  }

  /**
   * 设置全局错误处理
   * @private
   */
  _setupGlobalErrorHandling() {
    // 全局错误处理
    window.addEventListener('error', (event) => {
      console.error('全局错误:', event.error);
      eventManager.emit(APP_EVENTS.APP_ERROR, { 
        error: event.error, 
        source: 'global' 
      });
    });

    // Promise错误处理
    window.addEventListener('unhandledrejection', (event) => {
      console.error('未处理的Promise拒绝:', event.reason);
      eventManager.emit(APP_EVENTS.APP_ERROR, { 
        error: event.reason, 
        source: 'promise' 
      });
    });
  }

  /**
   * 设置事件监听
   * @private
   */
  _setupEventListeners() {
    // 监听统计数据更新事件
    eventManager.on(APP_EVENTS.STATISTICS_UPDATE, (data) => {
      this._updateStatisticsDisplay(data);
    });

    // 监听识别成功事件
    eventManager.on(APP_EVENTS.RECOGNITION_SUCCESS, (data) => {
      console.log('识别成功:', data);
      // 可以在这里添加额外的处理逻辑
    });

    // 监听Tab切换
    this._setupTabHandlers();
  }

  /**
   * 设置Tab处理
   * @private
   */
  _setupTabHandlers() {
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
      button.addEventListener('shown.bs.tab', (event) => {
        const newTab = event.target.getAttribute('data-bs-target').replace('#', '');
        this.currentTab = newTab;
        eventManager.emit(APP_EVENTS.TAB_CHANGE, { tab: newTab });
        console.log('切换到Tab:', newTab);
      });
    });
  }

  /**
   * 初始化UI
   * @private
   */
  _initializeUI() {
    console.log('🎨 初始化UI组件...');
    
    // 初始化Bootstrap组件
    this._initializeBootstrapComponents();
    
    // 设置版本信息
    this._updateVersionInfo();
    
    console.log('✅ UI组件初始化完成');
  }

  /**
   * 初始化Bootstrap组件
   * @private
   */
  _initializeBootstrapComponents() {
    // 这里可以初始化需要的Bootstrap组件
    // 例如：tooltips, popovers等
    
    // 初始化tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }

  /**
   * 更新版本信息
   * @private
   */
  _updateVersionInfo() {
    const versionElements = document.querySelectorAll('.app-version');
    versionElements.forEach(el => {
      el.textContent = CONFIG.APP.VERSION;
    });
  }

  /**
   * 加载初始数据
   * @private
   */
  async _loadInitialData() {
    console.log('📊 加载初始数据...');
    
    try {
      // 加载系统统计信息
      await this.updateStatistics();
      
      console.log('✅ 初始数据加载完成');
    } catch (error) {
      console.error('❌ 初始数据加载失败:', error);
      // 不阻止应用初始化，只是显示警告
      showToast('数据加载', '部分数据加载失败，但系统仍可正常使用', 'warning');
    }
  }

  /**
   * 设置定时器
   * @private
   */
  _setupTimers() {
    // 设置统计数据自动更新
    this.statisticsUpdateTimer = setInterval(
      () => this.updateStatistics(),
      CONFIG.UI.STATISTICS_UPDATE_INTERVAL
    );
  }

  /**
   * 更新统计信息
   */
  async updateStatistics() {
    try {
      const stats = await faceRecognitionService.getStatistics();
      eventManager.emit(APP_EVENTS.STATISTICS_UPDATE, stats);
      return stats;
    } catch (error) {
      console.error('统计信息更新失败:', error);
      throw error;
    }
  }

  /**
   * 更新统计信息显示
   * @private
   */
  _updateStatisticsDisplay(stats) {
    // 更新各种统计信息显示
    const elements = {
      totalPersons: $('#totalPersons'),
      totalEncodings: $('#totalEncodings'),
      currentModel: $('#currentModel'),
      recognitionThreshold: $('#recognitionThreshold')
    };

    if (elements.totalPersons) {
      elements.totalPersons.textContent = stats.total_persons || 0;
    }
    
    if (elements.totalEncodings) {
      elements.totalEncodings.textContent = stats.total_encodings || 0;
    }
    
    if (elements.currentModel) {
      elements.currentModel.textContent = stats.current_model || 'Unknown';
    }
    
    if (elements.recognitionThreshold) {
      elements.recognitionThreshold.textContent = 
        ((stats.recognition_threshold || 0.6) * 100).toFixed(0) + '%';
    }
  }

  /**
   * 获取模块实例
   * @param {string} name - 模块名称
   * @returns {object|null} 模块实例
   */
  getModule(name) {
    return this.modules.get(name) || null;
  }

  /**
   * 检查健康状态
   */
  async checkHealth() {
    try {
      const health = await faceRecognitionService.healthCheck();
      console.log('健康检查结果:', health);
      return health;
    } catch (error) {
      console.error('健康检查失败:', error);
      throw error;
    }
  }

  /**
   * 销毁应用程序
   */
  destroy() {
    console.log('🔄 销毁应用程序...');
    
    // 清除定时器
    if (this.statisticsUpdateTimer) {
      clearInterval(this.statisticsUpdateTimer);
      this.statisticsUpdateTimer = null;
    }
    
    // 清除事件监听器
    eventManager.clear();
    
    // 清除模块
    this.modules.clear();
    
    // 重置状态
    this.isInitialized = false;
    
    console.log('✅ 应用程序已销毁');
  }
}

// 创建应用程序实例
const app = new FaceRecognitionApp();

// DOM加载完成后初始化应用程序
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => app.init());
} else {
  app.init();
}

// 导出应用程序实例供调试使用
window.FaceRecognitionApp = app;

// 导出应用程序类供其他模块使用
export { FaceRecognitionApp };
export default app;

/**
 * 应用程序配置
 * @description 集中管理所有配置信息
 */

export const CONFIG = {
  // API配置
  API: {
    BASE_URL: '/api',
    TIMEOUT: 30000,
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 1000
  },

  // 文件上传配置
  UPLOAD: {
    MAX_FILE_SIZE: 16 * 1024 * 1024, // 16MB
    ACCEPTED_TYPES: ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff'],
    ACCEPTED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
  },

  // 识别配置
  RECOGNITION: {
    DEFAULT_THRESHOLD: 0.6,
    MIN_THRESHOLD: 0.0,
    MAX_THRESHOLD: 0.9,
    THRESHOLD_STEP: 0.05
  },

  // UI配置
  UI: {
    TOAST_DEFAULT_DURATION: 3000,
    STATISTICS_UPDATE_INTERVAL: 60000, // 1分钟
    LOADING_SPINNER_DELAY: 200,
    DEBOUNCE_DELAY: 300
  },

  // 应用信息
  APP: {
    NAME: '人脸识别系统',
    VERSION: '2.0.0',
    DESCRIPTION: '基于 InsightFace 和 DeepFace 的高精度人脸识别系统'
  }
};

// 环境配置
export const ENV = {
  isDevelopment: location.hostname === 'localhost' || location.hostname === '127.0.0.1',
  isProduction: location.protocol === 'https:',
  
  // 动态获取API基础URL
  getApiBaseUrl() {
    return CONFIG.API.BASE_URL;
  }
};

// 只读配置，防止意外修改
Object.freeze(CONFIG);
Object.freeze(ENV);

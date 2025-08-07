/**
 * 通用工具函数
 * @description 提供应用程序通用的工具函数
 */

import { CONFIG } from '../config.js';

/**
 * 防抖函数
 * @param {Function} func - 需要防抖的函数
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function debounce(func, delay = CONFIG.UI.DEBOUNCE_DELAY) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

/**
 * 节流函数
 * @param {Function} func - 需要节流的函数
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Function} 节流后的函数
 */
export function throttle(func, delay) {
  let lastCall = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      return func.apply(this, args);
    }
  };
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的文件大小
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  
  const units = ['B', 'KB', 'MB', 'GB'];
  const base = 1024;
  const index = Math.floor(Math.log(bytes) / Math.log(base));
  const size = (bytes / Math.pow(base, index)).toFixed(1);
  
  return `${size} ${units[index]}`;
}

/**
 * 格式化日期时间
 * @param {Date|string|number} date - 日期
 * @param {object} options - 格式化选项
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, options = {}) {
  const dateObj = date instanceof Date ? date : new Date(date);
  
  const defaultOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  };
  
  return dateObj.toLocaleString('zh-CN', { ...defaultOptions, ...options });
}

/**
 * 验证图片文件
 * @param {File} file - 文件对象
 * @throws {Error} 验证失败时抛出错误
 */
export function validateImageFile(file) {
  if (!file) {
    throw new Error('请选择文件');
  }

  if (!CONFIG.UPLOAD.ACCEPTED_TYPES.includes(file.type)) {
    throw new Error(`不支持的文件格式: ${file.type}。支持的格式: ${CONFIG.UPLOAD.ACCEPTED_EXTENSIONS.join(', ')}`);
  }

  if (file.size > CONFIG.UPLOAD.MAX_FILE_SIZE) {
    const maxSizeMB = (CONFIG.UPLOAD.MAX_FILE_SIZE / 1024 / 1024).toFixed(0);
    const fileSizeMB = (file.size / 1024 / 1024).toFixed(2);
    throw new Error(`文件太大: ${fileSizeMB}MB。最大支持: ${maxSizeMB}MB`);
  }

  return true;
}

/**
 * 创建图片预览URL
 * @param {File} file - 图片文件
 * @returns {Promise<string>} 预览URL
 */
export function createImagePreview(file) {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith('image/')) {
      reject(new Error('不是有效的图片文件'));
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = () => reject(new Error('文件读取失败'));
    reader.readAsDataURL(file);
  });
}

/**
 * 安全的文件克隆
 * @param {File} file - 原始文件
 * @returns {File} 克隆的文件
 */
export function cloneFile(file) {
  return new File([file], file.name, {
    type: file.type,
    lastModified: file.lastModified
  });
}

/**
 * 生成唯一ID
 * @param {string} prefix - 前缀
 * @returns {string} 唯一ID
 */
export function generateId(prefix = 'id') {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 深拷贝对象
 * @param {any} obj - 要拷贝的对象
 * @returns {any} 拷贝后的对象
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj);
  if (obj instanceof Array) return obj.map(item => deepClone(item));
  if (typeof obj === 'object') {
    const clonedObj = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }
}

/**
 * 安全的JSON解析
 * @param {string} jsonString - JSON字符串
 * @param {any} defaultValue - 默认值
 * @returns {any} 解析结果
 */
export function safeJsonParse(jsonString, defaultValue = null) {
  try {
    return JSON.parse(jsonString);
  } catch {
    return defaultValue;
  }
}

/**
 * 检查对象是否为空
 * @param {any} obj - 要检查的对象
 * @returns {boolean} 是否为空
 */
export function isEmpty(obj) {
  if (obj == null) return true;
  if (typeof obj === 'string' || Array.isArray(obj)) return obj.length === 0;
  if (typeof obj === 'object') return Object.keys(obj).length === 0;
  return false;
}

/**
 * 延迟执行
 * @param {number} ms - 延迟时间（毫秒）
 * @returns {Promise<void>}
 */
export function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 数组去重
 * @param {Array} array - 原数组
 * @param {string|Function} key - 去重依据的键或函数
 * @returns {Array} 去重后的数组
 */
export function uniqueArray(array, key) {
  if (!key) return [...new Set(array)];
  
  const seen = new Set();
  return array.filter(item => {
    const identifier = typeof key === 'function' ? key(item) : item[key];
    if (seen.has(identifier)) return false;
    seen.add(identifier);
    return true;
  });
}

/**
 * 安全的元素选择器
 * @param {string} selector - CSS选择器
 * @param {Element} context - 上下文元素
 * @returns {Element|null} 元素
 */
export function $(selector, context = document) {
  return context.querySelector(selector);
}

/**
 * 安全的多元素选择器
 * @param {string} selector - CSS选择器
 * @param {Element} context - 上下文元素
 * @returns {NodeList} 元素列表
 */
export function $$(selector, context = document) {
  return context.querySelectorAll(selector);
}

/**
 * 检查元素是否存在
 * @param {string|Element} element - 元素或选择器
 * @returns {boolean} 是否存在
 */
export function elementExists(element) {
  if (typeof element === 'string') {
    return document.querySelector(element) !== null;
  }
  return element && element.nodeType === Node.ELEMENT_NODE;
}

/**
 * 安全的事件监听器添加
 * @param {Element|string} element - 元素或选择器
 * @param {string} event - 事件类型
 * @param {Function} handler - 事件处理器
 * @param {object} options - 选项
 * @returns {Function|null} 移除事件监听器的函数
 */
export function addEventListener(element, event, handler, options = {}) {
  const el = typeof element === 'string' ? $(element) : element;
  if (!el) return null;
  
  el.addEventListener(event, handler, options);
  
  // 返回移除监听器的函数
  return () => el.removeEventListener(event, handler, options);
}

/**
 * 批量添加CSS类
 * @param {Element|string} element - 元素或选择器
 * @param {...string} classes - 类名列表
 */
export function addClass(element, ...classes) {
  const el = typeof element === 'string' ? $(element) : element;
  if (el) {
    el.classList.add(...classes);
  }
}

/**
 * 批量移除CSS类
 * @param {Element|string} element - 元素或选择器
 * @param {...string} classes - 类名列表
 */
export function removeClass(element, ...classes) {
  const el = typeof element === 'string' ? $(element) : element;
  if (el) {
    el.classList.remove(...classes);
  }
}

/**
 * 切换CSS类
 * @param {Element|string} element - 元素或选择器
 * @param {string} className - 类名
 * @param {boolean} force - 强制添加或移除
 */
export function toggleClass(element, className, force) {
  const el = typeof element === 'string' ? $(element) : element;
  if (el) {
    return el.classList.toggle(className, force);
  }
  return false;
}

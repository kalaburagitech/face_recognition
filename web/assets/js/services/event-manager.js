/**
 * 事件管理器
 * @description 提供类型安全的事件发布订阅机制
 */

export class EventManager {
  constructor() {
    this.listeners = new Map();
    this.onceListeners = new Map();
  }

  /**
   * 订阅事件
   * @param {string} event - 事件名称
   * @param {Function} callback - 回调函数
   * @returns {Function} 取消订阅的函数
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    
    this.listeners.get(event).add(callback);
    
    // 返回取消订阅函数
    return () => this.off(event, callback);
  }

  /**
   * 订阅一次性事件
   * @param {string} event - 事件名称
   * @param {Function} callback - 回调函数
   * @returns {Function} 取消订阅的函数
   */
  once(event, callback) {
    if (!this.onceListeners.has(event)) {
      this.onceListeners.set(event, new Set());
    }
    
    this.onceListeners.get(event).add(callback);
    
    // 返回取消订阅函数
    return () => this.onceListeners.get(event)?.delete(callback);
  }

  /**
   * 取消订阅
   * @param {string} event - 事件名称
   * @param {Function} callback - 回调函数
   */
  off(event, callback) {
    this.listeners.get(event)?.delete(callback);
    this.onceListeners.get(event)?.delete(callback);
  }

  /**
   * 发布事件
   * @param {string} event - 事件名称
   * @param {any} data - 事件数据
   */
  emit(event, data) {
    // 触发普通监听器
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`事件监听器执行错误 [${event}]:`, error);
        }
      });
    }

    // 触发一次性监听器
    const onceListeners = this.onceListeners.get(event);
    if (onceListeners) {
      onceListeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`一次性事件监听器执行错误 [${event}]:`, error);
        }
      });
      // 清除一次性监听器
      this.onceListeners.delete(event);
    }
  }

  /**
   * 清除所有监听器
   */
  clear() {
    this.listeners.clear();
    this.onceListeners.clear();
  }

  /**
   * 清除指定事件的所有监听器
   * @param {string} event - 事件名称
   */
  clearEvent(event) {
    this.listeners.delete(event);
    this.onceListeners.delete(event);
  }

  /**
   * 获取事件监听器数量
   * @param {string} event - 事件名称
   * @returns {number}
   */
  listenerCount(event) {
    const regularCount = this.listeners.get(event)?.size || 0;
    const onceCount = this.onceListeners.get(event)?.size || 0;
    return regularCount + onceCount;
  }

  /**
   * 获取所有事件名称
   * @returns {string[]}
   */
  eventNames() {
    const regularEvents = Array.from(this.listeners.keys());
    const onceEvents = Array.from(this.onceListeners.keys());
    return [...new Set([...regularEvents, ...onceEvents])];
  }
}

// 创建全局事件管理器实例
export const eventManager = new EventManager();

// 定义应用事件类型
export const APP_EVENTS = {
  // 应用生命周期
  APP_INIT: 'app:init',
  APP_READY: 'app:ready',
  APP_ERROR: 'app:error',
  
  // 文件操作
  FILE_SELECT: 'file:select',
  FILE_UPLOAD_START: 'file:upload:start',
  FILE_UPLOAD_PROGRESS: 'file:upload:progress',
  FILE_UPLOAD_SUCCESS: 'file:upload:success',
  FILE_UPLOAD_ERROR: 'file:upload:error',
  
  // 识别操作
  RECOGNITION_START: 'recognition:start',
  RECOGNITION_SUCCESS: 'recognition:success',
  RECOGNITION_ERROR: 'recognition:error',
  
  // 入库操作
  ENROLLMENT_START: 'enrollment:start',
  ENROLLMENT_SUCCESS: 'enrollment:success',
  ENROLLMENT_ERROR: 'enrollment:error',
  
  // 数据更新
  STATISTICS_UPDATE: 'statistics:update',
  PERSON_LIST_UPDATE: 'person:list:update',
  
  // UI状态
  TAB_CHANGE: 'ui:tab:change',
  MODAL_OPEN: 'ui:modal:open',
  MODAL_CLOSE: 'ui:modal:close',
  TOAST_SHOW: 'ui:toast:show'
};

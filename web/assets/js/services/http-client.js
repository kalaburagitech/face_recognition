/**
 * HTTP客户端服务
 * @description 统一处理所有HTTP请求，支持重试、超时和错误处理
 */

import { CONFIG, ENV } from '../config.js';

/**
 * HTTP客户端类
 */
export class HttpClient {
  constructor() {
    this.baseURL = ENV.getApiBaseUrl();
    this.timeout = CONFIG.API.TIMEOUT;
    this.retryAttempts = CONFIG.API.RETRY_ATTEMPTS;
    this.retryDelay = CONFIG.API.RETRY_DELAY;
  }

  /**
   * 发送HTTP请求
   * @param {string} url - 请求URL
   * @param {RequestInit} options - fetch选项
   * @param {number} retries - 重试次数
   * @returns {Promise<Response>}
   */
  async request(url, options = {}, retries = this.retryAttempts) {
    const fullUrl = this._buildUrl(url);
    
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        console.log(`[HTTP] ${options.method || 'GET'} ${fullUrl}${attempt > 0 ? ` (重试 ${attempt}/${retries - 1})` : ''}`);
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        const response = await fetch(fullUrl, {
          ...options,
          signal: controller.signal,
          headers: this._buildHeaders(options.headers, options.body)
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          console.log(`[HTTP] ✅ ${response.status} ${fullUrl}`);
          return response;
        }
        
        // 如果是最后一次尝试，抛出错误
        if (attempt === retries - 1) {
          const errorText = await this._getErrorText(response);
          throw new HttpError(`HTTP ${response.status}: ${errorText}`, response.status, response);
        }
        
        console.warn(`[HTTP] ⚠️ ${response.status} ${fullUrl} - 准备重试`);
        
      } catch (error) {
        if (attempt === retries - 1) {
          console.error(`[HTTP] ❌ ${fullUrl}`, error);
          throw this._processError(error);
        }
        
        // 重试延迟
        await this._delay(this.retryDelay * (attempt + 1));
      }
    }
  }

  /**
   * GET请求
   */
  async get(url, params = {}) {
    const urlWithParams = this._addQueryParams(url, params);
    return this.request(urlWithParams, { method: 'GET' });
  }

  /**
   * POST请求
   */
  async post(url, data, options = {}) {
    return this.request(url, {
      method: 'POST',
      body: this._processBody(data),
      ...options
    });
  }

  /**
   * PUT请求
   */
  async put(url, data, options = {}) {
    return this.request(url, {
      method: 'PUT',
      body: this._processBody(data),
      ...options
    });
  }

  /**
   * DELETE请求
   */
  async delete(url) {
    return this.request(url, { method: 'DELETE' });
  }

  /**
   * 构建完整URL
   * @private
   */
  _buildUrl(url) {
    if (url.startsWith('http')) return url;
    return `${this.baseURL}${url.startsWith('/') ? '' : '/'}${url}`;
  }

  /**
   * 构建请求头
   * @private
   */
  _buildHeaders(customHeaders = {}, body) {
    const headers = { ...customHeaders };
    
    // 对于FormData，让浏览器自动设置Content-Type
    if (!(body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }
    
    // 如果是FormData，删除Content-Type让浏览器自动设置
    if (body instanceof FormData && headers['Content-Type']) {
      delete headers['Content-Type'];
    }
    
    return headers;
  }

  /**
   * 处理请求体
   * @private
   */
  _processBody(data) {
    if (data instanceof FormData || typeof data === 'string') {
      return data;
    }
    return JSON.stringify(data);
  }

  /**
   * 添加查询参数
   * @private
   */
  _addQueryParams(url, params) {
    const urlObj = new URL(url, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        urlObj.searchParams.set(key, value);
      }
    });
    return urlObj.pathname + urlObj.search;
  }

  /**
   * 获取错误文本
   * @private
   */
  async _getErrorText(response) {
    try {
      const text = await response.text();
      return text || response.statusText;
    } catch {
      return response.statusText;
    }
  }

  /**
   * 处理错误
   * @private
   */
  _processError(error) {
    if (error.name === 'AbortError') {
      return new HttpError('请求超时，请检查网络连接', 0);
    }
    
    if (error.message.includes('Failed to fetch')) {
      return new HttpError('网络连接失败，请检查服务器状态', 0);
    }
    
    return error;
  }

  /**
   * 延迟函数
   * @private
   */
  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/**
 * HTTP错误类
 */
export class HttpError extends Error {
  constructor(message, status = 0, response = null) {
    super(message);
    this.name = 'HttpError';
    this.status = status;
    this.response = response;
  }
}

// 创建默认实例
export const httpClient = new HttpClient();

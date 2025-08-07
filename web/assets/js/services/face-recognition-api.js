/**
 * 人脸识别API服务
 * @description 封装所有与人脸识别相关的API调用
 */

import { httpClient } from './http-client.js';

/**
 * 人脸识别API服务类
 */
export class FaceRecognitionService {
  /**
   * 获取系统统计信息
   * @returns {Promise<object>} 统计信息
   */
  async getStatistics() {
    const response = await httpClient.get('/statistics');
    return response.json();
  }

  /**
   * 更新识别阈值
   * @param {number} threshold - 新的阈值
   * @returns {Promise<object>} 更新结果
   */
  async updateRecognitionThreshold(threshold) {
    const formData = new FormData();
    formData.append('threshold', threshold.toString());
    
    const response = await httpClient.post('/config/threshold', formData);
    return response.json();
  }

  /**
   * 更新重复入库阈值
   * @param {number} threshold - 新的阈值
   * @returns {Promise<object>} 更新结果
   */
  async updateDuplicateThreshold(threshold) {
    const formData = new FormData();
    formData.append('threshold', threshold.toString());
    
    const response = await httpClient.post('/config/duplicate_threshold', formData);
    return response.json();
  }

  /**
   * 人脸识别
   * @param {File} file - 图片文件
   * @param {number} threshold - 识别阈值
   * @returns {Promise<object>} 识别结果
   */
  async recognizeFace(file, threshold = 0.6) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await httpClient.post(`/recognize?threshold=${threshold}`, formData);
    return response.json();
  }

  /**
   * 人脸识别（带可视化）
   * @param {File} file - 图片文件
   * @param {number} threshold - 识别阈值
   * @returns {Promise<Blob>} 可视化图片
   */
  async recognizeFaceWithVisualization(file, threshold = 0.6) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await httpClient.post(`/recognize_visual?threshold=${threshold}`, formData);
    return response.blob();
  }

  /**
   * 人脸入库
   * @param {FormData} formData - 包含文件和人员信息的表单数据
   * @returns {Promise<object>} 入库结果
   */
  async enrollFace(formData) {
    const response = await httpClient.postFormData('/enroll', formData);
    return response.json();
  }

  /**
   * 人员入库 (向后兼容)
   * @param {File} file - 人脸图片文件
   * @param {string} name - 人员姓名
   * @param {string} description - 人员描述
   * @returns {Promise<object>} 入库结果
   */
  async enrollPerson(file, name, description = '') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    if (description) {
      formData.append('description', description);
    }
    
    return this.enrollFace(formData);
  }

  /**
   * 人脸属性分析
   * @param {File} file - 图片文件
   * @returns {Promise<object>} 分析结果
   */
  async analyzeFaceAttributes(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await httpClient.post('/analyze', formData);
    return response.json();
  }

  /**
   * 获取所有人员列表
   * @returns {Promise<object>} 人员列表
   */
  async getPersons() {
    const response = await httpClient.get('/persons');
    return response.json();
  }

  /**
   * 获取指定人员详情
   * @param {number} personId - 人员ID
   * @returns {Promise<object>} 人员详情
   */
  async getPerson(personId) {
    const response = await httpClient.get(`/person/${personId}`);
    return response.json();
  }

  /**
   * 获取指定人员的人脸列表
   * @param {number} personId - 人员ID
   * @returns {Promise<object>} 人脸列表
   */
  async getPersonFaces(personId) {
    const response = await httpClient.get(`/person/${personId}/faces`);
    return response.json();
  }

  /**
   * 获取人脸图片
   * @param {number} faceId - 人脸ID
   * @returns {Promise<Blob>} 图片数据
   */
  async getFaceImage(faceId) {
    const response = await httpClient.get(`/face/${faceId}/image`);
    return response.blob();
  }

  /**
   * 更新人员信息
   * @param {number} personId - 人员ID
   * @param {object} data - 更新数据
   * @returns {Promise<object>} 更新结果
   */
  async updatePerson(personId, data) {
    const response = await httpClient.put(`/person/${personId}`, data);
    return response.json();
  }

  /**
   * 删除人员
   * @param {number} personId - 人员ID
   * @returns {Promise<object>} 删除结果
   */
  async deletePerson(personId) {
    const response = await httpClient.delete(`/person/${personId}`);
    return response.json();
  }

  /**
   * 删除人脸编码
   * @param {number} encodingId - 编码ID
   * @returns {Promise<object>} 删除结果
   */
  async deleteFaceEncoding(encodingId) {
    const response = await httpClient.delete(`/face_encoding/${encodingId}`);
    return response.json();
  }

  /**
   * 获取系统配置
   * @returns {Promise<object>} 系统配置
   */
  async getConfig() {
    const response = await httpClient.get('/config');
    return response.json();
  }

  /**
   * 更新系统配置
   * @param {object} config - 配置数据
   * @returns {Promise<object>} 更新结果
   */
  async updateConfig(config) {
    const response = await httpClient.post('/config', config);
    return response.json();
  }

  /**
   * 健康检查
   * @returns {Promise<object>} 健康状态
   */
  async healthCheck() {
    const response = await httpClient.get('/health');
    return response.json();
  }
}

// 创建默认实例
export const faceRecognitionService = new FaceRecognitionService();

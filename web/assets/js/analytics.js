// 统计分析模块 - 简化版
class Analytics {
    constructor() {
        this.stats = null;
        this.config = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadData();
        this.loadConfiguration();
    }

    bindEvents() {
        // 阈值同步控制 - 识别阈值
        const recognitionRange = document.getElementById('recognitionThresholdRange');
        const recognitionInput = document.getElementById('recognitionThreshold');
        const recognitionDisplay = document.getElementById('recognitionThresholdDisplay');

        if (recognitionRange && recognitionInput && recognitionDisplay) {
            recognitionRange.addEventListener('input', (e) => {
                const value = e.target.value;
                recognitionInput.value = value;
                recognitionDisplay.textContent = value;
            });

            recognitionInput.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                if (!isNaN(value) && value >= 0.1 && value <= 0.9) {
                    recognitionRange.value = value;
                    recognitionDisplay.textContent = value;
                }
            });
        }

        // 检测阈值
        const detectionRange = document.getElementById('detectionThresholdRange');
        const detectionInput = document.getElementById('detectionThreshold');
        const detectionDisplay = document.getElementById('detectionThresholdDisplay');

        if (detectionRange && detectionInput && detectionDisplay) {
            detectionRange.addEventListener('input', (e) => {
                const value = e.target.value;
                detectionInput.value = value;
                detectionDisplay.textContent = value;
            });

            detectionInput.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                if (!isNaN(value) && value >= 0.1 && value <= 0.9) {
                    detectionRange.value = value;
                    detectionDisplay.textContent = value;
                }
            });
        }

        // 重复阈值
        const duplicateRange = document.getElementById('duplicateThresholdRange');
        const duplicateInput = document.getElementById('duplicateThreshold');
        const duplicateDisplay = document.getElementById('duplicateThresholdDisplay');

        if (duplicateRange && duplicateInput && duplicateDisplay) {
            duplicateRange.addEventListener('input', (e) => {
                const value = e.target.value;
                duplicateInput.value = value;
                duplicateDisplay.textContent = value;
            });

            duplicateInput.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                if (!isNaN(value) && value >= 0.8 && value <= 0.99) {
                    duplicateRange.value = value;
                    duplicateDisplay.textContent = value;
                }
            });
        }
    }

    initThresholdControls() {
        const thresholdRange = document.getElementById('thresholdRange');
        const thresholdInput = document.getElementById('threshold');
        const thresholdDisplay = document.getElementById('thresholdDisplay');

        if (thresholdRange && thresholdInput && thresholdDisplay) {
            // 设置初始值
            const initialValue = '0.35';
            thresholdRange.value = initialValue;
            thresholdInput.value = initialValue;
            thresholdDisplay.textContent = initialValue;
        }
    }

    async loadData() {
        try {
            // 显示加载状态
            this.showLoading(true);

            // 并行加载数据
            const [statsResponse, configResponse] = await Promise.all([
                fetch('/api/statistics').catch(() => null),
                fetch('/api/config').catch(() => null)
            ]);

            // 处理统计数据
            if (statsResponse && statsResponse.ok) {
                this.stats = await statsResponse.json();
            } else {
                // 显示错误而不是使用模拟数据
                console.error('无法获取统计数据');
                this.stats = this.getEmptyStats();
                this.displayError('无法获取统计数据，请检查后端服务是否正常运行');
            }

            // 处理配置数据
            if (configResponse && configResponse.ok) {
                this.config = await configResponse.json();
            } else {
                // 使用默认配置
                this.config = this.getDefaultConfig();
            }

            this.displayStatistics();
            this.displayConfiguration();
            this.updateLastUpdateTime();

        } catch (error) {
            console.error('Load analytics data error:', error);
            this.displayError('加载数据失败，请检查网络连接');
            // 显示空数据而不是模拟数据
            this.stats = this.getEmptyStats();
            this.config = this.getDefaultConfig();
            this.displayStatistics();
            this.displayConfiguration();
        } finally {
            this.showLoading(false);
        }
    }

    getEmptyStats() {
        return {
            total_persons: 0,
            total_encodings: 0,
            avg_encodings_per_person: 0,
            recognition_threshold: 0.2,
            detection_threshold: 0.5,
            duplicate_threshold: 0.95,
            system_status: 'unknown'
        };
    }

    getDefaultConfig() {
        return {
            recognition_threshold: 0.2,     // 人脸识别匹配阈值：越低要求越严格
            detection_threshold: 0.5,       // 人脸检测置信度阈值：越高检测越严格 
            duplicate_threshold: 0.95,      // 重复人脸判定阈值：越高防重复越严格
            model_name: 'buffalo_l',
            provider: 'CPUExecutionProvider'
        };
    }

    displayStatistics() {
        if (!this.stats) return;

        // 更新顶部统计卡片
        this.updateElement('statTotalPersons', this.stats.total_persons || 0);
        this.updateElement('statTotalEncodings', this.stats.total_encodings || 0);
        this.updateElement('statThreshold', (this.stats.recognition_threshold || 0.35).toFixed(2));

        // 更新详细统计
        this.updateElement('detailTotalPersons', this.stats.total_persons || 0);
        this.updateElement('detailTotalEncodings', this.stats.total_encodings || 0);
        this.updateElement('avgPhotosPerPerson', (this.stats.avg_encodings_per_person || 0).toFixed(1) + ' 张');
        this.updateElement('currentThreshold', (this.stats.recognition_threshold || 0.35).toFixed(2));
    }

    displayConfiguration() {
        if (!this.config) return;

        // 更新配置表单
        this.updateFormElement('threshold', this.config.recognition_threshold || 0.35);
        this.updateFormElement('thresholdRange', this.config.recognition_threshold || 0.35);
        this.updateFormElement('modelName', this.config.model_name || 'buffalo_l');
        this.updateFormElement('provider', this.config.provider || 'CPUExecutionProvider');

        // 更新阈值显示
        const thresholdDisplay = document.getElementById('thresholdDisplay');
        if (thresholdDisplay) {
            thresholdDisplay.textContent = (this.config.recognition_threshold || 0.35).toFixed(2);
        }

        // 更新系统信息
        this.updateElement('currentModel', this.config.model_name || 'buffalo_l');
        this.updateElement('currentProvider', this.config.provider || 'CPU');
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    updateFormElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.value = value;
        }
    }

    async updateConfiguration() {
        try {
            const recognitionThreshold = parseFloat(document.getElementById('recognitionThreshold').value);
            const detectionThreshold = parseFloat(document.getElementById('detectionThreshold').value);
            const duplicateThreshold = parseFloat(document.getElementById('duplicateThreshold').value);
            
            // 验证三个阈值的有效性
            if (isNaN(recognitionThreshold) || recognitionThreshold < 0.1 || recognitionThreshold > 0.9) {
                throw new Error('识别阈值必须在 0.1 到 0.9 之间');
            }
            if (isNaN(detectionThreshold) || detectionThreshold < 0.1 || detectionThreshold > 0.9) {
                throw new Error('检测阈值必须在 0.1 到 0.9 之间');
            }
            if (isNaN(duplicateThreshold) || duplicateThreshold < 0.8 || duplicateThreshold > 0.99) {
                throw new Error('重复阈值必须在 0.8 到 0.99 之间');
            }

            const config = {
                recognition_threshold: recognitionThreshold,
                detection_threshold: detectionThreshold,
                duplicate_threshold: duplicateThreshold
            };

            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '配置更新失败');
            }

            // 显示成功提示
            this.showNotification('配置更新成功！', 'success');
            
            // 3秒后重新加载配置以确保同步
            setTimeout(() => {
                this.loadConfiguration();
            }, 3000);

        } catch (error) {
            console.error('更新配置失败:', error);
            this.showNotification(error.message || '配置更新失败，请重试！', 'error');
        }
    }

    async loadConfiguration() {
        try {
            const response = await fetch('/api/config');
            if (response.ok) {
                const config = await response.json();
                
                // 设置识别阈值
                const recognitionThreshold = config.recognition_threshold || 0.2;
                const recognitionRange = document.getElementById('recognitionThresholdRange');
                const recognitionInput = document.getElementById('recognitionThreshold');
                const recognitionDisplay = document.getElementById('recognitionThresholdDisplay');
                
                if (recognitionRange && recognitionInput && recognitionDisplay) {
                    recognitionRange.value = recognitionThreshold;
                    recognitionInput.value = recognitionThreshold;
                    recognitionDisplay.textContent = recognitionThreshold;
                }

                // 设置检测阈值
                const detectionThreshold = config.detection_threshold || 0.35;
                const detectionRange = document.getElementById('detectionThresholdRange');
                const detectionInput = document.getElementById('detectionThreshold');
                const detectionDisplay = document.getElementById('detectionThresholdDisplay');
                
                if (detectionRange && detectionInput && detectionDisplay) {
                    detectionRange.value = detectionThreshold;
                    detectionInput.value = detectionThreshold;
                    detectionDisplay.textContent = detectionThreshold;
                }

                // 设置重复阈值
                const duplicateThreshold = config.duplicate_threshold || 0.95;
                const duplicateRange = document.getElementById('duplicateThresholdRange');
                const duplicateInput = document.getElementById('duplicateThreshold');
                const duplicateDisplay = document.getElementById('duplicateThresholdDisplay');
                
                if (duplicateRange && duplicateInput && duplicateDisplay) {
                    duplicateRange.value = duplicateThreshold;
                    duplicateInput.value = duplicateThreshold;
                    duplicateDisplay.textContent = duplicateThreshold;
                }
                
            } else {
                console.warn('无法加载配置，使用默认值');
                this.setDefaultConfiguration();
            }
        } catch (error) {
            console.error('加载配置失败:', error);
            this.setDefaultConfiguration();
        }
    }

    setDefaultConfiguration() {
        const defaultConfig = this.getDefaultConfig();
        
        // 设置识别阈值默认值
        const recognitionRange = document.getElementById('recognitionThresholdRange');
        const recognitionInput = document.getElementById('recognitionThreshold');
        const recognitionDisplay = document.getElementById('recognitionThresholdDisplay');
        
        if (recognitionRange && recognitionInput && recognitionDisplay) {
            recognitionRange.value = defaultConfig.recognition_threshold;
            recognitionInput.value = defaultConfig.recognition_threshold;
            recognitionDisplay.textContent = defaultConfig.recognition_threshold;
        }

        // 设置检测阈值默认值
        const detectionRange = document.getElementById('detectionThresholdRange');
        const detectionInput = document.getElementById('detectionThreshold');
        const detectionDisplay = document.getElementById('detectionThresholdDisplay');
        
        if (detectionRange && detectionInput && detectionDisplay) {
            detectionRange.value = defaultConfig.detection_threshold;
            detectionInput.value = defaultConfig.detection_threshold;
            detectionDisplay.textContent = defaultConfig.detection_threshold;
        }

        // 设置重复阈值默认值
        const duplicateRange = document.getElementById('duplicateThresholdRange');
        const duplicateInput = document.getElementById('duplicateThreshold');
        const duplicateDisplay = document.getElementById('duplicateThresholdDisplay');
        
        if (duplicateRange && duplicateInput && duplicateDisplay) {
            duplicateRange.value = defaultConfig.duplicate_threshold;
            duplicateInput.value = defaultConfig.duplicate_threshold;
            duplicateDisplay.textContent = defaultConfig.duplicate_threshold;
        }
    }

    showLoading(show) {
        const container = document.getElementById('analytics');
        if (container) {
            if (show) {
                container.classList.add('loading');
            } else {
                container.classList.remove('loading');
            }
        }
    }

    updateLastUpdateTime() {
        const element = document.getElementById('lastUpdateTime');
        if (element) {
            element.textContent = new Date().toLocaleString('zh-CN');
        }
    }

    displayError(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type = 'info') {
        // 简单的消息显示
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // 如果有 ToastManager，使用它
        if (window.ToastManager) {
            window.ToastManager.show(message, type);
        } else {
            // 否则使用简单的 alert
            if (type === 'error') {
                alert('错误: ' + message);
            } else if (type === 'warning') {
                alert('警告: ' + message);
            } else if (type === 'success') {
                alert('成功: ' + message);
            }
        }
    }

    showNotification(message, type = 'info') {
        this.showMessage(message, type);
    }

    // 导出统计数据
    exportStats() {
        try {
            const exportData = {
                timestamp: new Date().toISOString(),
                statistics: this.stats,
                configuration: this.config,
                export_time: new Date().toLocaleString('zh-CN')
            };

            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `face_recognition_stats_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showMessage('统计数据导出成功', 'success');

        } catch (error) {
            console.error('Export stats error:', error);
            this.showMessage('导出失败: ' + error.message, 'error');
        }
    }

    // 下载系统报告
    downloadSystemReport() {
        try {
            const reportData = {
                系统概览: {
                    总人员数: this.stats?.total_persons || 0,
                    总照片数: this.stats?.total_encodings || 0,
                    平均每人照片: (this.stats?.avg_encodings_per_person || 0).toFixed(1),
                    识别阈值: (this.stats?.recognition_threshold || 0.35).toFixed(2)
                },
                系统配置: {
                    识别模型: this.config?.model_name || 'buffalo_l',
                    执行提供者: this.config?.provider || 'CPU',
                    最大文件大小: '10MB',
                    支持格式: 'JPEG, PNG, WebP'
                },
                生成时间: new Date().toLocaleString('zh-CN')
            };

            const content = `# 人脸识别系统报告

## 系统概览
- 总人员数: ${reportData.系统概览.总人员数}
- 总照片数: ${reportData.系统概览.总照片数}  
- 平均每人照片: ${reportData.系统概览.平均每人照片}
- 识别阈值: ${reportData.系统概览.识别阈值}

## 系统配置
- 识别模型: ${reportData.系统配置.识别模型}
- 执行提供者: ${reportData.系统配置.执行提供者}
- 最大文件大小: ${reportData.系统配置.最大文件大小}
- 支持格式: ${reportData.系统配置.支持格式}

---
报告生成时间: ${reportData.生成时间}
`;

            const blob = new Blob([content], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `system_report_${new Date().toISOString().split('T')[0]}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showMessage('系统报告下载成功', 'success');

        } catch (error) {
            console.error('Download report error:', error);
            this.showMessage('系统报告下载失败', 'error');
        }
    }

    // 清理缓存
    clearCache() {
        if (confirm('确定要清理系统缓存吗？这将清除临时文件和缓存数据。')) {
            try {
                // 清理本地存储
                localStorage.removeItem('face_recognition_cache');
                sessionStorage.clear();
                
                // 模拟清理过程
                setTimeout(() => {
                    this.showMessage('缓存清理完成', 'success');
                    this.loadData(); // 重新加载数据
                }, 1000);

            } catch (error) {
                console.error('Clear cache error:', error);
                this.showMessage('缓存清理失败', 'error');
            }
        }
    }

    // 显示API文档
    showApiDocs() {
        const docsContent = `
# 人脸识别系统 API 文档

## 基础接口

### 1. 统计数据
- **GET** /api/statistics
- 响应: { total_persons, total_encodings, avg_encodings_per_person, recognition_threshold }

### 2. 系统配置  
- **GET** /api/config
- **POST** /api/config
- 参数: { recognition_threshold, model_name, provider }

### 3. 人脸识别
- **POST** /api/recognize
- 参数: image (file)
- 响应: { person_name, confidence, bbox }

### 4. 人员管理
- **GET** /api/persons - 获取人员列表
- **POST** /api/persons - 注册新人员
- **DELETE** /api/persons/{id} - 删除人员

更多详细信息请查看项目文档。
        `;

        // 创建模态框显示文档
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-book me-2"></i>API 文档
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <pre style="white-space: pre-wrap; font-family: 'JetBrains Mono', monospace; font-size: 0.875rem;">${docsContent}</pre>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        
        if (window.bootstrap) {
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
            
            modal.addEventListener('hidden.bs.modal', () => {
                document.body.removeChild(modal);
            });
        } else {
            // 如果没有 Bootstrap，使用简单显示
            alert(docsContent);
            document.body.removeChild(modal);
        }
    }
}

// 导出到全局作用域
window.Analytics = Analytics;

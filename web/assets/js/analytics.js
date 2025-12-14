// Statistics and analysis module - simplified version
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
        // Threshold sync control - recognition threshold
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

        // Detection threshold
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

        // Duplicate threshold
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
            // Set initial value
            const initialValue = '0.35';
            thresholdRange.value = initialValue;
            thresholdInput.value = initialValue;
            thresholdDisplay.textContent = initialValue;
        }
    }

    async loadData() {
        try {
            // Show loading state
            this.showLoading(true);

            // Load data in parallel
            const [statsResponse, configResponse] = await Promise.all([
                fetch('/api/statistics').catch(() => null),
                fetch('/api/config').catch(() => null)
            ]);

            // Handle statistics data
            if (statsResponse && statsResponse.ok) {
                this.stats = await statsResponse.json();
            } else {
                // Show error instead of using mock data
                console.error('Failed to get statistics data');
                this.stats = this.getEmptyStats();
                this.displayError('Failed to get statistics data, please check whether the backend service is running properly');
            }

            // Handle configuration data
            if (configResponse && configResponse.ok) {
                this.config = await configResponse.json();
            } else {
                // Use default configuration
                this.config = this.getDefaultConfig();
            }

            this.displayStatistics();
            this.displayConfiguration();
            this.updateLastUpdateTime();

        } catch (error) {
            console.error('Load analytics data error:', error);
            this.displayError('Failed to load data, please check the network connection');
            // Show empty data instead of mock data
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
            avg_photos_per_person: 0,
            recognition_threshold: 0.2,
            detection_threshold: 0.5,
            duplicate_threshold: 0.95,
            system_status: 'unknown'
        };
    }

    getDefaultConfig() {
        return {
            recognition_threshold: 0.2,     // Face recognition matching threshold: the lower, the stricter
            detection_threshold: 0.5,       // Face detection confidence threshold: the higher, the stricter 
            duplicate_threshold: 0.95,      // Duplicate face judgment threshold: the higher, the stricter the duplicate prevention
            model_name: 'buffalo_l',
            provider: 'CPUExecutionProvider'
        };
    }

    displayStatistics() {
        if (!this.stats) return;

        // Update top statistics cards
        this.updateElement('statTotalPersons', this.stats.total_persons || 0);
        this.updateElement('statTotalEncodings', this.stats.total_encodings || 0);
        this.updateElement('statThreshold', (this.stats.recognition_threshold || 0.35).toFixed(2));

        // Update detailed statistics
        this.updateElement('detailTotalPersons', this.stats.total_persons || 0);
        this.updateElement('detailTotalEncodings', this.stats.total_encodings || 0);
        this.updateElement('avgPhotosPerPerson', (this.stats.avg_photos_per_person || 0).toFixed(1) + ' images');
        this.updateElement('currentThreshold', (this.stats.recognition_threshold || 0.35).toFixed(2));
    }

    displayConfiguration() {
        if (!this.config) return;

        // Update configuration form
        this.updateFormElement('threshold', this.config.recognition_threshold || 0.35);
        this.updateFormElement('thresholdRange', this.config.recognition_threshold || 0.35);
        this.updateFormElement('modelName', this.config.model_name || 'buffalo_l');
        this.updateFormElement('provider', this.config.provider || 'CPUExecutionProvider');

        // Update threshold display
        const thresholdDisplay = document.getElementById('thresholdDisplay');
        if (thresholdDisplay) {
            thresholdDisplay.textContent = (this.config.recognition_threshold || 0.35).toFixed(2);
        }

        // Update system info
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
            
            // Validate the three thresholds
            if (isNaN(recognitionThreshold) || recognitionThreshold < 0.1 || recognitionThreshold > 0.9) {
                throw new Error('Recognition threshold must be between 0.1 and 0.9');
            }
            if (isNaN(detectionThreshold) || detectionThreshold < 0.1 || detectionThreshold > 0.9) {
                throw new Error('Detection threshold must be between 0.1 and 0.9');
            }
            if (isNaN(duplicateThreshold) || duplicateThreshold < 0.8 || duplicateThreshold > 0.99) {
                throw new Error('Duplicate threshold must be between 0.8 and 0.99');
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
                throw new Error(errorData.detail || 'Configuration update failed');
            }

            // Show success message
            this.showNotification('Configuration updated successfully!', 'success');
            
            // Reload configuration after 3 seconds to ensure synchronization
            setTimeout(() => {
                this.loadConfiguration();
            }, 3000);

        } catch (error) {
            console.error('Failed to update configuration:', error);
            this.showNotification(error.message || 'Configuration update failed, please try again!', 'error');
        }
    }

    async loadConfiguration() {
        try {
            const response = await fetch('/api/config');
            if (response.ok) {
                const config = await response.json();
                
                // Set recognition threshold
                const recognitionThreshold = config.recognition_threshold || 0.2;
                const recognitionRange = document.getElementById('recognitionThresholdRange');
                const recognitionInput = document.getElementById('recognitionThreshold');
                const recognitionDisplay = document.getElementById('recognitionThresholdDisplay');
                
                if (recognitionRange && recognitionInput && recognitionDisplay) {
                    recognitionRange.value = recognitionThreshold;
                    recognitionInput.value = recognitionThreshold;
                    recognitionDisplay.textContent = recognitionThreshold;
                }

                // Set detection threshold
                const detectionThreshold = config.detection_threshold || 0.35;
                const detectionRange = document.getElementById('detectionThresholdRange');
                const detectionInput = document.getElementById('detectionThreshold');
                const detectionDisplay = document.getElementById('detectionThresholdDisplay');
                
                if (detectionRange && detectionInput && detectionDisplay) {
                    detectionRange.value = detectionThreshold;
                    detectionInput.value = detectionThreshold;
                    detectionDisplay.textContent = detectionThreshold;
                }

                // Set duplicate threshold
                const duplicateThreshold = config.duplicate_threshold || 0.85;
                const duplicateRange = document.getElementById('duplicateThresholdRange');
                const duplicateInput = document.getElementById('duplicateThreshold');
                const duplicateDisplay = document.getElementById('duplicateThresholdDisplay');
                
                if (duplicateRange && duplicateInput && duplicateDisplay) {
                    duplicateRange.value = duplicateThreshold;
                    duplicateInput.value = duplicateThreshold;
                    duplicateDisplay.textContent = duplicateThreshold;
                }
                
            } else {
                console.warn('Failed to load configuration, using default values');
                this.setDefaultConfiguration();
            }
        } catch (error) {
            console.error('Failed to load configuration:', error);
            this.setDefaultConfiguration();
        }
    }

    setDefaultConfiguration() {
        const defaultConfig = this.getDefaultConfig();
        
        // Set default recognition threshold
        const recognitionRange = document.getElementById('recognitionThresholdRange');
        const recognitionInput = document.getElementById('recognitionThreshold');
        const recognitionDisplay = document.getElementById('recognitionThresholdDisplay');
        
        if (recognitionRange && recognitionInput && recognitionDisplay) {
            recognitionRange.value = defaultConfig.recognition_threshold;
            recognitionInput.value = defaultConfig.recognition_threshold;
            recognitionDisplay.textContent = defaultConfig.recognition_threshold;
        }

        // Set default detection threshold
        const detectionRange = document.getElementById('detectionThresholdRange');
        const detectionInput = document.getElementById('detectionThreshold');
        const detectionDisplay = document.getElementById('detectionThresholdDisplay');
        
        if (detectionRange && detectionInput && detectionDisplay) {
            detectionRange.value = defaultConfig.detection_threshold;
            detectionInput.value = defaultConfig.detection_threshold;
            detectionDisplay.textContent = defaultConfig.detection_threshold;
        }

        // Set default duplicate threshold
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
            element.textContent = new Date().toLocaleString('en-US');
        }
    }

    displayError(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type = 'info') {
        // Simple message display
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // If there is a ToastManager, use it
        if (window.ToastManager) {
            window.ToastManager.show(message, type);
        } else {
            // Otherwise use simple alert
            if (type === 'error') {
                alert('Error: ' + message);
            } else if (type === 'warning') {
                alert('Warning: ' + message);
            } else if (type === 'success') {
                alert('Success: ' + message);
            }
        }
    }

    showNotification(message, type = 'info') {
        this.showMessage(message, type);
    }

    // Export statistics data
    exportStats() {
        try {
            const exportData = {
                timestamp: new Date().toISOString(),
                statistics: this.stats,
                configuration: this.config,
                export_time: new Date().toLocaleString('en-US')
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

            this.showMessage('Statistics data exported successfully', 'success');

        } catch (error) {
            console.error('Export stats error:', error);
            this.showMessage('Export failed: ' + error.message, 'error');
        }
    }

    // Download system report
    downloadSystemReport() {
        try {
            const reportData = {
                system_overview: {
                    total_persons: this.stats?.total_persons || 0,
                    total_photos: this.stats?.total_encodings || 0,
                    avg_photos_per_person: (this.stats?.avg_photos_per_person || 0).toFixed(1),
                    recognition_threshold: (this.stats?.recognition_threshold || 0.35).toFixed(2)
                },
                system_config: {
                    model_name: this.config?.model_name || 'buffalo_l',
                    execution_provider: this.config?.provider || 'CPU',
                    max_file_size: '10MB',
                    supported_formats: 'JPEG, PNG, WebP'
                },
                generated_time: new Date().toLocaleString('en-US')
            };

            const content = `# Face Recognition System Report

## System Overview
- Total persons: ${reportData.system_overview.total_persons}
- Total photos: ${reportData.system_overview.total_photos}  
- Average photos per person: ${reportData.system_overview.avg_photos_per_person}
- Recognition threshold: ${reportData.system_overview.recognition_threshold}

## System Configuration
- Recognition model: ${reportData.system_config.model_name}
- Execution provider: ${reportData.system_config.execution_provider}
- Max file size: ${reportData.system_config.max_file_size}
- Supported formats: ${reportData.system_config.supported_formats}

---
Report generated at: ${reportData.generated_time}
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

            this.showMessage('System report downloaded successfully', 'success');

        } catch (error) {
            console.error('Download report error:', error);
            this.showMessage('Failed to download system report', 'error');
        }
    }

    // Clear cache
    clearCache() {
        if (confirm('Are you sure you want to clear the system cache? This will remove temporary files and cached data.')) {
            try {
                // Clear local storage
                localStorage.removeItem('face_recognition_cache');
                sessionStorage.clear();
                
                // Simulate cleanup process
                setTimeout(() => {
                    this.showMessage('Cache cleared successfully', 'success');
                    this.loadData(); // Reload data
                }, 1000);

            } catch (error) {
                console.error('Clear cache error:', error);
                this.showMessage('Failed to clear cache', 'error');
            }
        }
    }

    // Show API documentation
    showApiDocs() {
        const docsContent = `
# Face Recognition System API Documentation

## Basic Endpoints

### 1. Statistics
- **GET** /api/statistics
- Response: { total_persons, total_encodings, avg_encodings_per_person, recognition_threshold }

### 2. System Configuration  
- **GET** /api/config
- **POST** /api/config
- Params: { recognition_threshold, model_name, provider }

### 3. Face Recognition
- **POST** /api/recognize
- Params: image (file)
- Response: { person_name, confidence, bbox }

### 4. Person Management
- **GET** /api/persons - Get person list
- **POST** /api/persons - Register new person
- **DELETE** /api/persons/{id} - Delete person

For more details, please refer to the project documentation.
        `;

        // Create modal to display documentation
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-book me-2"></i>API Documentation
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <pre style="white-space: pre-wrap; font-family: 'JetBrains Mono', monospace; font-size: 0.875rem;">${docsContent}</pre>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
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
            // If Bootstrap is not available, use simple display
            alert(docsContent);
            document.body.removeChild(modal);
        }
    }
}

// Export to global scope
window.Analytics = Analytics;

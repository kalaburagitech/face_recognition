// Face recognition module
class FaceRecognition {
    constructor() {
        this.currentFile = null;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Upload area
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('imageFile');
        const recognizeBtn = document.getElementById('recognizeBtn');

        if (uploadZone && fileInput) {
            // Click to upload
            uploadZone.addEventListener('click', () => fileInput.click());
            
            // File selection
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFile(e.target.files[0]);
                }
            });

            // Drag and drop upload
            DragDropHandler.init(uploadZone, (files) => {
                if (files.length > 0) {
                    this.handleFile(files[0]);
                }
            });
        }

        // Identify button
        if (recognizeBtn) {
            recognizeBtn.addEventListener('click', () => this.performRecognition());
        }

        // reset button
        const resetBtn = document.querySelector('[onclick="clearRecognition()"]');
        if (resetBtn) {
            resetBtn.onclick = () => this.clearRecognition();
        }
    }

    handleFile(file) {
        const validation = FileValidator.validate(file);
        
        if (!validation.valid) {
            validation.errors.forEach(error => {
                ToastManager.show(error, 'error');
            });
            return;
        }

        this.currentFile = file;
        this.showPreview(file);
        this.enableRecognitionButton();
        this.showFileInfo(file);
    }

    showPreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = document.getElementById('previewImg');
            const preview = document.getElementById('imagePreview');
            
            if (img && preview) {
                img.src = e.target.result;
                preview.style.display = 'block';
                
                // Add fade-in animation
                preview.classList.add('fade-in');
            }
        };
        reader.readAsDataURL(file);
    }

    showFileInfo(file) {
        const infoDiv = document.getElementById('imageInfo');
        if (infoDiv) {
            const fileSize = (file.size / 1024 / 1024).toFixed(2);
            infoDiv.innerHTML = `
                <i class="bi bi-info-circle me-1"></i>
                file name: ${file.name} | 
                size: ${fileSize} MB | 
                type: ${file.type}
            `;
        }
    }

    enableRecognitionButton() {
        const btn = document.getElementById('recognizeBtn');
        const clearBtn = document.getElementById('clearBtn');
        if (btn) {
            btn.disabled = false;
        }
        if (clearBtn) {
            clearBtn.style.display = 'block';
        }
    }

    async performRecognition() {
        if (!this.currentFile) {
            ToastManager.show('Please select a picture first', 'warning');
            return;
        }

        // Check if region is selected
        const regionSelect = document.getElementById('recognitionRegion');
        if (!regionSelect || !regionSelect.value) {
            ToastManager.show('Please select a region', 'warning');
            return;
        }

        const btn = document.getElementById('recognizeBtn');
        const loadingOverlay = document.getElementById('recognitionLoading');
        
        // show loading status
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
        }
        
        LoadingManager.setButtonLoading(btn, true, 'Recognizing...');

        try {
            const formData = new FormData();
            formData.append('file', this.currentFile);
            formData.append('region', regionSelect.value);
            
            // Add optional emp_id if provided
            const empIdInput = document.getElementById('recognitionEmpId');
            if (empIdInput && empIdInput.value.trim()) {
                formData.append('emp_id', empIdInput.value.trim());
            }

            // First get the recognition results
            const result = await ApiClient.post('/api/recognize', formData);
            
            // Then get the visualization picture
            const visualResponse = await fetch('/api/recognize_visual', {
                method: 'POST',
                body: formData
            });
            
            if (visualResponse.ok) {
                const blob = await visualResponse.blob();
                const visualUrl = URL.createObjectURL(blob);
                this.displayResults(result, visualUrl);
            } else {
                this.displayResults(result);
            }
            
            ToastManager.show('Recognition completed', 'success');
            this.showDownloadButton();

        } catch (error) {
            console.error('Recognition error:', error);
            ToastManager.show(`Recognition failed: ${error.message}`, 'error');
            this.displayError('Recognition failed，Please try again');
        } finally {
            LoadingManager.setButtonLoading(btn, false);
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }
    }

    showDownloadButton() {
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.style.display = 'block';
        }
    }

    displayResults(result, visualUrl = null) {
        const container = document.getElementById('recognitionResults');
        if (!container) return;

        let resultsHtml = '';
        
        // If there is a visual picture，show first
        if (visualUrl) {
            resultsHtml += `
                <div class="mb-4">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="text-primary mb-0">
                            <i class="bi bi-image me-2"></i>Identify visualization results
                        </h6>
                        <button class="btn btn-outline-primary btn-sm" onclick="downloadVisualization('${visualUrl}')">
                            <i class="bi bi-download me-1"></i>download
                        </button>
                    </div>
                    <div class="text-center">
                        <img src="${visualUrl}" class="img-fluid rounded shadow" alt="Visualization of recognition results" style="max-height: 350px; cursor: pointer;" onclick="showImageModal('${visualUrl}')">
                        <div class="small text-muted mt-2">Click on the image to view a larger version</div>
                    </div>
                </div>
            `;
        }

        // Display recognition result details
        if (result.matches && result.matches.length > 0) {
            resultsHtml += `
                <div class="mb-3">
                    <h6 class="text-success mb-3">
                        <i class="bi bi-person-check me-2"></i>Recognition successful - turn up ${result.matches.length} matches
                    </h6>
                    <div class="row">
                        ${result.matches.map((match, index) => `
                            <div class="col-12 mb-3">
                                ${this.createResultCard(match, index + 1)}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;

            // Show summary information
            resultsHtml += `
                <div class="alert alert-info">
                    <div class="row text-center">
                        <div class="col-4">
                            <div class="fw-bold">${result.total_faces || 1}</div>
                            <div class="small">Detect faces</div>
                        </div>
                        <div class="col-4">
                            <div class="fw-bold">${result.matches.length}</div>
                            <div class="small">Match people</div>
                        </div>
                        <div class="col-4">
                            <div class="fw-bold">${Math.max(...result.matches.map(m => m.match_score)).toFixed(1)}%</div>
                            <div class="small">highest similarity</div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            resultsHtml += `
                <div class="alert alert-warning text-center">
                    <i class="bi bi-exclamation-triangle fs-1 text-warning mb-3"></i>
                    <h5 class="mb-2">No matching people found</h5>
                    <p class="mb-3">There is no matching record for this face in the database</p>
                    <div class="d-grid gap-2">
                        <button class="btn btn-primary" onclick="showEnrollmentModal()">
                            <i class="bi bi-person-plus me-2"></i>Register this person
                        </button>
                        <small class="text-muted">It is recommended to check the photo quality or register the person first</small>
                    </div>
                </div>
            `;
        }

        container.innerHTML = resultsHtml;
        container.classList.add('fade-in');
    }

    createResultCard(match, index) {
        const scoreClass = this.getScoreClass(match.match_score);
        return `
            <div class="result-card" id="result-card-${match.emp_id}">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div class="d-flex align-items-center">
                        <div class="badge bg-primary me-2">#${index}</div>
                        <div>
                            <h6 class="mb-1 text-primary fw-bold">${match.name}</h6>
                            <small class="text-muted">Employee ID: ${match.emp_id}${match.face_encoding_id ? ` | human faceID: ${match.face_encoding_id}` : ''}</small>
                        </div>
                    </div>
                    <span class="match-score ${scoreClass}">
                        ${match.match_score.toFixed(1)}%
                    </span>
                </div>
                
                <div class="row g-3 text-sm">
                    <div class="col-md-6">
                        <div class="d-flex justify-content-between">
                            <span class="text-muted">similarity distance:</span>
                            <span class="fw-semibold">${match.distance.toFixed(4)}</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="d-flex justify-content-between">
                            <span class="text-muted">Image quality:</span>
                            <span class="fw-semibold">${((match.quality || 0) * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="d-flex justify-content-between">
                            <span class="text-muted">detection frame:</span>
                            <span class="fw-semibold">${match.bbox ? `${match.bbox[2]-match.bbox[0]}×${match.bbox[3]-match.bbox[1]}` : 'N/A'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="mt-3">
                    <div class="progress" style="height: 8px;">
                        <div class="progress-bar ${this.getProgressBarClass(match.match_score)}" 
                             style="width: ${match.match_score}%"></div>
                    </div>
                    <div class="d-flex justify-content-between mt-1">
                        <small class="text-muted">Confidence</small>
                        <small class="text-muted">${this.getConfidenceText(match.match_score)}</small>
                    </div>
                </div>
                
                <div class="mt-3" id="attendance-section-${match.emp_id}">
                    <button class="btn btn-success w-100" onclick="faceRecognition.markAttendance('${match.emp_id}', '${match.name}')">
                        <i class="bi bi-check-circle me-2"></i>Submit Attendance
                    </button>
                </div>
            </div>
        `;
    }

    async markAttendance(empId, personName) {
        const attendanceSection = document.getElementById(`attendance-section-${empId}`);
        if (!attendanceSection) return;

        // Show loading state
        attendanceSection.innerHTML = `
            <button class="btn btn-secondary w-100" disabled>
                <span class="spinner-border spinner-border-sm me-2"></span>Checking...
            </button>
        `;

        try {
            // Mark attendance
            const formData = new FormData();
            formData.append('emp_id', empId);
            formData.append('status', 'present');

            const response = await fetch('/api/attendance/mark', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            // Debug logging
            console.log('Attendance API Response:', result);
            console.log('already_marked flag:', result.already_marked);

            if (result.success) {
                if (result.already_marked === true) {
                    // Attendance already marked
                    attendanceSection.innerHTML = `
                        <div class="alert alert-info mb-0">
                            <i class="bi bi-info-circle me-2"></i>
                            <strong>Attendance Already Marked</strong><br>
                            <small>Marked at: ${new Date(result.attendance.marked_at).toLocaleString()}</small>
                        </div>
                    `;
                    ToastManager.show(`Attendance already marked for ${personName}`, 'info');
                } else {
                    // Successfully marked
                    attendanceSection.innerHTML = `
                        <div class="alert alert-success mb-0">
                            <i class="bi bi-check-circle me-2"></i>
                            <strong>Attendance Marked Successfully</strong><br>
                            <small>Marked at: ${new Date(result.attendance.marked_at).toLocaleString()}</small>
                        </div>
                    `;
                    ToastManager.show(`Attendance marked for ${personName}`, 'success');
                }
            } else {
                throw new Error(result.error || 'Failed to mark attendance');
            }
        } catch (error) {
            console.error('Attendance marking error:', error);
            attendanceSection.innerHTML = `
                <div class="alert alert-danger mb-0">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Failed to mark attendance: ${error.message}
                </div>
                <button class="btn btn-warning w-100 mt-2" onclick="faceRecognition.markAttendance('${empId}', '${personName}')">
                    <i class="bi bi-arrow-clockwise me-2"></i>Retry
                </button>
            `;
            ToastManager.show(`Failed to mark attendance: ${error.message}`, 'error');
        }
    }

    getScoreClass(score) {
        if (score >= 80) return 'match-high';
        if (score >= 60) return 'match-medium';
        return 'match-low';
    }

    getProgressBarClass(score) {
        if (score >= 80) return 'bg-success';
        if (score >= 60) return 'bg-warning';
        return 'bg-danger';
    }

    getConfidenceText(score) {
        if (score >= 90) return 'very high';
        if (score >= 80) return 'high';
        if (score >= 60) return 'medium';
        if (score >= 40) return 'lower';
        return 'Low';
    }

    displayError(message) {
        const container = document.getElementById('recognitionResults');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    ${message}
                </div>
            `;
        }
    }

    clearRecognition() {
        this.currentFile = null;
        
        const fileInput = document.getElementById('imageFile');
        const preview = document.getElementById('imagePreview');
        const btn = document.getElementById('recognizeBtn');
        const clearBtn = document.getElementById('clearBtn');
        const downloadBtn = document.getElementById('downloadBtn');
        const results = document.getElementById('recognitionResults');
        const imageInfo = document.getElementById('imageInfo');

        if (fileInput) fileInput.value = '';
        if (preview) preview.style.display = 'none';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-search me-2"></i>Start identifying';
        }
        if (clearBtn) clearBtn.style.display = 'none';
        if (downloadBtn) downloadBtn.style.display = 'none';
        if (imageInfo) imageInfo.innerHTML = '';
        
        if (results) {
            results.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-search"></i>
                    <h6>Waiting for recognition</h6>
                    <p class="mb-0">Please upload a photo to start identification</p>
                </div>
            `;
        }

        ToastManager.show('The recognition interface has been reset', 'info');
    }
}

// Export to global scope
window.FaceRecognition = FaceRecognition;

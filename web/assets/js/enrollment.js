// Personnel registration module
class PersonEnrollment {
    constructor() {
        this.enrollmentFiles = [];
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Upload area
        const uploadZone = document.getElementById('enrollmentUpload');
        const fileInput = document.getElementById('enrollmentFile');
        const enrollBtn = document.getElementById('enrollBtn');

        if (uploadZone && fileInput) {
            // Click to upload
            uploadZone.addEventListener('click', () => fileInput.click());
            
            // File selection
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFiles(e.target.files);
                }
            });

            // Drag and drop upload
            DragDropHandler.init(uploadZone, (files) => {
                this.handleFiles(files);
            });
        }

        // Register button
        if (enrollBtn) {
            enrollBtn.addEventListener('click', () => this.performEnrollment());
        }

        // form validation
        const nameInput = document.getElementById('personName');
        if (nameInput) {
            nameInput.addEventListener('input', () => this.updateEnrollmentButton());
        }

        // reset button
        const resetBtn = document.querySelector('[onclick="clearEnrollment()"]');
        if (resetBtn) {
            resetBtn.onclick = () => this.clearEnrollment();
        }
    }

    handleFiles(files) {
        const validation = FileValidator.validateMultiple(files);
        
        if (validation.hasErrors) {
            validation.errors.forEach(error => {
                ToastManager.show(error, 'error');
            });
        }

        if (validation.validFiles.length > 0) {
            this.enrollmentFiles = validation.validFiles;
            this.showPreviews(validation.validFiles);
            this.updateEnrollmentButton();
            
            // If it is a single picture and the name is empty，Automatically extract from filename
            if (validation.validFiles.length === 1) {
                const nameInput = document.getElementById('personName');
                if (nameInput && !nameInput.value.trim()) {
                    const fileName = validation.validFiles[0].name;
                    const nameFromFile = fileName.replace(/\.(jpg|jpeg|png|gif|bmp|webp|avif)$/i, '')
                                                .replace(/[_-]/g, ' ')
                                                .trim();
                    if (nameFromFile) {
                        nameInput.value = nameFromFile;
                        ToastManager.show(`Name auto-filled from file name：${nameFromFile}`, 'info');
                        this.updateEnrollmentButton();
                    }
                }
            }
        }
    }

    async showPreviews(files) {
        const container = document.getElementById('enrollmentImages');
        const preview = document.getElementById('enrollmentPreview');
        const photoCount = document.getElementById('photoCount');
        
        if (!container || !preview) {
            console.error('Preview container elements not found');
            return;
        }

        // Clear existing previews
        ImagePreview.clear(container);
        
        // Update photo count
        if (photoCount) {
            photoCount.textContent = `${files.length} photo${files.length !== 1 ? 's' : ''} selected`;
        }
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const col = document.createElement('div');
            col.className = 'col-md-4 col-sm-6 mb-3';
            
            try {
                await ImagePreview.createPreview(file, col, {
                    maxHeight: '150px',
                    className: 'img-fluid image-preview w-100',
                    onRemove: (element, file) => this.removeImage(element, file)
                });
                container.appendChild(col);
            } catch (error) {
                console.error('Preview error:', error);
                if (window.ToastManager) {
                    ToastManager.show('Image preview failed', 'error');
                } else {
                    alert('Image preview failed');
                }
            }
        }
        
        // Show the preview section
        preview.classList.remove('d-none');
        preview.style.display = 'block';
    }

    removeImage(element, file) {
        // Remove from file list
        const index = this.enrollmentFiles.indexOf(file);
        if (index > -1) {
            this.enrollmentFiles.splice(index, 1);
        }
        
        // RemoveDOMelement
        element.remove();
        
        // Update photo quantity
        const photoCount = document.getElementById('photoCount');
        if (photoCount) {
            photoCount.textContent = `${this.enrollmentFiles.length} photo${this.enrollmentFiles.length !== 1 ? 's' : ''} selected`;
        }
        
        // If there are no files left，Hide preview area
        if (this.enrollmentFiles.length === 0) {
            const preview = document.getElementById('enrollmentPreview');
            if (preview) {
                preview.classList.add('d-none');
                preview.style.display = 'none';
            }
            
            // Reset file input
            const fileInput = document.getElementById('enrollmentFile');
            if (fileInput) {
                fileInput.value = '';
            }
        }
        
        this.updateEnrollmentButton();
    }

    updateEnrollmentButton() {
        const btn = document.getElementById('enrollBtn');
        const nameInput = document.getElementById('personName');
        
        if (btn && nameInput) {
            const hasName = nameInput.value.trim().length > 0;
            const hasFiles = this.enrollmentFiles.length > 0;
            
            // If there are multiple photos，As long as there are files, you can perform batch storage（No name required）
            if (this.enrollmentFiles.length > 1) {
                btn.disabled = !hasFiles;
                btn.textContent = `Batch registration (${this.enrollmentFiles.length}open)`;
            } else if (this.enrollmentFiles.length === 1) {
                // single photo：Just have files，If there is no name it will be extracted from the file name
                btn.disabled = !hasFiles;
                btn.textContent = hasName ? 'Registered Person' : 'Registered Person (use filename)';
            } else {
                btn.disabled = true;
                btn.textContent = 'Registered Person';
            }
        }
    }

    async performEnrollment() {
        console.log('Start the registration process...');
        
        const nameInput = document.getElementById('personName');
        const descInput = document.getElementById('personDescription');
        
        if (!nameInput) {
            console.error('Name input box element not found');
            if (window.ToastManager) {
                ToastManager.show('Page elements missing', 'error');
            } else {
                alert('Page elements missing');
            }
            return;
        }

        const name = nameInput.value.trim();
        const description = descInput ? descInput.value.trim() : '';
        
        console.log('Registration information:', { name, description });
        
        // Check if we're in video mode and have captured frames
        const videoMode = document.getElementById('videoMode');
        const isVideoMode = videoMode && videoMode.checked;
        
        console.log('Registration mode check:', { isVideoMode, videoModeExists: !!videoMode, videoModeChecked: videoMode?.checked });
        
        if (isVideoMode) {
            console.log('Use video registration mode');
            // Handle video registration
            return this.performVideoEnrollment(name, description);
        } else {
            console.log('Using photo registration mode');
        }

        if (this.enrollmentFiles.length === 0) {
            ToastManager.show('Please upload at least one photo', 'warning');
            return;
        }

        const btn = document.getElementById('enrollBtn');

        try {
            if (this.enrollmentFiles.length === 1) {
                // Single photo registration
                let finalName = name;
                
                // if name is empty，Extract from file name
                if (!finalName) {
                    const fileName = this.enrollmentFiles[0].name;
                    finalName = fileName.replace(/\.(jpg|jpeg|png|gif|bmp|webp|avif)$/i, '')
                                       .replace(/[_-]/g, ' ')
                                       .trim();
                    if (!finalName) {
                        ToastManager.show('Unable to extract name from file name，Please enter manually', 'warning');
                        nameInput.focus();
                        return;
                    }
                }

                LoadingManager.setButtonLoading(btn, true, 'Registering...');

                // Get region, emp_id, and emp_rank
                const regionInput = document.getElementById('personRegion');
                const empIdInput = document.getElementById('empId');
                const empRankInput = document.getElementById('empRank');
                
                const region = regionInput ? regionInput.value.trim() : '';
                const empId = empIdInput ? empIdInput.value.trim() : '';
                const empRank = empRankInput ? empRankInput.value.trim() : '';
                
                if (!region || !empId || !empRank) {
                    ToastManager.show('Please fill in all required fields: Region, Employee ID, and Employee Rank', 'warning');
                    LoadingManager.setButtonLoading(btn, false);
                    return;
                }

                const formData = new FormData();
                formData.append('name', finalName);
                formData.append('region', region);
                formData.append('emp_id', empId);
                formData.append('emp_rank', empRank);
                if (description) formData.append('description', description);
                formData.append('file', this.enrollmentFiles[0]);

                const result = await ApiClient.post('/api/enroll', formData);
                this.displayResults(result);
                ToastManager.show('Personnel registration successful', 'success');
            } else {
                // Batch registration
                LoadingManager.setButtonLoading(btn, true, `Batch registration in progress (${this.enrollmentFiles.length}open)...`);

                // Get region, emp_id, and emp_rank
                const regionInput = document.getElementById('personRegion');
                const empIdInput = document.getElementById('empId');
                const empRankInput = document.getElementById('empRank');
                
                const region = regionInput ? regionInput.value.trim() : '';
                const empId = empIdInput ? empIdInput.value.trim() : '';
                const empRank = empRankInput ? empRankInput.value.trim() : '';
                
                if (!region || !empId || !empRank) {
                    ToastManager.show('Please fill in all required fields: Region, Employee ID, and Employee Rank', 'warning');
                    LoadingManager.setButtonLoading(btn, false);
                    return;
                }
                
                // For batch enrollment, name is required
                if (!name) {
                    ToastManager.show('Please enter the person name for batch enrollment', 'warning');
                    nameInput.focus();
                    LoadingManager.setButtonLoading(btn, false);
                    return;
                }

                const formData = new FormData();
                
                // add all files
                this.enrollmentFiles.forEach((file, index) => {
                    formData.append('files', file);
                });

                // Add name (required for batch enrollment)
                formData.append('name', name);
                
                // Add region, emp_id, and emp_rank
                formData.append('region', region);
                formData.append('emp_id', empId);
                formData.append('emp_rank', empRank);

                // If you fill in the description，then use this description as the description of the first file
                if (description) {
                    formData.append('description', description);
                }

                const result = await ApiClient.post('/api/batch_enroll', formData);
                this.displayBatchResults(result);
                
                // Check if duplicate faces are detected
                if (result.duplicate_detected) {
                    // Error message distinguishing between video registration and regular batch registration
                    if (result.is_video_registration) {
                        ToastManager.show(`Video registration failed: Too similar face frames detected。Please try recording again with different angles or expressions`, 'error');
                    } else {
                        ToastManager.show(`Batch registration failed: ${result.message}`, 'error');
                    }
                } else if (result.success && result.success_count > 0) {
                    if (result.is_video_registration) {
                        ToastManager.show(`Video registration completed：successfully processed ${result.success_count} frame，fail ${result.error_count} frame`, 
                            result.error_count === 0 ? 'success' : 'warning');
                    } else {
                        ToastManager.show(`Batch registration completed：success ${result.success_count} indivual，fail ${result.error_count} indivual`, 
                            result.error_count === 0 ? 'success' : 'warning');
                    }
                } else {
                    ToastManager.show('Registration failed', 'error');
                }
            }

        } catch (error) {
            console.error('Enrollment error:', error);
            ToastManager.show(`Registration failed: ${error.message}`, 'error');
            this.displayError(error.message);
        } finally {
            LoadingManager.setButtonLoading(btn, false);
            // restore button text
            if (this.enrollmentFiles.length > 1) {
                btn.textContent = `Batch registration (${this.enrollmentFiles.length}open)`;
            } else {
                btn.textContent = 'Registered Person';
            }
        }
    }
    
    async performVideoEnrollment(name, description) {
        console.log('Start video registration...', { name, description });
        
        // Check if we have captured frames from video registration
        if (!window.registrationFrames || window.registrationFrames.length === 0) {
            ToastManager.show('Please complete the video recording capture frame data first', 'warning');
            return;
        }
        
        if (!name.trim()) {
            ToastManager.show('Please enter persons name', 'warning');
            const nameInput = document.getElementById('personName');
            if (nameInput) nameInput.focus();
            return;
        }
        
        const btn = document.getElementById('enrollBtn');
        const frameCount = window.registrationFrames.length;
        
        try {
            // Use LoadingManager if available, otherwise fallback to basic button state
            if (window.LoadingManager) {
                LoadingManager.setButtonLoading(btn, true, `in use ${frameCount} Frame video data registration...`);
            } else {
                btn.disabled = true;
                btn.innerHTML = `<i class="bi bi-hourglass-split me-2"></i>in use ${frameCount} Frame video data registration...`;
            }
            
            if (frameCount === 1) {
                // Single frame enrollment
                const result = await this.enrollWithSingleFrame(window.registrationFrames[0], name, description);
                this.displayResults(result);
                if (window.ToastManager) {
                    ToastManager.show('Video registration successful！', 'success');
                } else {
                    alert('Video registration successful！');
                }
            } else {
                // Multiple frames enrollment (batch)
                const result = await this.enrollWithMultipleFrames(window.registrationFrames, name, description);
                this.displayVideoEnrollmentResults(result, frameCount);
                if (window.ToastManager) {
                    ToastManager.show(`Video registration completed！used ${frameCount} frame data`, 'success');
                } else {
                    alert(`Video registration completed！used ${frameCount} frame data`);
                }
            }
            
        } catch (error) {
            console.error('Video enrollment error:', error);
            const errorMessage = error.message || 'unknown error';
            if (window.ToastManager) {
                ToastManager.show(`Video registration failed: ${errorMessage}`, 'error');
            } else {
                alert(`Video registration failed: ${errorMessage}`);
            }
            this.displayError(errorMessage);
        } finally {
            // Reset button state
            if (window.LoadingManager) {
                LoadingManager.setButtonLoading(btn, false);
            } else {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-person-plus me-1"></i>Registered Person';
            }
        }
    }
    
    async enrollWithSingleFrame(frameBlob, name, description) {
        if (!frameBlob || !name) {
            throw new Error('Missing required parameters：frame data or name');
        }
        
        // Get region, emp_id, and emp_rank
        const regionInput = document.getElementById('personRegion');
        const empIdInput = document.getElementById('empId');
        const empRankInput = document.getElementById('empRank');
        
        const region = regionInput ? regionInput.value.trim() : '';
        const empId = empIdInput ? empIdInput.value.trim() : '';
        const empRank = empRankInput ? empRankInput.value.trim() : '';
        
        if (!region || !empId || !empRank) {
            throw new Error('Please fill in all required fields: Region, Employee ID, and Employee Rank');
        }
        
        const formData = new FormData();
        formData.append('name', name);
        formData.append('region', region);
        formData.append('emp_id', empId);
        formData.append('emp_rank', empRank);
        if (description) formData.append('description', description);
        
        // Convert blob to file
        const file = this.blobToFile(frameBlob, `video_frame_${Date.now()}.jpg`);
        formData.append('file', file);
        
        console.log('Send single frame registration request:', { name, region, empId, empRank, description, fileSize: file.size });
        const result = await ApiClient.post('/api/enroll', formData);
        console.log('Single frame registration response:', result);
        return result;
    }
    
    async enrollWithMultipleFrames(frameBlobs, name, description) {
        if (!frameBlobs || frameBlobs.length === 0 || !name) {
            throw new Error('Missing required parameters：frame data or name');
        }
        
        // Get region, emp_id, and emp_rank
        const regionInput = document.getElementById('personRegion');
        const empIdInput = document.getElementById('empId');
        const empRankInput = document.getElementById('empRank');
        
        const region = regionInput ? regionInput.value.trim() : '';
        const empId = empIdInput ? empIdInput.value.trim() : '';
        const empRank = empRankInput ? empRankInput.value.trim() : '';
        
        if (!region || !empId || !empRank) {
            throw new Error('Please fill in all required fields: Region, Employee ID, and Employee Rank');
        }
        
        const formData = new FormData();
        formData.append('name', name);
        formData.append('region', region);
        formData.append('emp_id', empId);
        formData.append('emp_rank', empRank);
        if (description) formData.append('description', description);
        
        // Convert all blobs to files and append them
        frameBlobs.forEach((blob, index) => {
            const file = this.blobToFile(blob, `video_frame_${index + 1}_${Date.now()}.jpg`);
            formData.append('files', file);
        });
        
        console.log('Send multi-frame batch registration request:', { name, region, empId, empRank, description, frameCount: frameBlobs.length });
        const result = await ApiClient.post('/api/batch_enroll', formData);
        console.log('Multi-frame registration response:', result);
        
        // Check for duplicate detection
        if (result.duplicate_detected) {
            throw new Error(result.message || 'Duplicate faces detected，Please try again with a different face');
        }
        
        return result;
    }
    
    blobToFile(blob, fileName) {
        if (!blob) {
            throw new Error('Invalidblobdata');
        }
        
        // Create a File object from blob
        const file = new File([blob], fileName, { 
            type: blob.type || 'image/jpeg',
            lastModified: Date.now()
        });
        
        console.log('Convertblobfor files:', { fileName, size: file.size, type: file.type });
        return file;
    }
    
    displayVideoEnrollmentResults(result, frameCount) {
        const container = document.getElementById('enrollmentResults');
        if (!container) return;
        
        if (result.success) {
            let html = `
                <div class="alert alert-${result.error_count === 0 ? 'success' : 'warning'}">
                    <i class="bi bi-${result.error_count === 0 ? 'camera-video-fill' : 'exclamation-triangle'} me-2"></i>
                    <strong>Video registration completed！</strong>
                    <br>use ${frameCount} frame video data，success ${result.success_count} indivual，fail ${result.error_count} indivual
                    <br><small class="text-muted">🎥 Video registration can provide higher recognition accuracy</small>
                </div>
            `;
            
            if (result.results && result.results.length > 0) {
                html += `<div class="mt-3"><h6 class="mb-2">Video frame processing results：</h6><div class="row">`;
                
                result.results.forEach((item, index) => {
                    const statusClass = item.success ? 'success' : 'danger';
                    const statusIcon = item.success ? 'check-circle-fill' : 'x-circle-fill';
                    
                    html += `
                        <div class="col-12 mb-2">
                            <div class="card border-${statusClass}">
                                <div class="card-body p-2">
                                    <div class="d-flex align-items-center">
                                        <i class="bi bi-${statusIcon} text-${statusClass} me-2"></i>
                                        <div class="flex-grow-1">
                                            <div class="fw-bold">
                                                🎥 No. ${index + 1} frame
                                            </div>
                                            <div class="small text-muted">
                                                ${item.name ? `👤 Name: <strong>${item.name}</strong>` : ''}
                                                ${item.success ? 
                                                    `${item.person_id ? ` | 🆔 ID: ${item.person_id}` : ''}${item.quality_score ? ` | 📊 quality: ${(item.quality_score * 100).toFixed(1)}%` : ''}` :
                                                    ` | ❌ mistake: ${item.error}`
                                                }
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                html += `</div></div>`;
            }
            
            html += `
                <div class="small text-muted mt-3">
                    <div><strong>processing time:</strong> ${new Date().toLocaleString()}</div>
                    <div><strong>state:</strong> ${result.message || 'Video registration completed'}</div>
                    <div><strong>Data source:</strong> 5Second video recording (${frameCount} frame)</div>
                </div>
            `;
            
            container.innerHTML = html;
        } else {
            this.displayError(result.error || 'Video registration failed');
        }
    }

    displayBatchResults(result) {
        const container = document.getElementById('enrollmentResults');
        if (!container) return;

        // Check if it is video registration mode
        const isVideoRegistration = result.is_video_registration || false;

        // Check if it is a duplicate detection error
        if (result.duplicate_detected) {
            let errorTitle = 'Duplicate face detection';
            let errorIcon = 'exclamation-triangle';
            let helpText = '💡 Please try again with a different face picture or a different person name';
            
            if (isVideoRegistration) {
                errorTitle = 'Video registration detects duplicate frames';
                errorIcon = 'camera-video-off';
                helpText = '💡 Please try different angles、Re-record video with expression or gesture';
            }
            
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-${errorIcon} me-2"></i>
                    <strong>${errorTitle}</strong>
                    <br>${result.message}
                    <br><small class="text-muted mt-2">${helpText}</small>
                </div>
                <div class="mt-3">
                    <h6 class="mb-2 text-danger">Failure details：</h6>
                    <div class="card border-danger">
                        <div class="card-body p-2">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-x-circle-fill text-danger me-2"></i>
                                <div class="flex-grow-1">
                                    <div class="fw-bold">
                                        ${isVideoRegistration ? '🎥' : '📁'} ${result.results[0]?.file_name || 'unknown file'}
                                    </div>
                                    <div class="small text-muted">
                                        👤 name: <strong>${result.results[0]?.name || 'unknown'}</strong>
                                         | ❌ mistake: ${result.results[0]?.error || result.message}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="small text-muted mt-3">
                    <div><strong>processing time:</strong> ${new Date().toLocaleString()}</div>
                    <div><strong>state:</strong> ${isVideoRegistration ? 'Video registration detects duplicate frames' : 'Duplicate faces detected，Batch processing stopped'}</div>
                    ${isVideoRegistration ? '<div><strong>suggestion:</strong> Adjust the camera angle or change your facial expression and try again</div>' : ''}
                </div>
            `;
            return;
        }

        if (result.success) {
            let modeText = 'Batch registration';
            let successIcon = 'check-circle';
            let processingNote = '💡 The system has automatically sorted files by name.，Ensure data sequence consistency';
            
            if (isVideoRegistration) {
                modeText = 'Video registration';
                successIcon = 'camera-video-fill';
                processingNote = '🎥 Video registration can provide higher recognition accuracy and robustness';
            }
            
            let html = `
                <div class="alert alert-${result.error_count === 0 ? 'success' : 'warning'}">
                    <i class="bi bi-${result.error_count === 0 ? successIcon : 'exclamation-triangle'} me-2"></i>
                    <strong>${modeText}Finish</strong>
                    <br>total ${result.total_files} files，success ${result.success_count} indivual，fail ${result.error_count} indivual
                    <br><small class="text-muted">${processingNote}</small>
                </div>
            `;

            if (result.results && result.results.length > 0) {
                html += `<div class="mt-3"><h6 class="mb-2">Detailed results：</h6><div class="row">`;
                
                result.results.forEach((item, index) => {
                    const statusClass = item.success ? 'success' : 'danger';
                    const statusIcon = item.success ? 'check-circle-fill' : 'x-circle-fill';
                    
                    // Check if file name and person name match（for highlighting）
                    const fileBaseName = item.file_name ? item.file_name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ') : '';
                    const isMatching = item.name && fileBaseName.toLowerCase().includes(item.name.toLowerCase().replace(' ', ''));
                    const matchIcon = isMatching ? '<i class="bi bi-link-45deg text-success ms-1" title="File name matches person name"></i>' : '';
                    
                    // Display special identifier for video registration
                    const fileIcon = isVideoRegistration ? '🎥' : '📁';
                    const frameText = isVideoRegistration ? `No. ${index + 1} frame` : item.file_name;
                    
                    html += `
                        <div class="col-12 mb-2">
                            <div class="card border-${statusClass}">
                                <div class="card-body p-2">
                                    <div class="d-flex align-items-center">
                                        <i class="bi bi-${statusIcon} text-${statusClass} me-2"></i>
                                        <div class="flex-grow-1">
                                            <div class="fw-bold">
                                                ${fileIcon} ${frameText} ${matchIcon}
                                            </div>
                                            <div class="small text-muted">
                                                ${item.name ? `👤 Name: <strong>${item.name}</strong>` : ''}
                                                ${item.success ? 
                                                    `${item.person_id ? ` | 🆔 ID: ${item.person_id}` : ''}${item.quality_score ? ` | 📊 quality: ${(item.quality_score * 100).toFixed(1)}%` : ''}` :
                                                    ` | ❌ mistake: ${item.error}`
                                                }
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                html += `</div></div>`;
            }

            html += `
                <div class="small text-muted mt-3">
                    <div><strong>processing time:</strong> ${new Date().toLocaleString()}</div>
                    <div><strong>state:</strong> ${result.message}</div>
                    ${isVideoRegistration ? '<div><strong>Data source:</strong> 5Second video recording</div>' : ''}
                </div>
            `;

            container.innerHTML = html;
        } else {
            this.displayError(result.error || 'Registration failed');
        }
    }

    displayResults(result) {
        const container = document.getElementById('enrollmentResults');
        if (!container) return;

        if (result.success) {
            // fromAPIGet the correct number of faces in the results
            const facesDetected = result.faces_detected || 1;
            const faceQuality = result.face_quality ? (result.face_quality * 100).toFixed(1) : 'N/A';
            
            container.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle me-2"></i>
                    <strong>Registration successful！</strong>
                    <br>Successfully registered ${facesDetected} face${result.face_quality ? `，quality score: ${faceQuality}%` : ''}
                </div>
                <div class="small text-muted mt-2">
                    <div><strong>personnelID:</strong> ${result.person_id}</div>
                    ${result.face_encoding_id ? `<div><strong>human faceID:</strong> ${result.face_encoding_id}</div>` : ''}
                    <div><strong>Name:</strong> ${result.person_name || result.name}</div>
                    ${result.description ? `<div><strong>describe:</strong> ${result.description}</div>` : ''}
                    <div><strong>processing time:</strong> ${result.processing_time ? (result.processing_time * 1000).toFixed(0) + 'ms' : 'N/A'}</div>
                    <div><strong>Registration time:</strong> ${new Date().toLocaleString()}</div>
                </div>
                ${result.visualized_image ? `
                    <div class="mt-3">
                        <h6 class="small text-muted mb-2">Face detection results:</h6>
                        <img src="data:image/jpeg;base64,${result.visualized_image}" 
                             class="img-fluid rounded border" 
                             style="max-height: 200px;" 
                             alt="Face detection visualization">
                    </div>
                ` : ''}
            `;
        } else {
            this.displayError(result.error || 'Registration failed');
        }
    }

    displayError(message) {
        const container = document.getElementById('enrollmentResults');
        if (container) {
            // Check error type
            const isDuplicateError = (
                message.includes('Similar faces') || 
                message.includes('Already exists') || 
                message.includes('Repeat frame') || 
                message.includes('Duplicate faces') ||
                message.includes('Already registered') ||
                message.includes('Cannot register as a different person')
            );
            const isVideoError = message.includes('video') || message.includes('frame data') || message.includes('different postures');
            const isCrossPersonError = message.includes('Cannot register as a different person') || message.includes('has been registered as');
            
            let errorTitle = 'Registration failed';
            let errorIcon = 'exclamation-triangle';
            let helpText = '';
            
            if (isDuplicateError) {
                if (isCrossPersonError) {
                    errorTitle = 'Duplicate face detection - The same face cannot be registered multiple times';
                    errorIcon = 'person-x';
                    helpText = '🚨 The system has detected that your face has been registered。The same person cannot register multiple times under different names。';
                } else if (isVideoError) {
                    errorTitle = 'Video registration detects duplicate frames';
                    errorIcon = 'camera-video-off';
                    helpText = '💡 Please try different angles、Re-record video with expression or gesture';
                } else {
                    errorTitle = 'Duplicate face detection';
                    errorIcon = 'person-exclamation';
                    helpText = '💡 Please try again with a different face picture or a different person name';
                }
            }
            
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-${errorIcon} me-2"></i>
                    <strong>${errorTitle}</strong>
                    <br><small>${message}</small>
                    ${helpText ? `<br><small class="text-muted mt-1">${helpText}</small>` : ''}
                </div>
            `;
        }
    }

    clearEnrollment() {
        this.enrollmentFiles = [];
        
        const fileInput = document.getElementById('enrollmentFile');
        const preview = document.getElementById('enrollmentPreview');
        const nameInput = document.getElementById('personName');
        const descInput = document.getElementById('personDescription');
        const btn = document.getElementById('enrollBtn');
        const results = document.getElementById('enrollmentResults');

        if (fileInput) fileInput.value = '';
        if (preview) preview.classList.add('d-none');
        if (nameInput) nameInput.value = '';
        if (descInput) descInput.value = '';
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Registered Person';
        }
        
        if (results) {
            results.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-person-plus"></i>
                    <h6>Waiting for registration information</h6>
                    <p class="mb-0">Please upload a photo and fill in the information</p>
                </div>
            `;
        }
    }
}

// Export to global scope
window.PersonEnrollment = PersonEnrollment;

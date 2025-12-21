// Personnel management module
class PersonManagement {
    constructor() {
        this.allPersons = [];
        this.filteredPersons = [];
        this.currentPerson = null;
        this.selectedPersons = new Set();
        this.viewMode = 'card'; // 'card' or 'list'
        this.sortBy = 'created_at'; // 'created_at', 'name', 'face_count'
        this.sortOrder = 'desc'; // 'asc' or 'desc'
        this.bulkSelectionMode = false; // Batch selection mode
        this.recentOperations = JSON.parse(localStorage.getItem('recentOperations') || '[]');
        
        // Pagination related properties
        this.currentPage = 1;
        this.pageSize = parseInt(localStorage.getItem('personManagement_pageSize')) || 20; // fromlocalStorageLoad user preferences
        this.totalPages = 1;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadPersons();
    }

    bindEvents() {
        // search
        const searchInput = document.getElementById('searchPerson');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterPersons(e.target.value);
            });
        }

        // View mode switch
        const cardViewBtn = document.getElementById('cardView');
        const listViewBtn = document.getElementById('listView');
        
        if (cardViewBtn) {
            cardViewBtn.addEventListener('change', () => {
                this.viewMode = 'card';
                this.displayPersons();
            });
        }
        
        if (listViewBtn) {
            listViewBtn.addEventListener('change', () => {
                this.viewMode = 'list';
                this.displayPersons();
            });
        }

        // refresh button
        const refreshBtn = document.querySelector('[onclick="refreshPersonList()"]');
        if (refreshBtn) {
            refreshBtn.onclick = () => this.loadPersons();
        }

        // sort button
        const sortBtn = document.querySelector('[onclick="showSortOptions()"]');
        if (sortBtn) {
            sortBtn.onclick = () => this.showSortOptions();
        }
    }

    async loadPersons() {
        try {
            // show loading status
            this.showLoading(true);
            
            // try from realityAPILoad data
            let data;
            try {
                const response = await fetch('/api/persons');
                if (response.ok) {
                    data = await response.json();
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (apiError) {
                console.error('Unable to get person data:', apiError);
                // Show errors instead of using mock data
                data = [];
                this.showError('Unable to get person data，Please check if the backend service is running normally');
            }
            
            this.allPersons = data.persons || data || [];
            this.filteredPersons = [...this.allPersons];
            this.sortPersons(); // Add sort
            this.updatePagination(); // Add paginated updates
            this.displayPersons();
            this.updateStatistics();
            this.updateRecentOperations(); // Update recent operations display
            
            // update count
            const countElement = document.querySelector('.person-count');
            if (countElement) {
                countElement.textContent = `${this.allPersons.length} people`;
                countElement.className = 'badge bg-primary';
            }

        } catch (error) {
            console.error('Load persons error:', error);
            this.showMessage(`Failed to load personnel list: ${error.message}`, 'error');
            this.displayError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    async updateStatistics() {
        try {
            // Get real-time statistics
            const response = await fetch('/api/statistics');
            if (response.ok) {
                const stats = await response.json();
                
                // Update quick statistics
                const totalPersonsCount = document.getElementById('totalPersonsCount');
                const totalFacesCount = document.getElementById('totalFacesCount');
                
                if (totalPersonsCount) {
                    totalPersonsCount.textContent = stats.total_persons || this.allPersons.length;
                }
                
                if (totalFacesCount) {
                    totalFacesCount.textContent = stats.total_encodings || 0;
                }
            } else {
                // Downgrade to local computing - Only show real data
                const totalPersonsCount = document.getElementById('totalPersonsCount');
                const totalFacesCount = document.getElementById('totalFacesCount');
                
                if (totalPersonsCount) {
                    totalPersonsCount.textContent = this.allPersons.length;
                }
                
                if (totalFacesCount) {
                    // if notAPIdata，displayed as0（Because there is no real face data）
                    totalFacesCount.textContent = 0;
                }
            }
        } catch (error) {
            console.error('Failed to update statistics:', error);
            // Downgrade using local data
            const totalPersonsCount = document.getElementById('totalPersonsCount');
            if (totalPersonsCount) {
                totalPersonsCount.textContent = this.allPersons.length;
            }
        }
    }

    filterPersons(query) {
        const term = query.toLowerCase().trim();
        
        if (!term) {
            this.filteredPersons = [...this.allPersons];
        } else {
            this.filteredPersons = this.allPersons.filter(person => 
                person.name.toLowerCase().includes(term) ||
                (person.description && person.description.toLowerCase().includes(term))
            );
        }
        
        this.sortPersons(); // Reorder
        this.updatePagination(); // Update pagination
        this.displayPersons();
    }

    sortPersons() {
        this.filteredPersons.sort((a, b) => {
            let valueA, valueB;
            
            switch (this.sortBy) {
                case 'name':
                    valueA = a.name.toLowerCase();
                    valueB = b.name.toLowerCase();
                    break;
                case 'face_count':
                    valueA = a.face_count || a.encodings_count || 0;
                    valueB = b.face_count || b.encodings_count || 0;
                    break;
                case 'created_at':
                default:
                    valueA = new Date(a.created_at || 0);
                    valueB = new Date(b.created_at || 0);
                    break;
            }
            
            if (this.sortOrder === 'asc') {
                return valueA > valueB ? 1 : valueA < valueB ? -1 : 0;
            } else {
                return valueA < valueB ? 1 : valueA > valueB ? -1 : 0;
            }
        });
    }

    // Paging related methods
    updatePagination() {
        this.totalPages = Math.ceil(this.filteredPersons.length / this.pageSize);
        
        // If the current page is out of range，Return to first page
        if (this.currentPage > this.totalPages) {
            this.currentPage = 1;
        }
        
        // Make sure there are at least1Page
        if (this.totalPages === 0) {
            this.totalPages = 1;
        }
        
        this.renderPaginationControls();
    }

    getCurrentPagePersons() {
        const startIndex = (this.currentPage - 1) * this.pageSize;
        const endIndex = startIndex + this.pageSize;
        return this.filteredPersons.slice(startIndex, endIndex);
    }

    goToPage(page) {
        if (page < 1 || page > this.totalPages) return;
        
        this.currentPage = page;
        this.displayPersons();
        this.renderPaginationControls();
        
        // Scroll to top of people list
        const container = document.getElementById('personsList');
        if (container) {
            container.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.goToPage(this.currentPage - 1);
        }
    }

    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.goToPage(this.currentPage + 1);
        }
    }

    renderPaginationControls() {
        // Find or create a paging container
        let paginationContainer = document.getElementById('personsPagination');
        if (!paginationContainer) {
            // on people list card card-body Add paging controls later
            const personsCard = document.getElementById('personsList')?.closest('.card');
            if (personsCard) {
                paginationContainer = document.createElement('div');
                paginationContainer.id = 'personsPagination';
                paginationContainer.className = 'card-footer bg-transparent border-top';
                personsCard.appendChild(paginationContainer);
            }
        }
        
        if (!paginationContainer) return;

        // If there is only one page or no data，Hide paging controls
        if (this.totalPages <= 1) {
            paginationContainer.style.display = 'none';
            return;
        }
        
        paginationContainer.style.display = 'block';

        const startItem = (this.currentPage - 1) * this.pageSize + 1;
        const endItem = Math.min(this.currentPage * this.pageSize, this.filteredPersons.length);
        
        paginationContainer.innerHTML = `
            <div class="row align-items-center">
                <div class="col-md-4">
                    <div class="d-flex align-items-center">
                        <span class="small text-muted me-2">Show per page:</span>
                        <select class="form-select form-select-sm" style="width: 80px;" onchange="window.personManagement.changePageSize(this.value)">
                            <option value="10" ${this.pageSize === 10 ? 'selected' : ''}>10</option>
                            <option value="20" ${this.pageSize === 20 ? 'selected' : ''}>20</option>
                            <option value="50" ${this.pageSize === 50 ? 'selected' : ''}>50</option>
                            <option value="100" ${this.pageSize === 100 ? 'selected' : ''}>100</option>
                        </select>
                        <span class="small text-muted ms-2">item</span>
                    </div>
                </div>
                <div class="col-md-4 text-center">
                    <nav aria-label="Person list pagination">
                        <ul class="pagination pagination-sm mb-0 justify-content-center">
                            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                                <button class="page-link" onclick="window.personManagement.previousPage()" 
                                        ${this.currentPage === 1 ? 'disabled' : ''}>
                                    <i class="bi bi-chevron-left"></i>
                                </button>
                            </li>
                            ${this.generatePageNumbers()}
                            <li class="page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}">
                                <button class="page-link" onclick="window.personManagement.nextPage()"
                                        ${this.currentPage === this.totalPages ? 'disabled' : ''}>
                                    <i class="bi bi-chevron-right"></i>
                                </button>
                            </li>
                        </ul>
                    </nav>
                </div>
                <div class="col-md-4 text-end">
                    <div class="small text-muted">
                        Showing the ${startItem}-${endItem} item，common ${this.filteredPersons.length} item
                        <br>No. ${this.currentPage} / ${this.totalPages} Page
                    </div>
                </div>
            </div>
        `;
    }

    changePageSize(newSize) {
        this.pageSize = parseInt(newSize);
        this.currentPage = 1; // Return to first page
        this.updatePagination();
        this.displayPersons();
        
        // Save user preferences
        localStorage.setItem('personManagement_pageSize', this.pageSize);
        
        this.showMessage(`Show per page ${this.pageSize} item`, 'info');
    }

    generatePageNumbers() {
        let html = '';
        const maxVisiblePages = 5;
        const halfVisible = Math.floor(maxVisiblePages / 2);
        
        let startPage = Math.max(1, this.currentPage - halfVisible);
        let endPage = Math.min(this.totalPages, startPage + maxVisiblePages - 1);
        
        // Adjust the start page，Make sure enough page numbers are shown
        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }
        
        // If the start page is not1，Show first page and ellipses
        if (startPage > 1) {
            html += `
                <li class="page-item">
                    <button class="page-link" onclick="window.personManagement.goToPage(1)">1</button>
                </li>
            `;
            if (startPage > 2) {
                html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
        }
        
        // Show page number
        for (let i = startPage; i <= endPage; i++) {
            html += `
                <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                    <button class="page-link" onclick="window.personManagement.goToPage(${i})">${i}</button>
                </li>
            `;
        }
        
        // If the end page is not the last page，Show ellipsis and last page
        if (endPage < this.totalPages) {
            if (endPage < this.totalPages - 1) {
                html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
            html += `
                <li class="page-item">
                    <button class="page-link" onclick="window.personManagement.goToPage(${this.totalPages})">${this.totalPages}</button>
                </li>
            `;
        }
        
        return html;
    }

    showSortOptions() {
        // Remove existing sort dialog
        const existingModal = document.getElementById('sortOptionsModal');
        if (existingModal) {
            existingModal.remove();
        }

        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'sortOptionsModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-0 shadow">
                    <div class="modal-header bg-light border-0">
                        <h6 class="modal-title">
                            <i class="bi bi-sort-down me-2"></i>Sorting options
                        </h6>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-4">
                        <div class="mb-3">
                            <label class="form-label">sort by</label>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="sortBy" value="created_at" id="sortByDate" ${this.sortBy === 'created_at' ? 'checked' : ''}>
                                <label class="form-check-label" for="sortByDate">
                                    <i class="bi bi-calendar3 me-2"></i>Registration time
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="sortBy" value="name" id="sortByName" ${this.sortBy === 'name' ? 'checked' : ''}>
                                <label class="form-check-label" for="sortByName">
                                    <i class="bi bi-person me-2"></i>Name
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="sortBy" value="face_count" id="sortByFaceCount" ${this.sortBy === 'face_count' ? 'checked' : ''}>
                                <label class="form-check-label" for="sortByFaceCount">
                                    <i class="bi bi-images me-2"></i>Number of photos
                                </label>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">sort order</label>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="sortOrder" value="desc" id="sortOrderDesc" ${this.sortOrder === 'desc' ? 'checked' : ''}>
                                <label class="form-check-label" for="sortOrderDesc">
                                    <i class="bi bi-sort-down me-2"></i>descending order（high to low）
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="sortOrder" value="asc" id="sortOrderAsc" ${this.sortOrder === 'asc' ? 'checked' : ''}>
                                <label class="form-check-label" for="sortOrderAsc">
                                    <i class="bi bi-sort-up me-2"></i>Ascending order（low to high）
                                </label>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer border-0">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="window.personManagement.applySorting()">
                            <i class="bi bi-check-lg me-1"></i>Apply sorting
                        </button>
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
        }
    }

    applySorting() {
        const sortByElements = document.querySelectorAll('input[name="sortBy"]:checked');
        const sortOrderElements = document.querySelectorAll('input[name="sortOrder"]:checked');
        
        if (sortByElements.length > 0) {
            this.sortBy = sortByElements[0].value;
        }
        
        if (sortOrderElements.length > 0) {
            this.sortOrder = sortOrderElements[0].value;
        }
        
        this.sortPersons(); // Reorder
        this.updatePagination(); // Update pagination
        this.displayPersons();
        this.showMessage('Sorting applied', 'success');
        
        // Close modal box
        const modal = bootstrap.Modal.getInstance(document.getElementById('sortOptionsModal'));
        if (modal) {
            modal.hide();
        }
    }

    displayPersons() {
        const container = document.getElementById('personsList');
        if (!container) return;

        // Get the personnel data of the current page
        const currentPagePersons = this.getCurrentPagePersons();

        if (this.filteredPersons.length === 0) {
            container.innerHTML = `
                <div class="empty-state text-center p-5">
                    <i class="bi bi-people text-muted" style="font-size: 3rem;"></i>
                    <h6 class="mt-3">No personnel data yet</h6>
                    <p class="text-muted mb-0">Please register personnel information first</p>
                </div>
            `;
            // Hide paging controls
            this.renderPaginationControls();
            return;
        }

        if (this.viewMode === 'card') {
            this.displayCardView(container, currentPagePersons);
        } else {
            this.displayListView(container, currentPagePersons);
        }
        
        // Update paging controls
        this.renderPaginationControls();
    }

    displayCardView(container, persons = this.filteredPersons) {
        const cardsHtml = persons.map(person => `
            <div class="col-lg-4 col-md-6 mb-3">
                <div class="card h-100 person-card shadow-sm" data-person-id="${person.id}">
                    <div class="card-body p-3">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            ${this.bulkSelectionMode ? `
                                <div class="form-check">
                                    <input class="form-check-input person-checkbox" type="checkbox" id="person_${person.id}" 
                                           data-person-id="${person.id}"
                                           ${this.selectedPersons.has(person.id) ? 'checked' : ''}
                                           onchange="window.personManagement.togglePersonSelection(${person.id})">
                                    <label class="form-check-label" for="person_${person.id}"></label>
                                </div>
                            ` : '<div></div>'}
                            <div class="dropdown">
                                <button class="btn btn-link btn-sm text-muted p-1" data-bs-toggle="dropdown">
                                    <i class="bi bi-three-dots-vertical"></i>
                                </button>
                                <ul class="dropdown-menu dropdown-menu-end">
                                    <li><a class="dropdown-item" href="#" onclick="window.personManagement.showPersonDetails(${person.id})">
                                        <i class="bi bi-eye me-2"></i>check the details
                                    </a></li>
                                    <li><a class="dropdown-item" href="#" onclick="window.personManagement.editPersonModal(${person.id})">
                                        <i class="bi bi-pencil me-2"></i>Edit information
                                    </a></li>
                                    <li><hr class="dropdown-divider"></li>
                                    <li><a class="dropdown-item text-danger" href="#" onclick="window.personManagement.deletePerson(${person.id})">
                                        <i class="bi bi-trash me-2"></i>delete
                                    </a></li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="text-center mb-3">
                            <div class="position-relative d-inline-block">
                                ${this.getPersonAvatar(person)}
                                <span class="position-absolute bottom-0 end-0 bg-success border border-2 border-white rounded-circle" 
                                      style="width: 16px; height: 16px;" title="Registered"></span>
                            </div>
                        </div>
                        
                        <h6 class="card-title text-center mb-1 fw-semibold">${person.name}</h6>
                        <p class="card-text text-center text-muted small mb-3">
                            ${person.emp_id ? `Emp ID: ${person.emp_id}` : `ID: ${person.id}`}
                            ${person.emp_rank ? ` | ${person.emp_rank}` : ''}
                            ${person.region ? ` | ${person.region.toUpperCase()}` : ''}
                        </p>
                        
                        ${person.description ? `<p class="card-text small mb-3 text-center text-secondary">"${person.description}"</p>` : ''}
                        
                        <div class="border-top pt-3 mt-3">
                            <div class="row text-center small">
                                <div class="col-6">
                                    <div class="d-flex align-items-center justify-content-center">
                                        <i class="bi bi-camera-fill text-primary me-1"></i>
                                        <span class="fw-medium">${person.encodings_count || 0}</span>
                                    </div>
                                    <small class="text-muted">photo</small>
                                </div>
                                <div class="col-6">
                                    <div class="d-flex align-items-center justify-content-center">
                                        <i class="bi bi-calendar3 text-success me-1"></i>
                                        <span class="fw-medium">${this.formatDate(person.created_at)}</span>
                                    </div>
                                    <small class="text-muted">register</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent border-top-0 pt-0 pb-3">
                        <div class="btn-group w-100" role="group">
                            <button class="btn btn-outline-primary btn-sm" onclick="window.personManagement.showPersonDetails(${person.id})" title="check the details">
                                <i class="bi bi-eye"></i>
                            </button>
                            <button class="btn btn-outline-secondary btn-sm" onclick="window.personManagement.editPersonModal(${person.id})" title="edit">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-danger btn-sm" onclick="window.personManagement.deletePerson(${person.id})" title="delete">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = `<div class="row">${cardsHtml}</div>`;
    }

    getPersonAvatar(person) {
        // If there is a face picture，Show real avatar
        if (person.face_image_url) {
            // Add timestamp to prevent caching issues
            const imageUrl = person.face_image_url + (person.face_image_url.includes('?') ? '&' : '?') + 't=' + Date.now();
            return `
                <img src="${imageUrl}" 
                     class="rounded-circle object-fit-cover cursor-pointer" 
                     style="width: 72px; height: 72px; border: 3px solid var(--bs-primary);"
                     alt="${person.name}"
                     onclick="window.personManagement.showPersonDetails(${person.id})"
                     title="Click to view details"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                <div class="bg-primary bg-gradient rounded-circle d-none align-items-center justify-content-center cursor-pointer" 
                     style="width: 72px; height: 72px;"
                     onclick="window.personManagement.showPersonDetails(${person.id})"
                     title="Click to view details">
                    <i class="bi bi-person-fill text-white fs-3"></i>
                </div>
            `;
        } else {
            // Use default avatar，Generate color based on name
            const colors = [
                'bg-primary', 'bg-success', 'bg-info', 'bg-warning', 
                'bg-danger', 'bg-secondary', 'bg-dark'
            ];
            const colorIndex = person.name.charCodeAt(0) % colors.length;
            const bgColor = colors[colorIndex];
            
            return `
                <div class="${bgColor} bg-gradient rounded-circle d-flex align-items-center justify-content-center cursor-pointer" 
                     style="width: 72px; height: 72px;"
                     onclick="window.personManagement.showPersonDetails(${person.id})"
                     title="Click to view details">
                    <span class="text-white fw-bold fs-4">${person.name.charAt(0)}</span>
                </div>
            `;
        }
    }

    formatDate(dateString) {
        if (!dateString) return 'unknown';
        const date = new Date(dateString);
        const now = new Date();
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return 'today';
        if (diffDays === 1) return 'yesterday';
        if (diffDays < 7) return `${diffDays}days ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)}weeks ago`;
        return date.toLocaleDateString('zh-CN');
    }

    displayListView(container, persons = this.filteredPersons) {
        const rowsHtml = persons.map(person => `
            <tr class="person-row" data-person-id="${person.id}">
                <td>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="person_list_${person.id}" 
                               data-person-id="${person.id}"
                               onchange="window.personManagement.togglePersonSelection(${person.id})">
                    </div>
                </td>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="position-relative me-3">
                            ${this.getPersonAvatarSmall(person)}
                        </div>
                        <div>
                            <h6 class="mb-0 fw-semibold">${person.name}</h6>
                            <small class="text-muted">
                                ${person.emp_id ? `Emp ID: ${person.emp_id}` : `ID: ${person.id}`}
                                ${person.emp_rank ? ` | ${person.emp_rank}` : ''}
                                ${person.region ? ` | ${person.region.toUpperCase()}` : ''}
                            </small>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="text-secondary">${person.description || '-'}</span>
                </td>
                <td>
                    <span class="badge bg-light text-dark border">
                        <i class="bi bi-camera-fill text-primary me-1"></i>${person.encodings_count || 0}
                    </span>
                </td>
                <td>
                    <small class="text-muted">
                        ${this.formatDate(person.created_at)}
                    </small>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="window.personManagement.showPersonDetails(${person.id})" title="check the details">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-outline-secondary" onclick="window.personManagement.editPersonModal(${person.id})" title="edit">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="window.personManagement.deletePerson(${person.id})" title="delete">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        container.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th width="50">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="selectAll" 
                                           onchange="window.personManagement.toggleSelectAll()">
                                </div>
                            </th>
                            <th>Personnel information</th>
                            <th>describe</th>
                            <th>Number of photos</th>
                            <th>Registration time</th>
                            <th width="120">operate</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rowsHtml}
                    </tbody>
                </table>
            </div>
        `;
    }

    getPersonAvatarSmall(person) {
        // List view avatar
        if (person.face_image_url) {
            // Add timestamp to prevent caching issues
            const imageUrl = person.face_image_url + (person.face_image_url.includes('?') ? '&' : '?') + 't=' + Date.now();
            return `
                <img src="${imageUrl}" 
                     class="rounded-circle object-fit-cover cursor-pointer" 
                     style="width: 48px; height: 48px; border: 2px solid var(--bs-primary);"
                     alt="${person.name}"
                     onclick="window.personManagement.showPersonDetails(${person.id})"
                     title="Click to view details"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                <div class="bg-primary bg-gradient rounded-circle d-none align-items-center justify-content-center cursor-pointer" 
                     style="width: 48px; height: 48px;"
                     onclick="window.personManagement.showPersonDetails(${person.id})"
                     title="Click to view details">
                    <span class="text-white fw-bold">${person.name.charAt(0)}</span>
                </div>
            `;
        } else {
            const colors = [
                'bg-primary', 'bg-success', 'bg-info', 'bg-warning', 
                'bg-danger', 'bg-secondary', 'bg-dark'
            ];
            const colorIndex = person.name.charCodeAt(0) % colors.length;
            const bgColor = colors[colorIndex];
            
            return `
                <div class="${bgColor} bg-gradient rounded-circle d-flex align-items-center justify-content-center cursor-pointer" 
                     style="width: 48px; height: 48px;"
                     onclick="window.personManagement.showPersonDetails(${person.id})"
                     title="Click to view details">
                    <span class="text-white fw-bold">${person.name.charAt(0)}</span>
                </div>
            `;
        }
    }

    togglePersonSelection(personId) {
        if (this.selectedPersons.has(personId)) {
            this.selectedPersons.delete(personId);
        } else {
            this.selectedPersons.add(personId);
        }
        this.updateBulkOperationButtons();
    }

    toggleSelectAll() {
        const selectAllCheckbox = document.getElementById('selectAll');
        if (selectAllCheckbox && selectAllCheckbox.checked) {
            this.filteredPersons.forEach(person => this.selectedPersons.add(person.id));
        } else {
            this.selectedPersons.clear();
        }
        
        // Update all checkbox states
        this.filteredPersons.forEach(person => {
            const checkbox1 = document.getElementById(`person_${person.id}`);
            const checkbox2 = document.getElementById(`person_list_${person.id}`);
            if (checkbox1) checkbox1.checked = this.selectedPersons.has(person.id);
            if (checkbox2) checkbox2.checked = this.selectedPersons.has(person.id);
        });
        
        this.updateBulkOperationButtons();
    }

    updateBulkOperationButtons() {
        const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
        const bulkExportBtn = document.getElementById('bulkExportBtn');
        const hasSelection = this.selectedPersons.size > 0;
        
        if (bulkDeleteBtn) {
            bulkDeleteBtn.disabled = !hasSelection;
            bulkDeleteBtn.innerHTML = `<i class="bi bi-trash me-1"></i>Batch delete (${this.selectedPersons.size})`;
        }
        
        if (bulkExportBtn) {
            bulkExportBtn.disabled = !hasSelection;
            bulkExportBtn.innerHTML = `<i class="bi bi-download me-1"></i>Export data (${this.selectedPersons.size})`;
        }
    }

    async showPersonDetails(personId) {
        try {
            const person = this.allPersons.find(p => p.id === personId);
            if (!person) {
                this.showMessage('Personnel information does not exist', 'error');
                return;
            }

            this.currentPerson = person;
            
            // Create an elegant details modal
            this.createPersonDetailModal(person);

        } catch (error) {
            console.error('Show person details error:', error);
            this.showMessage(`Failed to obtain person details: ${error.message}`, 'error');
        }
    }

    async createPersonDetailModal(person) {
        // Remove existing modal box
        const existingModal = document.getElementById('personDetailModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Mr Adult Face Gallery
        const faceGallery = await this.generateFaceGallery(person);

        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'personDetailModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-gradient-primary text-white border-0">
                        <div class="d-flex align-items-center">
                            <div class="me-3">
                                ${this.getPersonAvatarSmall(person)}
                            </div>
                            <div>
                                <h5 class="modal-title mb-0">${person.name}</h5>
                                <small class="opacity-75">Person details</small>
                            </div>
                        </div>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-4">
                        <div class="row">
                            <div class="col-md-4 text-center mb-4">
                                <div class="position-relative d-inline-block">
                                    ${this.getPersonAvatar(person)}
                                    <span class="position-absolute bottom-0 end-0 bg-success border border-2 border-white rounded-circle" 
                                          style="width: 20px; height: 20px;" title="Registered"></span>
                                </div>
                                <div class="mt-3">
                                    <button class="btn btn-outline-primary btn-sm me-2" onclick="window.personManagement.editPersonModal(${person.id})">
                                        <i class="bi bi-pencil me-1"></i>edit
                                    </button>
                                    <button class="btn btn-outline-danger btn-sm" onclick="window.personManagement.deletePersonConfirm(${person.id})">
                                        <i class="bi bi-trash me-1"></i>delete
                                    </button>
                                </div>
                            </div>
                            <div class="col-md-8">
                                <div class="row g-3">
                                    <div class="col-sm-6">
                                        <div class="info-card">
                                            <div class="info-label">Name</div>
                                            <div class="info-value">${person.name}</div>
                                        </div>
                                    </div>
                                    <div class="col-sm-6">
                                        <div class="info-card">
                                            <div class="info-label">Employee ID</div>
                                            <div class="info-value">${person.emp_id || 'N/A'}</div>
                                        </div>
                                    </div>
                                    <div class="col-sm-6">
                                        <div class="info-card">
                                            <div class="info-label">Rank</div>
                                            <div class="info-value">${person.emp_rank || 'N/A'}</div>
                                        </div>
                                    </div>
                                    <div class="col-sm-6">
                                        <div class="info-card">
                                            <div class="info-label">Region</div>
                                            <div class="info-value">${person.region ? person.region.toUpperCase() : 'N/A'}</div>
                                        </div>
                                    </div>
                                    <div class="col-12">
                                        <div class="info-card">
                                            <div class="info-label">describe</div>
                                            <div class="info-value">${person.description || 'No description yet'}</div>
                                        </div>
                                    </div>
                                    <div class="col-sm-6">
                                        <div class="info-card">
                                            <div class="info-label">Number of photos</div>
                                            <div class="info-value">
                                                <span class="badge bg-primary">${person.face_count || person.encodings_count || 0} open</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-sm-6">
                                        <div class="info-card">
                                            <div class="info-label">Registration time</div>
                                            <div class="info-value">${this.formatDate(person.created_at)}</div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mt-4">
                                    <h6 class="text-muted mb-3">
                                        <i class="bi bi-images me-2"></i>face photo
                                    </h6>
                                    <div class="face-gallery">
                                        ${faceGallery}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer border-0 bg-light">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">closure</button>
                        <button type="button" class="btn btn-primary" onclick="window.personManagement.editPersonModal(${person.id})">
                            <i class="bi bi-pencil me-1"></i>Edit information
                        </button>
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
        }
    }

    async generateFaceGallery(person) {
        // Try to get real photos of faces
        let faceImages = [];
        
        try {
            // First try to start with specialized facesAPIGet
            const response = await fetch(`/api/person/${person.emp_id}/faces`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.face_encodings && data.face_encodings.length > 0) {
                    // Willface_encodingsConvert to the format required by the front end
                    faceImages = data.face_encodings.map((encoding, index) => ({
                        id: encoding.id || `face_${person.id}_${index}`,
                        image_url: (encoding.has_image_data && encoding.id) ? `/api/face/${encoding.id}/image` : null,
                        created_at: encoding.created_at,
                        quality_score: encoding.quality_score,
                        face_index: index,
                        has_image: encoding.has_image_data || false
                    }));
                }
            }
        } catch (error) {
            console.warn('cannot be specializedAPIGet face photos:', error);
        }

        // If there are still no photos，Returns empty state but contains add button
        if (faceImages.length === 0) {
            return `
                <div class="text-center p-4">
                    <div class="text-muted mb-3">
                        <i class="bi bi-images" style="font-size: 3rem; opacity: 0.5;"></i>
                        <p class="mt-2 mb-0">No face photos yet</p>
                        <small class="text-muted">Add face photos to improve recognition accuracy</small>
                    </div>
                    <button class="btn btn-primary btn-sm" onclick="window.personManagement.addMoreFaces(${person.id})">
                        <i class="bi bi-plus-circle me-1"></i>Add a face photo
                    </button>
                </div>
            `;
        }

        let gallery = '<div class="row g-2">';
        
        // Show most9photo
        const displayCount = Math.min(faceImages.length, 9);
        
        for (let i = 0; i < displayCount; i++) {
            const face = faceImages[i];
            
            gallery += `
                <div class="col-4">
                    <div class="face-thumbnail position-relative">
                        <div class="face-image-container" onclick="window.personManagement.viewFaceImage('${face.id}', '${face.image_url || ''}', '${person.name}', ${i + 1})" style="cursor: pointer;">
                            ${face.image_url && face.has_image ? 
                                `<img src="${face.image_url}?t=${Date.now()}" class="img-fluid rounded" alt="face photo ${i+1}" style="width: 100%; height: 80px; object-fit: cover;"
                                      onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                 <div class="bg-light rounded d-flex align-items-center justify-content-center face-placeholder" style="width: 100%; height: 80px; display: none;">
                                     <i class="bi bi-person-circle text-muted"></i>
                                 </div>` :
                                `<div class="bg-light rounded d-flex align-items-center justify-content-center face-placeholder" style="width: 100%; height: 80px;">
                                    <div class="text-center">
                                        <i class="bi bi-person-circle text-muted" style="font-size: 2rem;"></i>
                                        <div class="small text-muted mt-1">Feature data</div>
                                    </div>
                                </div>`
                            }
                        </div>
                        <div class="face-actions position-absolute top-0 end-0 p-1">
                            <div class="btn-group-vertical" role="group">
                                <button class="btn btn-sm btn-outline-danger btn-action" 
                                        onclick="event.stopPropagation(); window.personManagement.deleteFaceImage(${person.id}, '${face.id}', ${i})"
                                        title="Delete this photo">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                        <div class="face-info position-absolute bottom-0 start-0 end-0 p-1">
                            <small class="text-white bg-dark bg-opacity-75 rounded px-1">
                                ${face.quality_score ? `quality: ${(face.quality_score * 100).toFixed(0)}%` : `photo ${i+1}`}
                            </small>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // If there are more photos，Show omitted hints
        if (faceImages.length > displayCount) {
            gallery += `
                <div class="col-4">
                    <div class="face-thumbnail bg-light rounded d-flex align-items-center justify-content-center face-placeholder">
                        <div class="text-center">
                            <i class="bi bi-three-dots text-muted"></i>
                            <div class="small text-muted">besides${faceImages.length - displayCount}open</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        gallery += '</div>';
        
        // Add descriptions and action buttons
        gallery += `
            <div class="mt-3">
                <div class="text-center mb-2">
                    <small class="text-muted">
                        <i class="bi bi-info-circle me-1"></i>
                        common ${faceImages.length} face photo
                    </small>
                </div>
                <div class="text-center">
                    <button class="btn btn-outline-primary btn-sm" onclick="window.personManagement.addMoreFaces(${person.id})">
                        <i class="bi bi-plus-circle me-1"></i>Face storage
                    </button>
                </div>
            </div>
        `;
        
        return gallery;
    }

    // View large image of face photo
    viewFaceImage(faceId, imageUrl, personName, faceNumber) {
        if (!imageUrl) {
            this.showMessage('This facial feature has no associated image data', 'info');
            return;
        }

        // Create image viewing modal box
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'faceImageModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-image me-2"></i>${personName || 'personnel'} - photo ${faceNumber || ''}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center p-4">
                        <div class="position-relative d-inline-block">
                            <img src="${imageUrl}" class="img-fluid rounded shadow" alt="face photo" style="max-height: 500px; max-width: 100%;"
                                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                            <div class="alert alert-warning" style="display: none;">
                                <i class="bi bi-exclamation-triangle me-2"></i>
                                Image loading failed，The image data may be corrupted or lost
                            </div>
                        </div>
                        <div class="mt-3 text-muted small">
                            <p class="mb-1">Click outside the photo or pressESCkey off</p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="bi bi-x me-1"></i>closure
                        </button>
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

            // Click outside the image to close the modal box
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    bootstrapModal.hide();
                }
            });
        }
    }

    // Delete a single face photo
    async deleteFaceImage(personId, faceId, faceIndex) {
        const person = this.allPersons.find(p => p.id === personId);
        if (!person) {
            this.showMessage('Personnel information does not exist', 'error');
            return;
        }

        const confirmed = await this.showDeleteFaceConfirmDialog(person, faceIndex);
        if (!confirmed) return;

        try {
            // call trueAPIDelete a single photo using emp_id
            const response = await fetch(`/api/person/${person.emp_id}/faces/${faceId}`, {
                method: 'DELETE'
            });
            
            let success = false;
            if (response.ok) {
                const data = await response.json();
                success = data.success;
                if (!success) {
                    throw new Error(data.message || 'Delete failed');
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }

            if (success) {
                // Update the number of faces of people
                const currentCount = person.face_count || person.encodings_count || 0;
                if (currentCount > 0) {
                    person.face_count = currentCount - 1;
                    person.encodings_count = currentCount - 1;
                }

                this.showMessage('Photo deleted successfully', 'success');
                this.addRecentOperation('Delete photo', `deleted ${person.name} A photo of a face`);
                
                // Reload people data to get the latest information
                await this.loadPersons();
                
                // Refresh the photo display on the details page
                const detailModal = document.getElementById('personDetailModal');
                if (detailModal) {
                    await this.refreshPersonDetails(personId);
                }
                
                // Refresh main list display
                this.displayPersons();
                this.updateStatistics();
            }

        } catch (error) {
            console.error('Delete face error:', error);
            this.showMessage(`Delete failed: ${error.message}`, 'error');
        }
    }

    // Show confirmation dialog for deleting a single photo
    showDeleteFaceConfirmDialog(person, faceIndex) {
        return new Promise((resolve) => {
            // Create confirmation dialog
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'deleteFaceConfirmModal';
            modal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg">
                        <div class="modal-header bg-danger text-white border-0">
                            <h5 class="modal-title">
                                <i class="bi bi-exclamation-triangle me-2"></i>Confirm photo deletion
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body p-4">
                            <div class="text-center mb-3">
                                <div class="text-warning mb-2">
                                    <i class="bi bi-image" style="font-size: 2rem;"></i>
                                </div>
                                <h6>Delete face photo</h6>
                                <p class="text-muted">Confirm to delete <strong>${person.name}</strong> This photo of？</p>
                            </div>
                            
                            <div class="alert alert-warning">
                                <i class="bi bi-info-circle me-2"></i>
                                <small>
                                    Once deleted, the photo cannot be recovered，May affect recognition accuracy。
                                    It is recommended to keep multiple photos from different angles to improve the recognition effect。
                                </small>
                            </div>
                        </div>
                        <div class="modal-footer border-0">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="bi bi-x me-1"></i>Cancel
                            </button>
                            <button type="button" class="btn btn-danger" id="confirmDeleteFace">
                                <i class="bi bi-trash me-1"></i>Confirm deletion
                            </button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            if (window.bootstrap) {
                const bootstrapModal = new bootstrap.Modal(modal);
                bootstrapModal.show();

                // Confirm button event
                const confirmBtn = modal.querySelector('#confirmDeleteFace');
                confirmBtn.addEventListener('click', () => {
                    bootstrapModal.hide();
                    resolve(true);
                });

                // Modal box close event
                modal.addEventListener('hidden.bs.modal', () => {
                    document.body.removeChild(modal);
                    resolve(false);
                });
            } else {
                resolve(confirm(`Confirm to delete "${person.name}" This photo of？`));
            }
        });
    }

    // Add more photos
    addMoreFaces(personId) {
        const person = this.allPersons.find(p => p.id === personId);
        if (!person) {
            this.showMessage('Personnel information does not exist', 'error');
            return;
        }

        // Create upload photo modal box
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'addFacesModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-person-plus-fill me-2"></i>for ${person.name} Add a face photo
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle me-2"></i>
                            <strong>Face storage instructions：</strong>Uploaded photos will be analyzed for face recognition and stored in the database，Used for subsequent face recognition comparison。
                        </div>
                        <div class="upload-area border-2 border-dashed border-primary rounded p-4 text-center mb-3" style="cursor: pointer;" onclick="document.getElementById('addFacesInput').click()">
                            <i class="bi bi-cloud-upload text-primary mb-2" style="font-size: 2rem;"></i>
                            <h6>Click to select or drag photos here</h6>
                            <p class="text-muted small mb-2">support JPG、PNG Format，No more than one sheet 5MB</p>
                            <input type="file" class="d-none" id="addFacesInput" multiple accept="image/*">
                        </div>
                        <div id="addFacesPreview" class="d-none">
                            <h6 class="small text-muted mb-2">Preview:</h6>
                            <div id="addFacesImages" class="row g-2"></div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="uploadFacesBtn" disabled>
                            <i class="bi bi-database-add me-1"></i>Start warehousing
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        
        if (window.bootstrap) {
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
            
            // File selection processing
            const fileInput = modal.querySelector('#addFacesInput');
            const uploadBtn = modal.querySelector('#uploadFacesBtn');
            const uploadArea = modal.querySelector('.upload-area');
            
            fileInput.addEventListener('change', (e) => {
                this.handleAddFacesFiles(e.target.files, modal);
                uploadBtn.disabled = e.target.files.length === 0;
            });

            // Drag and drop upload event
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('border-success');
                uploadArea.style.backgroundColor = 'rgba(var(--bs-success-rgb), 0.1)';
            });

            uploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('border-success');
                uploadArea.style.backgroundColor = '';
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('border-success');
                uploadArea.style.backgroundColor = '';
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    // Simulate file input selection
                    const dt = new DataTransfer();
                    for (let i = 0; i < files.length; i++) {
                        dt.items.add(files[i]);
                    }
                    fileInput.files = dt.files;
                    
                    // triggerchangeevent
                    this.handleAddFacesFiles(files, modal);
                    uploadBtn.disabled = files.length === 0;
                }
            });

            // Upload button event
            uploadBtn.addEventListener('click', () => {
                this.uploadAdditionalFaces(personId, fileInput.files, modal);
            });
            
            modal.addEventListener('hidden.bs.modal', () => {
                document.body.removeChild(modal);
            });
        }
    }

    // Process files with added photos
    handleAddFacesFiles(files, modal) {
        const preview = modal.querySelector('#addFacesPreview');
        const container = modal.querySelector('#addFacesImages');
        
        container.innerHTML = '';
        
        if (files.length === 0) {
            preview.classList.add('d-none');
            return;
        }

        Array.from(files).forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const col = document.createElement('div');
                col.className = 'col-4';
                col.innerHTML = `
                    <div class="position-relative">
                        <img src="${e.target.result}" class="img-fluid rounded" style="height: 80px; object-fit: cover; width: 100%;">
                        <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 m-1" 
                                onclick="this.parentElement.parentElement.remove()" title="Remove">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                `;
                container.appendChild(col);
            };
            reader.readAsDataURL(file);
        });

        preview.classList.remove('d-none');
    }

    // Upload additional photos of faces
    async uploadAdditionalFaces(personId, files, modal) {
        if (files.length === 0) return;

        const uploadBtn = modal.querySelector('#uploadFacesBtn');
        const originalText = uploadBtn.innerHTML;
        uploadBtn.innerHTML = '<i class="bi bi-spinner bi-spin me-1"></i>In stock...';
        uploadBtn.disabled = true;

        try {
            // call realAPIto upload photos
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('faces', files[i]);
            }

            // Get person to find emp_id
            const person = this.allPersons.find(p => p.id === personId);
            if (!person) {
                throw new Error('Person not found');
            }
            
            const response = await fetch(`/api/person/${person.emp_id}/faces`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: HTTP ${response.status}`);
            }

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || 'Upload failed');
            }

            // person is already declared above
            this.showMessage(`Successfully put into storage ${result.count || files.length} face photo`, 'success');
            this.addRecentOperation('Face storage', `for ${person ? person.name : 'personnel'} In stock ${result.count || files.length} face photo`);

            // Reload people data to get the latest information
            await this.loadPersons();
            
            // Refresh details page
            const detailModal = document.getElementById('personDetailModal');
            if (detailModal && person) {
                this.refreshPersonDetails(personId);
            }

            // Close modal box
            const bootstrapModal = bootstrap.Modal.getInstance(modal);
            if (bootstrapModal) {
                bootstrapModal.hide();
            }

        } catch (error) {
            console.error('Upload additional faces error:', error);
            this.showMessage(`Face storage failed: ${error.message}`, 'error');
        } finally {
            uploadBtn.innerHTML = originalText;
            uploadBtn.disabled = false;
        }
    }

    // Refresh the personnel details page
    async refreshPersonDetails(personId) {
        const detailModal = document.getElementById('personDetailModal');
        if (!detailModal) return;

        // Retrieve the latest personnel data
        const person = this.allPersons.find(p => p.id === personId);
        if (!person) return;

        // Update photo area
        const faceGallery = detailModal.querySelector('.face-gallery');
        if (faceGallery) {
            faceGallery.innerHTML = await this.generateFaceGallery(person);
        }

        // Update photo quantity display
        const faceCountElements = detailModal.querySelectorAll('.badge');
        faceCountElements.forEach(element => {
            if (element.textContent.includes('open')) {
                element.textContent = `${person.face_count || person.encodings_count || 0} open`;
            }
        });
        
        // Update photo quantity information in details page
        const infoCards = detailModal.querySelectorAll('.info-card');
        infoCards.forEach(card => {
            const label = card.querySelector('.info-label');
            if (label && label.textContent.includes('Number of photos')) {
                const valueElement = card.querySelector('.info-value .badge');
                if (valueElement) {
                    valueElement.textContent = `${person.face_count || person.encodings_count || 0} open`;
                }
            }
        });
    }

    // Methods related to batch operations
    enableBulkSelection() {
        this.bulkSelectionMode = true;
        // Refresh display to show checkbox
        this.displayPersons();
    }

    disableBulkSelection() {
        this.bulkSelectionMode = false;
        this.selectedPersons = new Set();
        // Refresh display to hide checkbox
        this.displayPersons();
        this.updateBulkOperationButtons();
    }

    clearAllSelections() {
        this.selectedPersons.clear();
        // Update all checkbox states
        const checkboxes = document.querySelectorAll('.person-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        this.updateBulkOperationButtons();
    }

    updateBulkOperationButtons() {
        const selectedCount = this.selectedPersons.size;
        const countElement = document.getElementById('selectedCount');
        if (countElement) {
            countElement.textContent = `(Selected ${selectedCount} item)`;
        }

        const exportBtn = document.getElementById('bulkExportBtn');
        const deleteBtn = document.getElementById('bulkDeleteBtn');
        
        if (exportBtn) {
            exportBtn.disabled = selectedCount === 0;
        }
        if (deleteBtn) {
            deleteBtn.disabled = selectedCount === 0;
        }
    }

    togglePersonSelection(personId) {
        if (this.selectedPersons.has(personId)) {
            this.selectedPersons.delete(personId);
        } else {
            this.selectedPersons.add(personId);
        }
        this.updateBulkOperationButtons();
    }

    // accomplishselectAllPersonsFunction
    selectAllPersons() {
        // Select all currently filtered people
        this.filteredPersons.forEach(person => {
            this.selectedPersons.add(person.id);
        });
        
        // Update all checkbox states
        this.updateAllCheckboxes();
        this.updateBulkOperationButtons();
    }

    // Update all checkbox states
    updateAllCheckboxes() {
        this.filteredPersons.forEach(person => {
            const checkboxes = document.querySelectorAll(`input[data-person-id="${person.id}"]`);
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.selectedPersons.has(person.id);
            });
        });
    }

    // Implement batch deletion function
    async bulkDeletePersons() {
        if (this.selectedPersons.size === 0) {
            this.showMessage('Please select the person you want to delete first', 'warning');
            return;
        }

        const selectedPersonsArray = Array.from(this.selectedPersons);
        const selectedPersonsData = selectedPersonsArray.map(id => 
            this.allPersons.find(p => p.id === id)
        ).filter(p => p); // filter outundefined

        // Display batch deletion confirmation dialog box
        const confirmed = await this.showBulkDeleteConfirmDialog(selectedPersonsData);
        if (!confirmed) return;

        // Perform batch deletion
        let successCount = 0;
        let failCount = 0;

        for (const person of selectedPersonsData) {
            try {
                // call trueAPIDelete people using emp_id
                const response = await fetch(`/api/person/${person.emp_id}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        successCount++;
                    } else {
                        throw new Error(data.message || 'Delete operation failed');
                    }
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (error) {
                failCount++;
                console.error(`Delete people ${person.name} fail:`, error);
            }
        }

        // Remove successfully deleted people from local data
        if (successCount > 0) {
            const successfullyDeletedIds = selectedPersonsArray.slice(0, successCount);
            this.allPersons = this.allPersons.filter(p => !successfullyDeletedIds.includes(p.id));
            this.filteredPersons = this.filteredPersons.filter(p => !successfullyDeletedIds.includes(p.id));
        }
        
        // Clear selection
        this.selectedPersons.clear();

        // Show results
        if (successCount > 0) {
            this.showMessage(`successfully deleted ${successCount} personal personnel${failCount > 0 ? `，${failCount} a failure` : ''}`, successCount === selectedPersonsData.length ? 'success' : 'warning');
            this.addRecentOperation('Batch delete', `Deleted in batches ${successCount} personal personnel`);
        } else {
            this.showMessage('Batch deletion failed', 'error');
        }

        // refresh display
        this.displayPersons();
        this.updateStatistics();
        this.updateBulkOperationButtons();
    }

    // Implement batch export function
    async exportSelectedPersons() {
        if (this.selectedPersons.size === 0) {
            this.showMessage('Please select the person you want to export first', 'warning');
            return;
        }

        const selectedPersonsArray = Array.from(this.selectedPersons);
        const selectedPersonsData = selectedPersonsArray.map(id => 
            this.allPersons.find(p => p.id === id)
        ).filter(p => p);

        try {
            // Prepare to export data
            const exportData = {
                export_time: new Date().toISOString(),
                export_count: selectedPersonsData.length,
                persons: selectedPersonsData.map(person => ({
                    id: person.id,
                    name: person.name,
                    description: person.description || '',
                    face_count: person.face_count || person.encodings_count || 0,
                    created_at: person.created_at,
                    face_image_url: person.face_image_url || ''
                }))
            };

            // Create and downloadJSONdocument
            const jsonString = JSON.stringify(exportData, null, 2);
            const blob = new Blob([jsonString], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `Personnel data export_${new Date().toLocaleDateString('zh-CN').replace(/\//g, '-')}_${selectedPersonsData.length}people.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            URL.revokeObjectURL(url);

            this.showMessage(`Exported successfully ${selectedPersonsData.length} personal data`, 'success');
            this.addRecentOperation('Data export', `Exported ${selectedPersonsData.length} personal data`);

        } catch (error) {
            console.error('Export error:', error);
            this.showMessage(`Export failed: ${error.message}`, 'error');
        }
    }

    // Display batch deletion confirmation dialog box
    showBulkDeleteConfirmDialog(persons) {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'bulkDeleteConfirmModal';
            
            const totalFaces = persons.reduce((sum, person) => {
                return sum + (person.face_count || person.encodings_count || 0);
            }, 0);
            
            modal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered modal-lg">
                    <div class="modal-content border-0 shadow-lg">
                        <div class="modal-header bg-danger text-white border-0">
                            <h5 class="modal-title">
                                <i class="bi bi-exclamation-triangle me-2"></i>Confirm batch deletion
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body p-4">
                            <div class="alert alert-danger">
                                <i class="bi bi-exclamation-triangle me-2"></i>
                                <strong>warn：</strong>You are about to delete <strong>${persons.length}</strong> All information about a person，include：
                                <ul class="mt-2 mb-0">
                                    <li>Basic information of all personnel</li>
                                    <li>total <strong>${totalFaces}</strong> face photo</li>
                                    <li>Relevant identification records</li>
                                </ul>
                            </div>
                            
                            <div class="mb-3">
                                <h6>Person to be deleted：</h6>
                                <div class="border rounded p-3" style="max-height: 200px; overflow-y: auto;">
                                    ${persons.map(person => `
                                        <div class="d-flex align-items-center mb-2">
                                            <div class="me-2">
                                                ${this.getPersonAvatarSmall(person)}
                                            </div>
                                            <div>
                                                <div class="fw-medium">${person.name}</div>
                                                <small class="text-muted">ID: ${person.id} | ${person.face_count || person.encodings_count || 0} photo</small>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                            
                            <div class="alert alert-warning">
                                <i class="bi bi-info-circle me-2"></i>
                                <strong>Notice：</strong>This action is irreversible，Please confirm before continuing。
                            </div>
                        </div>
                        <div class="modal-footer border-0">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="bi bi-x me-1"></i>Cancel
                            </button>
                            <button type="button" class="btn btn-danger" id="confirmBulkDelete">
                                <i class="bi bi-trash me-1"></i>Confirm deletion ${persons.length} personal personnel
                            </button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            if (window.bootstrap) {
                const bootstrapModal = new bootstrap.Modal(modal);
                bootstrapModal.show();

                // Confirm button event
                const confirmBtn = modal.querySelector('#confirmBulkDelete');
                confirmBtn.addEventListener('click', () => {
                    bootstrapModal.hide();
                    resolve(true);
                });

                // Modal box close event
                modal.addEventListener('hidden.bs.modal', () => {
                    document.body.removeChild(modal);
                    resolve(false);
                });
            } else {
                resolve(confirm(`Are you sure you want to delete this ${persons.length} Personnel?？`));
            }
        });
    }

    async deletePerson(personId) {
        const person = this.allPersons.find(p => p.id === personId);
        if (!person) {
            this.showMessage('Personnel information does not exist', 'error');
            return;
        }

        // Create elegant confirmation dialogs
        const result = await this.showDeleteConfirmDialog(person);
        if (!result) return;

        try {
            // Get person to find emp_id
            const person = this.allPersons.find(p => p.id === personId);
            if (!person) {
                throw new Error('Person not found');
            }
            
            // call trueAPIDelete people using emp_id
            const response = await fetch(`/api/person/${person.emp_id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // Remove from local data
                    this.allPersons = this.allPersons.filter(p => p.id !== personId);
                    this.filteredPersons = this.filteredPersons.filter(p => p.id !== personId);
                    this.selectedPersons.delete(personId);
                    
                    this.showMessage(`personnel "${person.name}" Deleted successfully`, 'success');
                    this.displayPersons();
                    this.updateStatistics();
                    this.updateBulkOperationButtons();
                    this.addRecentOperation('Delete people', `Removed person: ${person.name}`);
                } else {
                    throw new Error(data.message || 'Delete operation failed');
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }

        } catch (error) {
            console.error('Delete person error:', error);
            this.showMessage(`Delete failed: ${error.message}`, 'error');
        }
    }

    showDeleteConfirmDialog(person) {
        return new Promise((resolve) => {
            // Remove existing confirmation dialog
            const existingModal = document.getElementById('deleteConfirmModal');
            if (existingModal) {
                existingModal.remove();
            }

            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'deleteConfirmModal';
            modal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg">
                        <div class="modal-header bg-danger text-white border-0">
                            <h5 class="modal-title">
                                <i class="bi bi-exclamation-triangle-fill me-2"></i>Confirm deletion
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body p-4">
                            <div class="text-center mb-4">
                                <div class="d-inline-block position-relative">
                                    ${this.getPersonAvatar(person).replace(/onclick="[^"]*"/g, '')}
                                </div>
                            </div>
                            
                            <div class="alert alert-warning border-0 bg-warning bg-opacity-10">
                                <i class="bi bi-exclamation-triangle text-warning me-2"></i>
                                <strong>This action cannot be undone！</strong>
                            </div>
                            
                            <p class="text-center mb-4">
                                Are you sure you want to delete the person <strong class="text-danger">"${person.name}"</strong> ?？
                            </p>
                            
                            <div class="bg-light rounded p-3 mb-3">
                                <h6 class="text-muted mb-2">Data to be deleted：</h6>
                                <ul class="list-unstyled mb-0 small">
                                    <li><i class="bi bi-person text-primary me-2"></i>Basic information of personnel</li>
                                    <li><i class="bi bi-images text-success me-2"></i>${person.face_count || person.encodings_count || 0} face photo</li>
                                    <li><i class="bi bi-clock-history text-info me-2"></i>All relevant identification records</li>
                                </ul>
                            </div>
                        </div>
                        <div class="modal-footer border-0 bg-light">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="bi bi-x-lg me-1"></i>Cancel
                            </button>
                            <button type="button" class="btn btn-danger" id="confirmDeleteBtn">
                                <i class="bi bi-trash me-1"></i>Confirm deletion
                            </button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);
            
            const confirmBtn = modal.querySelector('#confirmDeleteBtn');
            confirmBtn.addEventListener('click', () => {
                resolve(true);
                if (window.bootstrap) {
                    const bootstrapModal = bootstrap.Modal.getInstance(modal);
                    if (bootstrapModal) {
                        bootstrapModal.hide();
                    }
                }
            });

            if (window.bootstrap) {
                const bootstrapModal = new bootstrap.Modal(modal);
                bootstrapModal.show();
                
                modal.addEventListener('hidden.bs.modal', () => {
                    resolve(false);
                    document.body.removeChild(modal);
                });
            }
        });
    }

    async bulkDeletePersons() {
        if (this.selectedPersons.size === 0) {
            this.showMessage('Please select the person you want to delete first', 'warning');
            return;
        }

        const selectedCount = this.selectedPersons.size;
        if (!confirm(`Are you sure you want to delete the selected ${selectedCount} Personnel?？This operation is irreversible。`)) {
            return;
        }

        try {
            const selectedIds = Array.from(this.selectedPersons);
            let successCount = 0;

            for (const personId of selectedIds) {
                try {
                    // Get person to find emp_id
                    const person = this.allPersons.find(p => p.id === personId);
                    if (!person) {
                        throw new Error('Person not found');
                    }
                    
                    // call trueAPIDelete people using emp_id
                    const response = await fetch(`/api/person/${person.emp_id}`, {
                        method: 'DELETE'
                    });
                    if (response.ok) {
                        const data = await response.json();
                        if (data.success) {
                            successCount++;
                        }
                    }
                } catch (apiError) {
                    console.error(`Delete people ${personId} fail:`, apiError);
                }
            }

            // Remove from local data
            this.allPersons = this.allPersons.filter(p => !this.selectedPersons.has(p.id));
            this.filteredPersons = this.filteredPersons.filter(p => !this.selectedPersons.has(p.id));
            this.selectedPersons.clear();

            this.showMessage(`successfully deleted ${successCount} personal personnel`, 'success');
            this.displayPersons();
            this.updateStatistics();
            this.updateBulkOperationButtons();
            this.addRecentOperation('Batch delete', `Deleted in batches ${successCount} personal personnel`);

        } catch (error) {
            console.error('Bulk delete error:', error);
            this.showMessage(`Batch deletion failed: ${error.message}`, 'error');
        }
    }

    async exportSelectedPersons() {
        if (this.selectedPersons.size === 0) {
            this.showMessage('Please select the person you want to export first', 'warning');
            return;
        }

        try {
            const selectedPersons = this.allPersons.filter(p => this.selectedPersons.has(p.id));
            
            const exportData = {
                export_time: new Date().toISOString(),
                total_count: selectedPersons.length,
                persons: selectedPersons.map(person => ({
                    id: person.id,
                    name: person.name,
                    description: person.description,
                    encodings_count: person.encodings_count,
                    created_at: person.created_at
                }))
            };

            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `persons_export_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showMessage(`Exported successfully ${selectedPersons.length} personal data`, 'success');

        } catch (error) {
            console.error('Export persons error:', error);
            this.showMessage(`Export failed: ${error.message}`, 'error');
        }
    }

    editPersonModal(personId) {
        const person = this.allPersons.find(p => p.id === personId);
        if (!person) {
            this.showMessage('Personnel information does not exist', 'error');
            return;
        }

        // Remove existing edit modal box
        const existingModal = document.getElementById('editPersonModal');
        if (existingModal) {
            existingModal.remove();
        }

        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'editPersonModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-gradient-secondary text-white border-0">
                        <h5 class="modal-title">
                            <i class="bi bi-pencil-square me-2"></i>Editor information
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-4">
                        <form id="editPersonForm">
                            <div class="row">
                                <div class="col-12 text-center mb-4">
                                    ${this.getPersonAvatar(person)}
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="editPersonName" class="form-label">
                                    <i class="bi bi-person me-1"></i>Name <span class="text-danger">*</span>
                                </label>
                                <input type="text" class="form-control" id="editPersonName" 
                                       value="${person.name}" required maxlength="100">
                            </div>
                            
                            <div class="mb-3">
                                <label for="editPersonDesc" class="form-label">
                                    <i class="bi bi-card-text me-1"></i>describe
                                </label>
                                <textarea class="form-control" id="editPersonDesc" rows="3" 
                                          maxlength="500" placeholder="Enter person description...">${person.description || ''}</textarea>
                                <div class="form-text">most500characters</div>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">
                                    <i class="bi bi-info-circle me-1"></i>Basic information
                                </label>
                                <div class="bg-light rounded p-3">
                                    <div class="row">
                                        <div class="col-6">
                                            <small class="text-muted">personnelID:</small><br>
                                            <strong>${person.id}</strong>
                                        </div>
                                        <div class="col-6">
                                            <small class="text-muted">Number of photos:</small><br>
                                            <strong>${person.face_count || person.encodings_count || 0} open</strong>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer border-0">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="window.personManagement.savePersonEdit(${person.id})">
                            <i class="bi bi-check-lg me-1"></i>Save changes
                        </button>
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
        }
    }

    async savePersonEdit(personId) {
        const nameInput = document.getElementById('editPersonName');
        const descInput = document.getElementById('editPersonDesc');
        
        if (!nameInput || !descInput) {
            this.showMessage('Form element does not exist', 'error');
            return;
        }

        const newName = nameInput.value.trim();
        const newDesc = descInput.value.trim();

        if (!newName) {
            this.showMessage('Name cannot be empty', 'warning');
            nameInput.focus();
            return;
        }

        try {
            // Get person to find emp_id
            const person = this.allPersons.find(p => p.id === personId);
            if (!person) {
                throw new Error('Person not found');
            }
            
            // call trueAPIUpdate personnel information using emp_id
            const response = await fetch(`/api/person/${person.emp_id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: newName,
                    description: newDesc
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // Update local data
                    const person = this.allPersons.find(p => p.id === personId);
                    if (person) {
                        const oldName = person.name;
                        person.name = newName;
                        person.description = newDesc;
                        
                        this.displayPersons();
                        this.showMessage('Personnel information has been updated', 'success');
                        this.addRecentOperation('Editorial Staff', `Will "${oldName}" information updated to "${newName}"`);
                        
                        // Close modal box
                        const modal = bootstrap.Modal.getInstance(document.getElementById('editPersonModal'));
                        if (modal) {
                            modal.hide();
                        }
                    }
                } else {
                    throw new Error(data.message || 'Update failed');
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
            
        } catch (error) {
            console.error('Save person edit error:', error);
            this.showMessage(`Update failed: ${error.message}`, 'error');
        }
    }

    async deletePersonConfirm(personId) {
        const person = this.allPersons.find(p => p.id === personId);
        if (!person) {
            this.showMessage('Personnel information does not exist', 'error');
            return;
        }

        // Close the details modal box
        const detailModal = bootstrap.Modal.getInstance(document.getElementById('personDetailModal'));
        if (detailModal) {
            detailModal.hide();
        }

        // Delay in showing elegant confirmation dialog
        setTimeout(async () => {
            const confirmed = await this.showDeleteConfirmDialog(person);
            if (confirmed) {
                this.deletePerson(personId);
            }
        }, 300);
    }

    showMessage(message, type = 'info') {
        // Show message notification
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // if there is ToastManager，use it
        if (window.ToastManager) {
            window.ToastManager.show(message, type);
        } else {
            // Otherwise use simple alert
            if (type === 'error') {
                alert('mistake: ' + message);
            } else if (type === 'warning') {
                alert('warn: ' + message);
            } else if (type === 'success') {
                alert('success: ' + message);
            }
        }
    }

    showLoading(show) {
        const container = document.getElementById('personsList');
        if (!container) return;

        if (show) {
            container.innerHTML = `
                <div class="d-flex justify-content-center p-5">
                    <div class="text-center">
                        <div class="spinner-border text-primary mb-3" role="status">
                            <span class="visually-hidden">loading...</span>
                        </div>
                        <p class="text-muted">Loading personnel data...</p>
                    </div>
                </div>
            `;
        }
        // Note: When show is false, displayPersons() will be called to show the actual content
    }

    displayError(message) {
        const container = document.getElementById('personsList');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    <strong>Loading failed</strong>
                    <br><small>${message}</small>
                    <div class="mt-2">
                        <button class="btn btn-sm btn-outline-danger" onclick="personManagement.loadPersons()">
                            Try again
                        </button>
                    </div>
                </div>
            `;
        }
    }

    showError(message) {
        this.displayError(message);
        this.showMessage(message, 'error');
    }

    // Methods related to recent operations
    addRecentOperation(action, details) {
        const operation = {
            id: Date.now(),
            action: action,
            details: details,
            timestamp: new Date().toISOString()
        };
        
        // Add to front of recent actions list
        this.recentOperations.unshift(operation);
        
        // Keep only the most recent20Operation records
        if (this.recentOperations.length > 20) {
            this.recentOperations = this.recentOperations.slice(0, 20);
        }
        
        // save tolocalStorage
        localStorage.setItem('recentOperations', JSON.stringify(this.recentOperations));
        
        // Update display
        this.updateRecentOperations();
    }

    updateRecentOperations() {
        const container = document.getElementById('recentOperations');
        if (!container) return;
        
        if (this.recentOperations.length === 0) {
            container.innerHTML = '<small class="text-muted">No operation record yet</small>';
            return;
        }
        
        const recentHtml = this.recentOperations.slice(0, 5).map(op => `
            <div class="d-flex align-items-start mb-2 small">
                <div class="me-2 text-primary">
                    <i class="bi bi-${this.getOperationIcon(op.action)}"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="fw-medium">${op.action}</div>
                    <div class="text-muted small">${op.details}</div>
                    <div class="text-muted small">${this.formatTimeAgo(op.timestamp)}</div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = recentHtml;
        
        if (this.recentOperations.length > 5) {
            container.innerHTML += `
                <div class="text-center">
                    <button class="btn btn-link btn-sm p-0" onclick="window.personManagement.showAllOperations()">
                        View all ${this.recentOperations.length} records
                    </button>
                </div>
            `;
        }
    }

    getOperationIcon(action) {
        const icons = {
            'Delete people': 'trash',
            'Editorial Staff': 'pencil',
            'Add people': 'person-plus',
            'Batch delete': 'trash-fill',
            'Export data': 'download',
            'Refresh data': 'arrow-clockwise'
        };
        return icons[action] || 'info-circle';
    }

    formatTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffMinutes = Math.floor((now - time) / (1000 * 60));
        
        if (diffMinutes < 1) return 'just';
        if (diffMinutes < 60) return `${diffMinutes}minutes ago`;
        
        const diffHours = Math.floor(diffMinutes / 60);
        if (diffHours < 24) return `${diffHours}hours ago`;
        
        const diffDays = Math.floor(diffHours / 24);
        if (diffDays < 7) return `${diffDays}days ago`;
        
        return time.toLocaleDateString('zh-CN');
    }

    showAllOperations() {
        // Create complete operation record dialog box
        const existingModal = document.getElementById('operationsHistoryModal');
        if (existingModal) {
            existingModal.remove();
        }

        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'operationsHistoryModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content border-0 shadow">
                    <div class="modal-header bg-light border-0">
                        <h5 class="modal-title">
                            <i class="bi bi-clock-history me-2"></i>Operation history
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-0">
                        <div class="list-group list-group-flush">
                            ${this.recentOperations.map(op => `
                                <div class="list-group-item">
                                    <div class="d-flex align-items-start">
                                        <div class="me-3 text-primary">
                                            <i class="bi bi-${this.getOperationIcon(op.action)} fs-5"></i>
                                        </div>
                                        <div class="flex-grow-1">
                                            <h6 class="mb-1">${op.action}</h6>
                                            <p class="mb-1 text-muted">${op.details}</p>
                                            <small class="text-muted">${new Date(op.timestamp).toLocaleString('zh-CN')}</small>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="modal-footer border-0">
                        <button type="button" class="btn btn-outline-danger btn-sm" onclick="window.personManagement.clearOperationHistory()">
                            <i class="bi bi-trash me-1"></i>clear record
                        </button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">closure</button>
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
        }
    }

    clearOperationHistory() {
        if (confirm('Are you sure you want to clear all operation records?？')) {
            this.recentOperations = [];
            localStorage.removeItem('recentOperations');
            this.updateRecentOperations();
            this.showMessage('Operation record has been cleared', 'success');
            
            // Close modal box
            const modal = bootstrap.Modal.getInstance(document.getElementById('operationsHistoryModal'));
            if (modal) {
                modal.hide();
            }
        }
    }

    // Batch face storage function
    showBatchFaceEnrollmentModal() {
        // Remove existing modal box
        const existingModal = document.getElementById('batchFaceEnrollmentModal');
        if (existingModal) {
            existingModal.remove();
        }

        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'batchFaceEnrollmentModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-primary text-white border-0">
                        <h5 class="modal-title">
                            <i class="bi bi-person-plus-fill me-2"></i>Batch face storage
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-4">
                        <div class="alert alert-info border-0">
                            <i class="bi bi-info-circle me-2"></i>
                            <strong>Instructions for batch face storage：</strong><br>
                            • Support uploading multiple face photos，The system will automatically recognize faces and store them in the database<br>
                            • Can add more face photos for existing people，or create new person<br>
                            • Supports automatic extraction of person names from file names<br>
                            • maximum per photo5MB，supportJPG、PNGFormat
                        </div>

                        <div class="mb-4">
                            <label class="form-label fw-bold">
                                <i class="bi bi-upload me-1"></i>Select face photo
                            </label>
                            <div class="upload-area border-2 border-dashed border-primary rounded p-4 text-center mb-3" 
                                 id="batchUploadArea" onclick="document.getElementById('batchFaceFiles').click()">
                                <i class="bi bi-cloud-upload text-primary mb-2" style="font-size: 3rem;"></i>
                                <h6 class="text-primary">Click to select or drag photos here</h6>
                                <p class="text-muted small mb-0">Support multiple selection，The system will automatically extract the person's name from the file name</p>
                                <input type="file" class="d-none" id="batchFaceFiles" multiple accept="image/*">
                            </div>
                            
                            <div id="batchFacePreview" class="d-none">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <h6 class="small text-muted mb-0">Preview (<span id="previewCount">0</span> photo)：</h6>
                                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="this.parentElement.parentElement.parentElement.querySelector('#batchFaceFiles').click()">
                                        <i class="bi bi-plus me-1"></i>add more
                                    </button>
                                </div>
                                <div id="batchFaceImages" class="row g-2" style="max-height: 300px; overflow-y: auto;"></div>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-6">
                                <label class="form-label">
                                    <i class="bi bi-gear me-1"></i>Warehousing mode
                                </label>
                                <div class="form-check">
                                    <input class="form-check-input" type="radio" name="enrollmentMode" id="autoMode" value="auto" checked>
                                    <label class="form-check-label" for="autoMode">
                                        <strong>automatic mode</strong><br>
                                        <small class="text-muted">Automatically extract names from file names</small>
                                    </label>
                                </div>
                                <div class="form-check mt-2">
                                    <input class="form-check-input" type="radio" name="enrollmentMode" id="manualMode" value="manual">
                                    <label class="form-check-label" for="manualMode">
                                        <strong>manual mode</strong><br>
                                        <small class="text-muted">Manually specify person information</small>
                                    </label>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div id="manualModeOptions" class="d-none">
                                    <label for="batchPersonName" class="form-label">
                                        <i class="bi bi-person me-1"></i>unified name（Optional）
                                    </label>
                                    <input type="text" class="form-control mb-2" id="batchPersonName" 
                                           placeholder="Leave blank to use filename">
                                    
                                    <label for="batchPersonDesc" class="form-label">
                                        <i class="bi bi-card-text me-1"></i>unified description（Optional）
                                    </label>
                                    <input type="text" class="form-control" id="batchPersonDesc" 
                                           placeholder="Add a unified description to all your photos">
                                </div>
                                <div id="autoModeInfo" class="">
                                    <div class="alert alert-light border mb-0">
                                        <small class="text-muted">
                                            <i class="bi bi-lightbulb me-1"></i>
                                            <strong>File naming suggestions：</strong><br>
                                            • Zhang San.jpg → Name：Zhang San<br>
                                            • John_Smith.png → Name：John Smith<br>
                                            • staff001.jpg → Name：staff001
                                        </small>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="batchResults" class="mt-3 d-none">
                            <h6 class="text-muted mb-2">
                                <i class="bi bi-list-check me-1"></i>Storage results：
                            </h6>
                            <div id="batchResultsContent"></div>
                        </div>
                    </div>
                    <div class="modal-footer border-0">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="bi bi-x me-1"></i>closure
                        </button>
                        <button type="button" class="btn btn-primary" id="startBatchEnrollment" disabled>
                            <i class="bi bi-database-add me-1"></i>Start batch storage
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        if (window.bootstrap) {
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();

            // Binding events
            this.bindBatchFaceEnrollmentEvents(modal);

            modal.addEventListener('hidden.bs.modal', () => {
                document.body.removeChild(modal);
            });
        }
    }

    bindBatchFaceEnrollmentEvents(modal) {
        const fileInput = modal.querySelector('#batchFaceFiles');
        const uploadArea = modal.querySelector('#batchUploadArea');
        const startBtn = modal.querySelector('#startBatchEnrollment');
        const autoMode = modal.querySelector('#autoMode');
        const manualMode = modal.querySelector('#manualMode');
        const manualOptions = modal.querySelector('#manualModeOptions');
        const autoInfo = modal.querySelector('#autoModeInfo');

        // File selection event
        fileInput.addEventListener('change', (e) => {
            this.handleBatchFaceFiles(e.target.files, modal);
        });

        // Drag and drop upload
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('border-success');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('border-success');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('border-success');
            this.handleBatchFaceFiles(e.dataTransfer.files, modal);
        });

        // Mode switching
        autoMode.addEventListener('change', () => {
            if (autoMode.checked) {
                manualOptions.classList.add('d-none');
                autoInfo.classList.remove('d-none');
            }
        });

        manualMode.addEventListener('change', () => {
            if (manualMode.checked) {
                manualOptions.classList.remove('d-none');
                autoInfo.classList.add('d-none');
            }
        });

        // Start batch storage
        startBtn.addEventListener('click', () => {
            this.performBatchFaceEnrollment(modal);
        });
    }

    handleBatchFaceFiles(files, modal) {
        const preview = modal.querySelector('#batchFacePreview');
        const container = modal.querySelector('#batchFaceImages');
        const startBtn = modal.querySelector('#startBatchEnrollment');
        const countSpan = modal.querySelector('#previewCount');

        if (files.length === 0) {
            preview.classList.add('d-none');
            startBtn.disabled = true;
            return;
        }

        // Save the file to the modal box data
        modal._batchFiles = Array.from(files);
        countSpan.textContent = files.length;

        container.innerHTML = '';

        Array.from(files).forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const col = document.createElement('div');
                col.className = 'col-3 mb-2';
                
                // Extract possible names from file names
                const fileName = file.name;
                const nameFromFile = fileName.replace(/\.(jpg|jpeg|png|gif|bmp|webp)$/i, '')
                                             .replace(/[_-]/g, ' ')
                                             .trim() || 'Unnamed';

                col.innerHTML = `
                    <div class="position-relative">
                        <img src="${e.target.result}" class="img-fluid rounded border" 
                             style="height: 80px; object-fit: cover; width: 100%;" 
                             alt="${fileName}">
                        <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 m-1" 
                                onclick="this.closest('.col-3').remove(); window.personManagement.updateBatchFileCount()" 
                                title="Remove">
                            <i class="bi bi-x"></i>
                        </button>
                        <div class="position-absolute bottom-0 start-0 end-0 bg-dark bg-opacity-75 text-white p-1 rounded-bottom small text-center">
                            ${nameFromFile.length > 8 ? nameFromFile.substring(0, 8) + '...' : nameFromFile}
                        </div>
                    </div>
                `;
                container.appendChild(col);
            };
            reader.readAsDataURL(file);
        });

        preview.classList.remove('d-none');
        startBtn.disabled = false;
    }

    updateBatchFileCount() {
        const modal = document.getElementById('batchFaceEnrollmentModal');
        if (!modal) return;

        const images = modal.querySelectorAll('#batchFaceImages .col-3');
        const countSpan = modal.querySelector('#previewCount');
        const startBtn = modal.querySelector('#startBatchEnrollment');

        const count = images.length;
        countSpan.textContent = count;
        startBtn.disabled = count === 0;

        if (count === 0) {
            modal.querySelector('#batchFacePreview').classList.add('d-none');
        }
    }

    async performBatchFaceEnrollment(modal) {
        const files = modal._batchFiles;
        if (!files || files.length === 0) {
            this.showMessage('Please select a face photo first', 'warning');
            return;
        }

        const startBtn = modal.querySelector('#startBatchEnrollment');
        const results = modal.querySelector('#batchResults');
        const resultsContent = modal.querySelector('#batchResultsContent');
        const autoMode = modal.querySelector('#autoMode').checked;
        const manualName = modal.querySelector('#batchPersonName').value.trim();
        const manualDesc = modal.querySelector('#batchPersonDesc').value.trim();

        const originalBtnText = startBtn.innerHTML;
        startBtn.innerHTML = '<i class="bi bi-spinner bi-spin me-1"></i>Loading in batches...';
        startBtn.disabled = true;

        try {
            const formData = new FormData();
            
            // Add files
            files.forEach(file => {
                formData.append('files', file);
            });

            // If it is manual mode and a name is specified，Add name parameter
            if (!autoMode && manualName) {
                formData.append('name', manualName);
            }

            // If description is specified，Add description parameters
            if (manualDesc) {
                formData.append('description', manualDesc);
            }

            const response = await fetch('/api/batch_enroll', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            // Show results
            this.displayBatchEnrollmentResults(result, resultsContent);
            results.classList.remove('d-none');

            if (result.success && result.success_count > 0) {
                this.showMessage(`Batch storage completed：success ${result.success_count} indivual，fail ${result.error_count} indivual`, 
                    result.error_count === 0 ? 'success' : 'warning');
                this.addRecentOperation('Batch face storage', `Warehoused in batches ${result.success_count} face photo`);
                
                // Refresh person list
                await this.loadPersons();
            } else {
                this.showMessage('Batch storage failed', 'error');
            }

        } catch (error) {
            console.error('Batch face enrollment error:', error);
            this.showMessage(`Batch storage failed: ${error.message}`, 'error');
        } finally {
            startBtn.innerHTML = originalBtnText;
            startBtn.disabled = false;
        }
    }

    displayBatchEnrollmentResults(result, container) {
        if (!result || !container) return;

        let html = `
            <div class="alert alert-${result.error_count === 0 ? 'success' : 'warning'} border-0">
                <div class="d-flex align-items-center mb-2">
                    <i class="bi bi-${result.error_count === 0 ? 'check-circle-fill' : 'exclamation-triangle-fill'} me-2"></i>
                    <strong>Batch storage completed</strong>
                </div>
                <div class="row text-center">
                    <div class="col-4">
                        <div class="fs-4 fw-bold">${result.total_files || 0}</div>
                        <small class="text-muted">total</small>
                    </div>
                    <div class="col-4">
                        <div class="fs-4 fw-bold text-success">${result.success_count || 0}</div>
                        <small class="text-muted">success</small>
                    </div>
                    <div class="col-4">
                        <div class="fs-4 fw-bold text-danger">${result.error_count || 0}</div>
                        <small class="text-muted">fail</small>
                    </div>
                </div>
            </div>
        `;

        if (result.results && result.results.length > 0) {
            html += '<div class="mt-3"><h6 class="small text-muted mb-2">Detailed results：</h6>';
            
            result.results.forEach((item, index) => {
                const statusClass = item.success ? 'success' : 'danger';
                const statusIcon = item.success ? 'check-circle-fill' : 'x-circle-fill';
                
                html += `
                    <div class="card border-${statusClass} mb-2">
                        <div class="card-body p-2">
                            <div class="d-flex align-items-center">
                                <i class="bi bi-${statusIcon} text-${statusClass} me-2"></i>
                                <div class="flex-grow-1 small">
                                    <div class="fw-bold">${item.file_name}</div>
                                    <div class="text-muted">
                                        ${item.name ? `Name: ${item.name}` : ''}
                                        ${item.success ? 
                                            `${item.person_id ? ` | personnelID: ${item.person_id}` : ''}${item.face_encoding_id ? ` | human faceID: ${item.face_encoding_id}` : ''}${item.quality_score ? ` | quality: ${(item.quality_score * 100).toFixed(1)}%` : ''}` :
                                            ` | mistake: ${item.error}`
                                        }
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
        }

        container.innerHTML = html;
    }
}

// global function
function showBulkOperations() {
    const panel = document.getElementById('bulkOperationsPanel');
    if (panel) {
        const isVisible = panel.style.display !== 'none';
        panel.style.display = isVisible ? 'none' : 'block';
        
        if (window.personManagement) {
            window.personManagement.showMessage(
                isVisible ? 'Batch operation panel is hidden' : 'Batch operation panel is displayed', 
                'info'
            );
        }
    }
}

function selectAllPersons() {
    if (window.personManagement) {
        window.personManagement.selectedPersons.clear();
        window.personManagement.filteredPersons.forEach(person => 
            window.personManagement.selectedPersons.add(person.id)
        );
        
        // Update all checkbox states
        window.personManagement.filteredPersons.forEach(person => {
            const checkbox1 = document.getElementById(`person_${person.id}`);
            const checkbox2 = document.getElementById(`person_list_${person.id}`);
            if (checkbox1) checkbox1.checked = true;
            if (checkbox2) checkbox2.checked = true;
        });
        
        window.personManagement.updateBulkOperationButtons();
        window.personManagement.showMessage(`Selected ${window.personManagement.selectedPersons.size} personal personnel`, 'info');
    }
}

function clearSelection() {
    if (window.personManagement) {
        window.personManagement.selectedPersons.clear();
        
        // Clear all checkbox states
        document.querySelectorAll('input[type="checkbox"][data-person-id]').forEach(cb => {
            cb.checked = false;
        });
        
        const selectAllCheckbox = document.getElementById('selectAll');
        if (selectAllCheckbox) selectAllCheckbox.checked = false;
        
        window.personManagement.updateBulkOperationButtons();
        window.personManagement.showMessage('All selections cleared', 'info');
    }
}

function bulkDeletePersons() {
    if (window.personManagement) {
        window.personManagement.bulkDeletePersons();
    } else {
        alert('Personnel management module not loaded');
    }
}

function exportSelectedPersons() {
    if (window.personManagement) {
        window.personManagement.exportSelectedPersons();
    } else {
        alert('Personnel management module not loaded');
    }
}

// Batch face storage function
function showBatchFaceEnrollment() {
    if (window.personManagement) {
        window.personManagement.showBatchFaceEnrollmentModal();
    } else {
        alert('Personnel management module not loaded');
    }
}

// Export to global scope
window.PersonManagement = PersonManagement;

// 人员管理模块
class PersonManagement {
    constructor() {
        this.allPersons = [];
        this.filteredPersons = [];
        this.currentPerson = null;
        this.selectedPersons = new Set();
        this.viewMode = 'card'; // 'card' or 'list'
        this.sortBy = 'created_at'; // 'created_at', 'name', 'face_count'
        this.sortOrder = 'desc'; // 'asc' or 'desc'
        this.bulkSelectionMode = false; // 批量选择模式
        this.recentOperations = JSON.parse(localStorage.getItem('recentOperations') || '[]');
        
        // 分页相关属性
        this.currentPage = 1;
        this.pageSize = parseInt(localStorage.getItem('personManagement_pageSize')) || 20; // 从localStorage加载用户偏好
        this.totalPages = 1;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadPersons();
    }

    bindEvents() {
        // 搜索
        const searchInput = document.getElementById('searchPerson');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterPersons(e.target.value);
            });
        }

        // 视图模式切换
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

        // 刷新按钮
        const refreshBtn = document.querySelector('[onclick="refreshPersonList()"]');
        if (refreshBtn) {
            refreshBtn.onclick = () => this.loadPersons();
        }

        // 排序按钮
        const sortBtn = document.querySelector('[onclick="showSortOptions()"]');
        if (sortBtn) {
            sortBtn.onclick = () => this.showSortOptions();
        }
    }

    async loadPersons() {
        try {
            // 显示加载状态
            this.showLoading(true);
            
            // 尝试从真实API加载数据
            let data;
            try {
                const response = await fetch('/api/persons');
                if (response.ok) {
                    data = await response.json();
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (apiError) {
                console.error('无法获取人员数据:', apiError);
                // 显示错误而不是使用模拟数据
                data = [];
                this.showError('无法获取人员数据，请检查后端服务是否正常运行');
            }
            
            this.allPersons = data.persons || data || [];
            this.filteredPersons = [...this.allPersons];
            this.sortPersons(); // 添加排序
            this.updatePagination(); // 添加分页更新
            this.displayPersons();
            this.updateStatistics();
            this.updateRecentOperations(); // 更新最近操作显示
            
            // 更新计数
            const countElement = document.querySelector('.person-count');
            if (countElement) {
                countElement.textContent = `${this.allPersons.length} 人`;
                countElement.className = 'badge bg-primary';
            }

        } catch (error) {
            console.error('Load persons error:', error);
            this.showMessage(`加载人员列表失败: ${error.message}`, 'error');
            this.displayError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    async updateStatistics() {
        try {
            // 获取实时统计数据
            const response = await fetch('/api/statistics');
            if (response.ok) {
                const stats = await response.json();
                
                // 更新快速统计
                const totalPersonsCount = document.getElementById('totalPersonsCount');
                const totalFacesCount = document.getElementById('totalFacesCount');
                
                if (totalPersonsCount) {
                    totalPersonsCount.textContent = stats.total_persons || this.allPersons.length;
                }
                
                if (totalFacesCount) {
                    totalFacesCount.textContent = stats.total_encodings || 0;
                }
            } else {
                // 降级到本地计算 - 只显示真实数据
                const totalPersonsCount = document.getElementById('totalPersonsCount');
                const totalFacesCount = document.getElementById('totalFacesCount');
                
                if (totalPersonsCount) {
                    totalPersonsCount.textContent = this.allPersons.length;
                }
                
                if (totalFacesCount) {
                    // 如果没有API数据，显示为0（因为没有真实的人脸数据）
                    totalFacesCount.textContent = 0;
                }
            }
        } catch (error) {
            console.error('更新统计失败:', error);
            // 使用本地数据降级
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
        
        this.sortPersons(); // 重新排序
        this.updatePagination(); // 更新分页
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

    // 分页相关方法
    updatePagination() {
        this.totalPages = Math.ceil(this.filteredPersons.length / this.pageSize);
        
        // 如果当前页面超出范围，回到第一页
        if (this.currentPage > this.totalPages) {
            this.currentPage = 1;
        }
        
        // 确保至少有1页
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
        
        // 滚动到人员列表顶部
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
        // 查找或创建分页容器
        let paginationContainer = document.getElementById('personsPagination');
        if (!paginationContainer) {
            // 在人员列表卡片的 card-body 后面添加分页控件
            const personsCard = document.getElementById('personsList')?.closest('.card');
            if (personsCard) {
                paginationContainer = document.createElement('div');
                paginationContainer.id = 'personsPagination';
                paginationContainer.className = 'card-footer bg-transparent border-top';
                personsCard.appendChild(paginationContainer);
            }
        }
        
        if (!paginationContainer) return;

        // 如果只有一页或没有数据，隐藏分页控件
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
                        <span class="small text-muted me-2">每页显示:</span>
                        <select class="form-select form-select-sm" style="width: 80px;" onchange="window.personManagement.changePageSize(this.value)">
                            <option value="10" ${this.pageSize === 10 ? 'selected' : ''}>10</option>
                            <option value="20" ${this.pageSize === 20 ? 'selected' : ''}>20</option>
                            <option value="50" ${this.pageSize === 50 ? 'selected' : ''}>50</option>
                            <option value="100" ${this.pageSize === 100 ? 'selected' : ''}>100</option>
                        </select>
                        <span class="small text-muted ms-2">项</span>
                    </div>
                </div>
                <div class="col-md-4 text-center">
                    <nav aria-label="人员列表分页">
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
                        显示第 ${startItem}-${endItem} 项，共 ${this.filteredPersons.length} 项
                        <br>第 ${this.currentPage} / ${this.totalPages} 页
                    </div>
                </div>
            </div>
        `;
    }

    changePageSize(newSize) {
        this.pageSize = parseInt(newSize);
        this.currentPage = 1; // 回到第一页
        this.updatePagination();
        this.displayPersons();
        
        // 保存用户偏好
        localStorage.setItem('personManagement_pageSize', this.pageSize);
        
        this.showMessage(`每页显示 ${this.pageSize} 项`, 'info');
    }

    generatePageNumbers() {
        let html = '';
        const maxVisiblePages = 5;
        const halfVisible = Math.floor(maxVisiblePages / 2);
        
        let startPage = Math.max(1, this.currentPage - halfVisible);
        let endPage = Math.min(this.totalPages, startPage + maxVisiblePages - 1);
        
        // 调整开始页面，确保显示足够的页码
        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }
        
        // 如果开始页面不是1，显示第一页和省略号
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
        
        // 显示页码
        for (let i = startPage; i <= endPage; i++) {
            html += `
                <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                    <button class="page-link" onclick="window.personManagement.goToPage(${i})">${i}</button>
                </li>
            `;
        }
        
        // 如果结束页面不是最后一页，显示省略号和最后一页
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
        // 移除已存在的排序对话框
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
                            <i class="bi bi-sort-down me-2"></i>排序选项
                        </h6>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-4">
                        <div class="mb-3">
                            <label class="form-label">排序方式</label>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="sortBy" value="created_at" id="sortByDate" ${this.sortBy === 'created_at' ? 'checked' : ''}>
                                <label class="form-check-label" for="sortByDate">
                                    <i class="bi bi-calendar3 me-2"></i>注册时间
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="sortBy" value="name" id="sortByName" ${this.sortBy === 'name' ? 'checked' : ''}>
                                <label class="form-check-label" for="sortByName">
                                    <i class="bi bi-person me-2"></i>姓名
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="sortBy" value="face_count" id="sortByFaceCount" ${this.sortBy === 'face_count' ? 'checked' : ''}>
                                <label class="form-check-label" for="sortByFaceCount">
                                    <i class="bi bi-images me-2"></i>照片数量
                                </label>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">排序顺序</label>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="sortOrder" value="desc" id="sortOrderDesc" ${this.sortOrder === 'desc' ? 'checked' : ''}>
                                <label class="form-check-label" for="sortOrderDesc">
                                    <i class="bi bi-sort-down me-2"></i>降序（高到低）
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="sortOrder" value="asc" id="sortOrderAsc" ${this.sortOrder === 'asc' ? 'checked' : ''}>
                                <label class="form-check-label" for="sortOrderAsc">
                                    <i class="bi bi-sort-up me-2"></i>升序（低到高）
                                </label>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer border-0">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="window.personManagement.applySorting()">
                            <i class="bi bi-check-lg me-1"></i>应用排序
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
        
        this.sortPersons(); // 重新排序
        this.updatePagination(); // 更新分页
        this.displayPersons();
        this.showMessage('排序已应用', 'success');
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('sortOptionsModal'));
        if (modal) {
            modal.hide();
        }
    }

    displayPersons() {
        const container = document.getElementById('personsList');
        if (!container) return;

        // 获取当前页面的人员数据
        const currentPagePersons = this.getCurrentPagePersons();

        if (this.filteredPersons.length === 0) {
            container.innerHTML = `
                <div class="empty-state text-center p-5">
                    <i class="bi bi-people text-muted" style="font-size: 3rem;"></i>
                    <h6 class="mt-3">暂无人员数据</h6>
                    <p class="text-muted mb-0">请先注册人员信息</p>
                </div>
            `;
            // 隐藏分页控件
            this.renderPaginationControls();
            return;
        }

        if (this.viewMode === 'card') {
            this.displayCardView(container, currentPagePersons);
        } else {
            this.displayListView(container, currentPagePersons);
        }
        
        // 更新分页控件
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
                                        <i class="bi bi-eye me-2"></i>查看详情
                                    </a></li>
                                    <li><a class="dropdown-item" href="#" onclick="window.personManagement.editPersonModal(${person.id})">
                                        <i class="bi bi-pencil me-2"></i>编辑信息
                                    </a></li>
                                    <li><hr class="dropdown-divider"></li>
                                    <li><a class="dropdown-item text-danger" href="#" onclick="window.personManagement.deletePerson(${person.id})">
                                        <i class="bi bi-trash me-2"></i>删除
                                    </a></li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="text-center mb-3">
                            <div class="position-relative d-inline-block">
                                ${this.getPersonAvatar(person)}
                                <span class="position-absolute bottom-0 end-0 bg-success border border-2 border-white rounded-circle" 
                                      style="width: 16px; height: 16px;" title="已注册"></span>
                            </div>
                        </div>
                        
                        <h6 class="card-title text-center mb-1 fw-semibold">${person.name}</h6>
                        <p class="card-text text-center text-muted small mb-3">
                            ID: ${person.id}
                        </p>
                        
                        ${person.description ? `<p class="card-text small mb-3 text-center text-secondary">"${person.description}"</p>` : ''}
                        
                        <div class="border-top pt-3 mt-3">
                            <div class="row text-center small">
                                <div class="col-6">
                                    <div class="d-flex align-items-center justify-content-center">
                                        <i class="bi bi-camera-fill text-primary me-1"></i>
                                        <span class="fw-medium">${person.encodings_count || 0}</span>
                                    </div>
                                    <small class="text-muted">照片</small>
                                </div>
                                <div class="col-6">
                                    <div class="d-flex align-items-center justify-content-center">
                                        <i class="bi bi-calendar3 text-success me-1"></i>
                                        <span class="fw-medium">${this.formatDate(person.created_at)}</span>
                                    </div>
                                    <small class="text-muted">注册</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent border-top-0 pt-0 pb-3">
                        <div class="btn-group w-100" role="group">
                            <button class="btn btn-outline-primary btn-sm" onclick="window.personManagement.showPersonDetails(${person.id})" title="查看详情">
                                <i class="bi bi-eye"></i>
                            </button>
                            <button class="btn btn-outline-secondary btn-sm" onclick="window.personManagement.editPersonModal(${person.id})" title="编辑">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-danger btn-sm" onclick="window.personManagement.deletePerson(${person.id})" title="删除">
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
        // 如果有人脸图片，显示真实头像
        if (person.face_image_url) {
            // 添加时间戳防止缓存问题
            const imageUrl = person.face_image_url + (person.face_image_url.includes('?') ? '&' : '?') + 't=' + Date.now();
            return `
                <img src="${imageUrl}" 
                     class="rounded-circle object-fit-cover cursor-pointer" 
                     style="width: 72px; height: 72px; border: 3px solid var(--bs-primary);"
                     alt="${person.name}"
                     onclick="window.personManagement.showPersonDetails(${person.id})"
                     title="点击查看详情"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                <div class="bg-primary bg-gradient rounded-circle d-none align-items-center justify-content-center cursor-pointer" 
                     style="width: 72px; height: 72px;"
                     onclick="window.personManagement.showPersonDetails(${person.id})"
                     title="点击查看详情">
                    <i class="bi bi-person-fill text-white fs-3"></i>
                </div>
            `;
        } else {
            // 使用默认头像，根据姓名生成颜色
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
                     title="点击查看详情">
                    <span class="text-white fw-bold fs-4">${person.name.charAt(0)}</span>
                </div>
            `;
        }
    }

    formatDate(dateString) {
        if (!dateString) return '未知';
        const date = new Date(dateString);
        const now = new Date();
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return '今天';
        if (diffDays === 1) return '昨天';
        if (diffDays < 7) return `${diffDays}天前`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)}周前`;
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
                            <small class="text-muted">ID: ${person.id}</small>
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
                        <button class="btn btn-outline-primary" onclick="window.personManagement.showPersonDetails(${person.id})" title="查看详情">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-outline-secondary" onclick="window.personManagement.editPersonModal(${person.id})" title="编辑">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="window.personManagement.deletePerson(${person.id})" title="删除">
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
                            <th>人员信息</th>
                            <th>描述</th>
                            <th>照片数</th>
                            <th>注册时间</th>
                            <th width="120">操作</th>
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
        // 列表视图的小头像
        if (person.face_image_url) {
            // 添加时间戳防止缓存问题
            const imageUrl = person.face_image_url + (person.face_image_url.includes('?') ? '&' : '?') + 't=' + Date.now();
            return `
                <img src="${imageUrl}" 
                     class="rounded-circle object-fit-cover cursor-pointer" 
                     style="width: 48px; height: 48px; border: 2px solid var(--bs-primary);"
                     alt="${person.name}"
                     onclick="window.personManagement.showPersonDetails(${person.id})"
                     title="点击查看详情"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                <div class="bg-primary bg-gradient rounded-circle d-none align-items-center justify-content-center cursor-pointer" 
                     style="width: 48px; height: 48px;"
                     onclick="window.personManagement.showPersonDetails(${person.id})"
                     title="点击查看详情">
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
                     title="点击查看详情">
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
        
        // 更新所有复选框状态
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
            bulkDeleteBtn.innerHTML = `<i class="bi bi-trash me-1"></i>批量删除 (${this.selectedPersons.size})`;
        }
        
        if (bulkExportBtn) {
            bulkExportBtn.disabled = !hasSelection;
            bulkExportBtn.innerHTML = `<i class="bi bi-download me-1"></i>导出数据 (${this.selectedPersons.size})`;
        }
    }

    async showPersonDetails(personId) {
        try {
            const person = this.allPersons.find(p => p.id === personId);
            if (!person) {
                this.showMessage('人员信息不存在', 'error');
                return;
            }

            this.currentPerson = person;
            
            // 创建优雅的详情模态框
            this.createPersonDetailModal(person);

        } catch (error) {
            console.error('Show person details error:', error);
            this.showMessage(`获取人员详情失败: ${error.message}`, 'error');
        }
    }

    async createPersonDetailModal(person) {
        // 移除已存在的模态框
        const existingModal = document.getElementById('personDetailModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 先生成人脸画廊
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
                                <small class="opacity-75">人员详细信息</small>
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
                                          style="width: 20px; height: 20px;" title="已注册"></span>
                                </div>
                                <div class="mt-3">
                                    <button class="btn btn-outline-primary btn-sm me-2" onclick="window.personManagement.editPersonModal(${person.id})">
                                        <i class="bi bi-pencil me-1"></i>编辑
                                    </button>
                                    <button class="btn btn-outline-danger btn-sm" onclick="window.personManagement.deletePersonConfirm(${person.id})">
                                        <i class="bi bi-trash me-1"></i>删除
                                    </button>
                                </div>
                            </div>
                            <div class="col-md-8">
                                <div class="row g-3">
                                    <div class="col-sm-6">
                                        <div class="info-card">
                                            <div class="info-label">人员ID</div>
                                            <div class="info-value">${person.id}</div>
                                        </div>
                                    </div>
                                    <div class="col-sm-6">
                                        <div class="info-card">
                                            <div class="info-label">姓名</div>
                                            <div class="info-value">${person.name}</div>
                                        </div>
                                    </div>
                                    <div class="col-12">
                                        <div class="info-card">
                                            <div class="info-label">描述</div>
                                            <div class="info-value">${person.description || '暂无描述'}</div>
                                        </div>
                                    </div>
                                    <div class="col-sm-6">
                                        <div class="info-card">
                                            <div class="info-label">照片数量</div>
                                            <div class="info-value">
                                                <span class="badge bg-primary">${person.face_count || person.encodings_count || 0} 张</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-sm-6">
                                        <div class="info-card">
                                            <div class="info-label">注册时间</div>
                                            <div class="info-value">${this.formatDate(person.created_at)}</div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mt-4">
                                    <h6 class="text-muted mb-3">
                                        <i class="bi bi-images me-2"></i>人脸照片
                                    </h6>
                                    <div class="face-gallery">
                                        ${faceGallery}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer border-0 bg-light">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <button type="button" class="btn btn-primary" onclick="window.personManagement.editPersonModal(${person.id})">
                            <i class="bi bi-pencil me-1"></i>编辑信息
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
        // 尝试获取真实的人脸照片
        let faceImages = [];
        
        try {
            // 首先尝试从专门的人脸API获取
            const response = await fetch(`/api/person/${person.id}/faces`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.face_encodings && data.face_encodings.length > 0) {
                    // 将face_encodings转换为前端需要的格式
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
            console.warn('无法从专门API获取人脸照片:', error);
        }

        // 如果仍然没有照片，返回空状态但包含添加按钮
        if (faceImages.length === 0) {
            return `
                <div class="text-center p-4">
                    <div class="text-muted mb-3">
                        <i class="bi bi-images" style="font-size: 3rem; opacity: 0.5;"></i>
                        <p class="mt-2 mb-0">暂无人脸照片</p>
                        <small class="text-muted">添加人脸照片以提高识别准确率</small>
                    </div>
                    <button class="btn btn-primary btn-sm" onclick="window.personManagement.addMoreFaces(${person.id})">
                        <i class="bi bi-plus-circle me-1"></i>添加人脸照片
                    </button>
                </div>
            `;
        }

        let gallery = '<div class="row g-2">';
        
        // 最多显示9张照片
        const displayCount = Math.min(faceImages.length, 9);
        
        for (let i = 0; i < displayCount; i++) {
            const face = faceImages[i];
            
            gallery += `
                <div class="col-4">
                    <div class="face-thumbnail position-relative">
                        <div class="face-image-container" onclick="window.personManagement.viewFaceImage('${face.id}', '${face.image_url || ''}', '${person.name}', ${i + 1})" style="cursor: pointer;">
                            ${face.image_url && face.has_image ? 
                                `<img src="${face.image_url}?t=${Date.now()}" class="img-fluid rounded" alt="人脸照片 ${i+1}" style="width: 100%; height: 80px; object-fit: cover;"
                                      onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                 <div class="bg-light rounded d-flex align-items-center justify-content-center face-placeholder" style="width: 100%; height: 80px; display: none;">
                                     <i class="bi bi-person-circle text-muted"></i>
                                 </div>` :
                                `<div class="bg-light rounded d-flex align-items-center justify-content-center face-placeholder" style="width: 100%; height: 80px;">
                                    <div class="text-center">
                                        <i class="bi bi-person-circle text-muted" style="font-size: 2rem;"></i>
                                        <div class="small text-muted mt-1">特征数据</div>
                                    </div>
                                </div>`
                            }
                        </div>
                        <div class="face-actions position-absolute top-0 end-0 p-1">
                            <div class="btn-group-vertical" role="group">
                                <button class="btn btn-sm btn-outline-danger btn-action" 
                                        onclick="event.stopPropagation(); window.personManagement.deleteFaceImage(${person.id}, '${face.id}', ${i})"
                                        title="删除此照片">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                        <div class="face-info position-absolute bottom-0 start-0 end-0 p-1">
                            <small class="text-white bg-dark bg-opacity-75 rounded px-1">
                                ${face.quality_score ? `质量: ${(face.quality_score * 100).toFixed(0)}%` : `照片 ${i+1}`}
                            </small>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // 如果还有更多照片，显示省略提示
        if (faceImages.length > displayCount) {
            gallery += `
                <div class="col-4">
                    <div class="face-thumbnail bg-light rounded d-flex align-items-center justify-content-center face-placeholder">
                        <div class="text-center">
                            <i class="bi bi-three-dots text-muted"></i>
                            <div class="small text-muted">还有${faceImages.length - displayCount}张</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        gallery += '</div>';
        
        // 添加说明和操作按钮
        gallery += `
            <div class="mt-3">
                <div class="text-center mb-2">
                    <small class="text-muted">
                        <i class="bi bi-info-circle me-1"></i>
                        共 ${faceImages.length} 张人脸照片
                    </small>
                </div>
                <div class="text-center">
                    <button class="btn btn-outline-primary btn-sm" onclick="window.personManagement.addMoreFaces(${person.id})">
                        <i class="bi bi-plus-circle me-1"></i>人脸入库
                    </button>
                </div>
            </div>
        `;
        
        return gallery;
    }

    // 查看人脸照片大图
    viewFaceImage(faceId, imageUrl, personName, faceNumber) {
        if (!imageUrl) {
            this.showMessage('该人脸特征没有关联的图片数据', 'info');
            return;
        }

        // 创建图片查看模态框
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'faceImageModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-image me-2"></i>${personName || '人员'} - 照片 ${faceNumber || ''}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center p-4">
                        <div class="position-relative d-inline-block">
                            <img src="${imageUrl}" class="img-fluid rounded shadow" alt="人脸照片" style="max-height: 500px; max-width: 100%;"
                                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                            <div class="alert alert-warning" style="display: none;">
                                <i class="bi bi-exclamation-triangle me-2"></i>
                                图片加载失败，可能图片数据已损坏或丢失
                            </div>
                        </div>
                        <div class="mt-3 text-muted small">
                            <p class="mb-1">点击照片外区域或按ESC键关闭</p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="bi bi-x me-1"></i>关闭
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

            // 点击图片外区域关闭模态框
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    bootstrapModal.hide();
                }
            });
        }
    }

    // 删除单张人脸照片
    async deleteFaceImage(personId, faceId, faceIndex) {
        const person = this.allPersons.find(p => p.id === personId);
        if (!person) {
            this.showMessage('人员信息不存在', 'error');
            return;
        }

        const confirmed = await this.showDeleteFaceConfirmDialog(person, faceIndex);
        if (!confirmed) return;

        try {
            // 调用真实API删除单张照片
            const response = await fetch(`/api/person/${personId}/faces/${faceId}`, {
                method: 'DELETE'
            });
            
            let success = false;
            if (response.ok) {
                const data = await response.json();
                success = data.success;
                if (!success) {
                    throw new Error(data.message || '删除失败');
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }

            if (success) {
                // 更新人员的人脸数量
                const currentCount = person.face_count || person.encodings_count || 0;
                if (currentCount > 0) {
                    person.face_count = currentCount - 1;
                    person.encodings_count = currentCount - 1;
                }

                this.showMessage('照片删除成功', 'success');
                this.addRecentOperation('删除照片', `删除了 ${person.name} 的一张人脸照片`);
                
                // 重新加载人员数据以获取最新信息
                await this.loadPersons();
                
                // 刷新详情页面的照片展示
                const detailModal = document.getElementById('personDetailModal');
                if (detailModal) {
                    await this.refreshPersonDetails(personId);
                }
                
                // 刷新主列表显示
                this.displayPersons();
                this.updateStatistics();
            }

        } catch (error) {
            console.error('Delete face error:', error);
            this.showMessage(`删除失败: ${error.message}`, 'error');
        }
    }

    // 显示删除单张照片的确认对话框
    showDeleteFaceConfirmDialog(person, faceIndex) {
        return new Promise((resolve) => {
            // 创建确认对话框
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'deleteFaceConfirmModal';
            modal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg">
                        <div class="modal-header bg-danger text-white border-0">
                            <h5 class="modal-title">
                                <i class="bi bi-exclamation-triangle me-2"></i>确认删除照片
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body p-4">
                            <div class="text-center mb-3">
                                <div class="text-warning mb-2">
                                    <i class="bi bi-image" style="font-size: 2rem;"></i>
                                </div>
                                <h6>删除人脸照片</h6>
                                <p class="text-muted">确定要删除 <strong>${person.name}</strong> 的这张照片吗？</p>
                            </div>
                            
                            <div class="alert alert-warning">
                                <i class="bi bi-info-circle me-2"></i>
                                <small>
                                    删除后该照片将无法恢复，可能会影响识别准确性。
                                    建议保留多张不同角度的照片以提高识别效果。
                                </small>
                            </div>
                        </div>
                        <div class="modal-footer border-0">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="bi bi-x me-1"></i>取消
                            </button>
                            <button type="button" class="btn btn-danger" id="confirmDeleteFace">
                                <i class="bi bi-trash me-1"></i>确认删除
                            </button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            if (window.bootstrap) {
                const bootstrapModal = new bootstrap.Modal(modal);
                bootstrapModal.show();

                // 确认按钮事件
                const confirmBtn = modal.querySelector('#confirmDeleteFace');
                confirmBtn.addEventListener('click', () => {
                    bootstrapModal.hide();
                    resolve(true);
                });

                // 模态框关闭事件
                modal.addEventListener('hidden.bs.modal', () => {
                    document.body.removeChild(modal);
                    resolve(false);
                });
            } else {
                resolve(confirm(`确定要删除 "${person.name}" 的这张照片吗？`));
            }
        });
    }

    // 添加更多照片
    addMoreFaces(personId) {
        const person = this.allPersons.find(p => p.id === personId);
        if (!person) {
            this.showMessage('人员信息不存在', 'error');
            return;
        }

        // 创建上传照片模态框
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'addFacesModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-person-plus-fill me-2"></i>为 ${person.name} 添加人脸照片
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle me-2"></i>
                            <strong>人脸入库说明：</strong>上传的照片将进行人脸识别分析并存储到数据库中，用于后续的人脸识别比对。
                        </div>
                        <div class="upload-area border-2 border-dashed border-primary rounded p-4 text-center mb-3" style="cursor: pointer;" onclick="document.getElementById('addFacesInput').click()">
                            <i class="bi bi-cloud-upload text-primary mb-2" style="font-size: 2rem;"></i>
                            <h6>点击选择或拖拽照片到此处</h6>
                            <p class="text-muted small mb-2">支持 JPG、PNG 格式，单张不超过 5MB</p>
                            <input type="file" class="d-none" id="addFacesInput" multiple accept="image/*">
                        </div>
                        <div id="addFacesPreview" class="d-none">
                            <h6 class="small text-muted mb-2">预览:</h6>
                            <div id="addFacesImages" class="row g-2"></div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" id="uploadFacesBtn" disabled>
                            <i class="bi bi-database-add me-1"></i>开始入库
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        
        if (window.bootstrap) {
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
            
            // 文件选择处理
            const fileInput = modal.querySelector('#addFacesInput');
            const uploadBtn = modal.querySelector('#uploadFacesBtn');
            const uploadArea = modal.querySelector('.upload-area');
            
            fileInput.addEventListener('change', (e) => {
                this.handleAddFacesFiles(e.target.files, modal);
                uploadBtn.disabled = e.target.files.length === 0;
            });

            // 拖拽上传事件
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
                    // 模拟文件输入选择
                    const dt = new DataTransfer();
                    for (let i = 0; i < files.length; i++) {
                        dt.items.add(files[i]);
                    }
                    fileInput.files = dt.files;
                    
                    // 触发change事件
                    this.handleAddFacesFiles(files, modal);
                    uploadBtn.disabled = files.length === 0;
                }
            });

            // 上传按钮事件
            uploadBtn.addEventListener('click', () => {
                this.uploadAdditionalFaces(personId, fileInput.files, modal);
            });
            
            modal.addEventListener('hidden.bs.modal', () => {
                document.body.removeChild(modal);
            });
        }
    }

    // 处理添加照片的文件
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
                                onclick="this.parentElement.parentElement.remove()" title="移除">
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

    // 上传额外的人脸照片
    async uploadAdditionalFaces(personId, files, modal) {
        if (files.length === 0) return;

        const uploadBtn = modal.querySelector('#uploadFacesBtn');
        const originalText = uploadBtn.innerHTML;
        uploadBtn.innerHTML = '<i class="bi bi-spinner bi-spin me-1"></i>入库中...';
        uploadBtn.disabled = true;

        try {
            // 调用真实的API来上传照片
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('faces', files[i]);
            }

            const response = await fetch(`/api/person/${personId}/faces`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`上传失败: HTTP ${response.status}`);
            }

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || '上传失败');
            }

            const person = this.allPersons.find(p => p.id === personId);
            this.showMessage(`成功入库 ${result.count || files.length} 张人脸照片`, 'success');
            this.addRecentOperation('人脸入库', `为 ${person ? person.name : '人员'} 入库了 ${result.count || files.length} 张人脸照片`);

            // 重新加载人员数据以获取最新信息
            await this.loadPersons();
            
            // 刷新详情页面
            const detailModal = document.getElementById('personDetailModal');
            if (detailModal && person) {
                this.refreshPersonDetails(personId);
            }

            // 关闭模态框
            const bootstrapModal = bootstrap.Modal.getInstance(modal);
            if (bootstrapModal) {
                bootstrapModal.hide();
            }

        } catch (error) {
            console.error('Upload additional faces error:', error);
            this.showMessage(`人脸入库失败: ${error.message}`, 'error');
        } finally {
            uploadBtn.innerHTML = originalText;
            uploadBtn.disabled = false;
        }
    }

    // 刷新人员详情页面
    async refreshPersonDetails(personId) {
        const detailModal = document.getElementById('personDetailModal');
        if (!detailModal) return;

        // 重新获取最新的人员数据
        const person = this.allPersons.find(p => p.id === personId);
        if (!person) return;

        // 更新照片区域
        const faceGallery = detailModal.querySelector('.face-gallery');
        if (faceGallery) {
            faceGallery.innerHTML = await this.generateFaceGallery(person);
        }

        // 更新照片数量显示
        const faceCountElements = detailModal.querySelectorAll('.badge');
        faceCountElements.forEach(element => {
            if (element.textContent.includes('张')) {
                element.textContent = `${person.face_count || person.encodings_count || 0} 张`;
            }
        });
        
        // 更新详情页面中的照片数量信息
        const infoCards = detailModal.querySelectorAll('.info-card');
        infoCards.forEach(card => {
            const label = card.querySelector('.info-label');
            if (label && label.textContent.includes('照片数量')) {
                const valueElement = card.querySelector('.info-value .badge');
                if (valueElement) {
                    valueElement.textContent = `${person.face_count || person.encodings_count || 0} 张`;
                }
            }
        });
    }

    // 批量操作相关方法
    enableBulkSelection() {
        this.bulkSelectionMode = true;
        // 刷新显示以显示复选框
        this.displayPersons();
    }

    disableBulkSelection() {
        this.bulkSelectionMode = false;
        this.selectedPersons = new Set();
        // 刷新显示以隐藏复选框
        this.displayPersons();
        this.updateBulkOperationButtons();
    }

    clearAllSelections() {
        this.selectedPersons.clear();
        // 更新所有复选框状态
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
            countElement.textContent = `(已选择 ${selectedCount} 项)`;
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

    // 实现selectAllPersons功能
    selectAllPersons() {
        // 全选当前筛选的人员
        this.filteredPersons.forEach(person => {
            this.selectedPersons.add(person.id);
        });
        
        // 更新所有复选框状态
        this.updateAllCheckboxes();
        this.updateBulkOperationButtons();
    }

    // 更新所有复选框状态
    updateAllCheckboxes() {
        this.filteredPersons.forEach(person => {
            const checkboxes = document.querySelectorAll(`input[data-person-id="${person.id}"]`);
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.selectedPersons.has(person.id);
            });
        });
    }

    // 实现批量删除功能
    async bulkDeletePersons() {
        if (this.selectedPersons.size === 0) {
            this.showMessage('请先选择要删除的人员', 'warning');
            return;
        }

        const selectedPersonsArray = Array.from(this.selectedPersons);
        const selectedPersonsData = selectedPersonsArray.map(id => 
            this.allPersons.find(p => p.id === id)
        ).filter(p => p); // 过滤掉undefined

        // 显示批量删除确认对话框
        const confirmed = await this.showBulkDeleteConfirmDialog(selectedPersonsData);
        if (!confirmed) return;

        // 执行批量删除
        let successCount = 0;
        let failCount = 0;

        for (const person of selectedPersonsData) {
            try {
                // 调用真实API删除人员
                const response = await fetch(`/api/person/${person.id}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        successCount++;
                    } else {
                        throw new Error(data.message || '删除操作失败');
                    }
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (error) {
                failCount++;
                console.error(`删除人员 ${person.name} 失败:`, error);
            }
        }

        // 从本地数据中移除成功删除的人员
        if (successCount > 0) {
            const successfullyDeletedIds = selectedPersonsArray.slice(0, successCount);
            this.allPersons = this.allPersons.filter(p => !successfullyDeletedIds.includes(p.id));
            this.filteredPersons = this.filteredPersons.filter(p => !successfullyDeletedIds.includes(p.id));
        }
        
        // 清空选择
        this.selectedPersons.clear();

        // 显示结果
        if (successCount > 0) {
            this.showMessage(`成功删除 ${successCount} 个人员${failCount > 0 ? `，${failCount} 个失败` : ''}`, successCount === selectedPersonsData.length ? 'success' : 'warning');
            this.addRecentOperation('批量删除', `批量删除了 ${successCount} 个人员`);
        } else {
            this.showMessage('批量删除失败', 'error');
        }

        // 刷新显示
        this.displayPersons();
        this.updateStatistics();
        this.updateBulkOperationButtons();
    }

    // 实现批量导出功能
    async exportSelectedPersons() {
        if (this.selectedPersons.size === 0) {
            this.showMessage('请先选择要导出的人员', 'warning');
            return;
        }

        const selectedPersonsArray = Array.from(this.selectedPersons);
        const selectedPersonsData = selectedPersonsArray.map(id => 
            this.allPersons.find(p => p.id === id)
        ).filter(p => p);

        try {
            // 准备导出数据
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

            // 创建并下载JSON文件
            const jsonString = JSON.stringify(exportData, null, 2);
            const blob = new Blob([jsonString], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `人员数据导出_${new Date().toLocaleDateString('zh-CN').replace(/\//g, '-')}_${selectedPersonsData.length}人.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            URL.revokeObjectURL(url);

            this.showMessage(`成功导出 ${selectedPersonsData.length} 个人员的数据`, 'success');
            this.addRecentOperation('数据导出', `导出了 ${selectedPersonsData.length} 个人员的数据`);

        } catch (error) {
            console.error('Export error:', error);
            this.showMessage(`导出失败: ${error.message}`, 'error');
        }
    }

    // 显示批量删除确认对话框
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
                                <i class="bi bi-exclamation-triangle me-2"></i>确认批量删除
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body p-4">
                            <div class="alert alert-danger">
                                <i class="bi bi-exclamation-triangle me-2"></i>
                                <strong>警告：</strong>您即将删除 <strong>${persons.length}</strong> 个人员的所有信息，包括：
                                <ul class="mt-2 mb-0">
                                    <li>所有人员基本信息</li>
                                    <li>共计 <strong>${totalFaces}</strong> 张人脸照片</li>
                                    <li>相关的识别记录</li>
                                </ul>
                            </div>
                            
                            <div class="mb-3">
                                <h6>将要删除的人员：</h6>
                                <div class="border rounded p-3" style="max-height: 200px; overflow-y: auto;">
                                    ${persons.map(person => `
                                        <div class="d-flex align-items-center mb-2">
                                            <div class="me-2">
                                                ${this.getPersonAvatarSmall(person)}
                                            </div>
                                            <div>
                                                <div class="fw-medium">${person.name}</div>
                                                <small class="text-muted">ID: ${person.id} | ${person.face_count || person.encodings_count || 0} 张照片</small>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                            
                            <div class="alert alert-warning">
                                <i class="bi bi-info-circle me-2"></i>
                                <strong>注意：</strong>此操作不可撤销，请确认后再继续。
                            </div>
                        </div>
                        <div class="modal-footer border-0">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="bi bi-x me-1"></i>取消
                            </button>
                            <button type="button" class="btn btn-danger" id="confirmBulkDelete">
                                <i class="bi bi-trash me-1"></i>确认删除 ${persons.length} 个人员
                            </button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            if (window.bootstrap) {
                const bootstrapModal = new bootstrap.Modal(modal);
                bootstrapModal.show();

                // 确认按钮事件
                const confirmBtn = modal.querySelector('#confirmBulkDelete');
                confirmBtn.addEventListener('click', () => {
                    bootstrapModal.hide();
                    resolve(true);
                });

                // 模态框关闭事件
                modal.addEventListener('hidden.bs.modal', () => {
                    document.body.removeChild(modal);
                    resolve(false);
                });
            } else {
                resolve(confirm(`确定要删除这 ${persons.length} 个人员吗？`));
            }
        });
    }

    async deletePerson(personId) {
        const person = this.allPersons.find(p => p.id === personId);
        if (!person) {
            this.showMessage('人员信息不存在', 'error');
            return;
        }

        // 创建优雅的确认对话框
        const result = await this.showDeleteConfirmDialog(person);
        if (!result) return;

        try {
            // 调用真实API删除人员
            const response = await fetch(`/api/person/${personId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // 从本地数据中移除
                    this.allPersons = this.allPersons.filter(p => p.id !== personId);
                    this.filteredPersons = this.filteredPersons.filter(p => p.id !== personId);
                    this.selectedPersons.delete(personId);
                    
                    this.showMessage(`人员 "${person.name}" 已成功删除`, 'success');
                    this.displayPersons();
                    this.updateStatistics();
                    this.updateBulkOperationButtons();
                    this.addRecentOperation('删除人员', `删除了人员: ${person.name}`);
                } else {
                    throw new Error(data.message || '删除操作失败');
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }

        } catch (error) {
            console.error('Delete person error:', error);
            this.showMessage(`删除失败: ${error.message}`, 'error');
        }
    }

    showDeleteConfirmDialog(person) {
        return new Promise((resolve) => {
            // 移除已存在的确认对话框
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
                                <i class="bi bi-exclamation-triangle-fill me-2"></i>确认删除
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
                                <strong>此操作无法撤销！</strong>
                            </div>
                            
                            <p class="text-center mb-4">
                                您确定要删除人员 <strong class="text-danger">"${person.name}"</strong> 吗？
                            </p>
                            
                            <div class="bg-light rounded p-3 mb-3">
                                <h6 class="text-muted mb-2">将被删除的数据：</h6>
                                <ul class="list-unstyled mb-0 small">
                                    <li><i class="bi bi-person text-primary me-2"></i>人员基本信息</li>
                                    <li><i class="bi bi-images text-success me-2"></i>${person.face_count || person.encodings_count || 0} 张人脸照片</li>
                                    <li><i class="bi bi-clock-history text-info me-2"></i>所有相关识别记录</li>
                                </ul>
                            </div>
                        </div>
                        <div class="modal-footer border-0 bg-light">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="bi bi-x-lg me-1"></i>取消
                            </button>
                            <button type="button" class="btn btn-danger" id="confirmDeleteBtn">
                                <i class="bi bi-trash me-1"></i>确认删除
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
            this.showMessage('请先选择要删除的人员', 'warning');
            return;
        }

        const selectedCount = this.selectedPersons.size;
        if (!confirm(`确定要删除选中的 ${selectedCount} 个人员吗？此操作不可恢复。`)) {
            return;
        }

        try {
            const selectedIds = Array.from(this.selectedPersons);
            let successCount = 0;

            for (const personId of selectedIds) {
                try {
                    // 调用真实API删除人员
                    const response = await fetch(`/api/person/${personId}`, {
                        method: 'DELETE'
                    });
                    if (response.ok) {
                        const data = await response.json();
                        if (data.success) {
                            successCount++;
                        }
                    }
                } catch (apiError) {
                    console.error(`删除人员 ${personId} 失败:`, apiError);
                }
            }

            // 从本地数据中移除
            this.allPersons = this.allPersons.filter(p => !this.selectedPersons.has(p.id));
            this.filteredPersons = this.filteredPersons.filter(p => !this.selectedPersons.has(p.id));
            this.selectedPersons.clear();

            this.showMessage(`成功删除 ${successCount} 个人员`, 'success');
            this.displayPersons();
            this.updateStatistics();
            this.updateBulkOperationButtons();
            this.addRecentOperation('批量删除', `批量删除了 ${successCount} 个人员`);

        } catch (error) {
            console.error('Bulk delete error:', error);
            this.showMessage(`批量删除失败: ${error.message}`, 'error');
        }
    }

    async exportSelectedPersons() {
        if (this.selectedPersons.size === 0) {
            this.showMessage('请先选择要导出的人员', 'warning');
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

            this.showMessage(`成功导出 ${selectedPersons.length} 个人员数据`, 'success');

        } catch (error) {
            console.error('Export persons error:', error);
            this.showMessage(`导出失败: ${error.message}`, 'error');
        }
    }

    editPersonModal(personId) {
        const person = this.allPersons.find(p => p.id === personId);
        if (!person) {
            this.showMessage('人员信息不存在', 'error');
            return;
        }

        // 移除已存在的编辑模态框
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
                            <i class="bi bi-pencil-square me-2"></i>编辑人员信息
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
                                    <i class="bi bi-person me-1"></i>姓名 <span class="text-danger">*</span>
                                </label>
                                <input type="text" class="form-control" id="editPersonName" 
                                       value="${person.name}" required maxlength="100">
                            </div>
                            
                            <div class="mb-3">
                                <label for="editPersonDesc" class="form-label">
                                    <i class="bi bi-card-text me-1"></i>描述
                                </label>
                                <textarea class="form-control" id="editPersonDesc" rows="3" 
                                          maxlength="500" placeholder="输入人员描述...">${person.description || ''}</textarea>
                                <div class="form-text">最多500个字符</div>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">
                                    <i class="bi bi-info-circle me-1"></i>基本信息
                                </label>
                                <div class="bg-light rounded p-3">
                                    <div class="row">
                                        <div class="col-6">
                                            <small class="text-muted">人员ID:</small><br>
                                            <strong>${person.id}</strong>
                                        </div>
                                        <div class="col-6">
                                            <small class="text-muted">照片数:</small><br>
                                            <strong>${person.face_count || person.encodings_count || 0} 张</strong>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer border-0">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="window.personManagement.savePersonEdit(${person.id})">
                            <i class="bi bi-check-lg me-1"></i>保存更改
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
            this.showMessage('表单元素不存在', 'error');
            return;
        }

        const newName = nameInput.value.trim();
        const newDesc = descInput.value.trim();

        if (!newName) {
            this.showMessage('姓名不能为空', 'warning');
            nameInput.focus();
            return;
        }

        try {
            // 调用真实API更新人员信息
            const response = await fetch(`/api/person/${personId}`, {
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
                    // 更新本地数据
                    const person = this.allPersons.find(p => p.id === personId);
                    if (person) {
                        const oldName = person.name;
                        person.name = newName;
                        person.description = newDesc;
                        
                        this.displayPersons();
                        this.showMessage('人员信息已更新', 'success');
                        this.addRecentOperation('编辑人员', `将 "${oldName}" 的信息更新为 "${newName}"`);
                        
                        // 关闭模态框
                        const modal = bootstrap.Modal.getInstance(document.getElementById('editPersonModal'));
                        if (modal) {
                            modal.hide();
                        }
                    }
                } else {
                    throw new Error(data.message || '更新失败');
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
            
        } catch (error) {
            console.error('Save person edit error:', error);
            this.showMessage(`更新失败: ${error.message}`, 'error');
        }
    }

    async deletePersonConfirm(personId) {
        const person = this.allPersons.find(p => p.id === personId);
        if (!person) {
            this.showMessage('人员信息不存在', 'error');
            return;
        }

        // 关闭详情模态框
        const detailModal = bootstrap.Modal.getInstance(document.getElementById('personDetailModal'));
        if (detailModal) {
            detailModal.hide();
        }

        // 延迟显示优雅的确认对话框
        setTimeout(async () => {
            const confirmed = await this.showDeleteConfirmDialog(person);
            if (confirmed) {
                this.deletePerson(personId);
            }
        }, 300);
    }

    showMessage(message, type = 'info') {
        // 显示消息通知
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

    showLoading(show) {
        const container = document.getElementById('personsList');
        if (!container) return;

        if (show) {
            container.innerHTML = `
                <div class="d-flex justify-content-center p-5">
                    <div class="text-center">
                        <div class="spinner-border text-primary mb-3" role="status">
                            <span class="visually-hidden">加载中...</span>
                        </div>
                        <p class="text-muted">正在加载人员数据...</p>
                    </div>
                </div>
            `;
        }
    }

    displayError(message) {
        const container = document.getElementById('personsList');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    <strong>加载失败</strong>
                    <br><small>${message}</small>
                    <div class="mt-2">
                        <button class="btn btn-sm btn-outline-danger" onclick="personManagement.loadPersons()">
                            重试
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

    // 最近操作相关方法
    addRecentOperation(action, details) {
        const operation = {
            id: Date.now(),
            action: action,
            details: details,
            timestamp: new Date().toISOString()
        };
        
        // 添加到最近操作列表前面
        this.recentOperations.unshift(operation);
        
        // 只保留最近20条操作记录
        if (this.recentOperations.length > 20) {
            this.recentOperations = this.recentOperations.slice(0, 20);
        }
        
        // 保存到localStorage
        localStorage.setItem('recentOperations', JSON.stringify(this.recentOperations));
        
        // 更新显示
        this.updateRecentOperations();
    }

    updateRecentOperations() {
        const container = document.getElementById('recentOperations');
        if (!container) return;
        
        if (this.recentOperations.length === 0) {
            container.innerHTML = '<small class="text-muted">暂无操作记录</small>';
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
                        查看全部 ${this.recentOperations.length} 条记录
                    </button>
                </div>
            `;
        }
    }

    getOperationIcon(action) {
        const icons = {
            '删除人员': 'trash',
            '编辑人员': 'pencil',
            '添加人员': 'person-plus',
            '批量删除': 'trash-fill',
            '导出数据': 'download',
            '刷新数据': 'arrow-clockwise'
        };
        return icons[action] || 'info-circle';
    }

    formatTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffMinutes = Math.floor((now - time) / (1000 * 60));
        
        if (diffMinutes < 1) return '刚刚';
        if (diffMinutes < 60) return `${diffMinutes}分钟前`;
        
        const diffHours = Math.floor(diffMinutes / 60);
        if (diffHours < 24) return `${diffHours}小时前`;
        
        const diffDays = Math.floor(diffHours / 24);
        if (diffDays < 7) return `${diffDays}天前`;
        
        return time.toLocaleDateString('zh-CN');
    }

    showAllOperations() {
        // 创建完整操作记录对话框
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
                            <i class="bi bi-clock-history me-2"></i>操作历史记录
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
                            <i class="bi bi-trash me-1"></i>清空记录
                        </button>
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
        }
    }

    clearOperationHistory() {
        if (confirm('确定要清空所有操作记录吗？')) {
            this.recentOperations = [];
            localStorage.removeItem('recentOperations');
            this.updateRecentOperations();
            this.showMessage('操作记录已清空', 'success');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('operationsHistoryModal'));
            if (modal) {
                modal.hide();
            }
        }
    }

    // 批量人脸入库功能
    showBatchFaceEnrollmentModal() {
        // 移除已存在的模态框
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
                            <i class="bi bi-person-plus-fill me-2"></i>批量人脸入库
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-4">
                        <div class="alert alert-info border-0">
                            <i class="bi bi-info-circle me-2"></i>
                            <strong>批量人脸入库说明：</strong><br>
                            • 支持上传多张人脸照片，系统会自动识别人脸并入库<br>
                            • 可以为现有人员添加更多人脸照片，或创建新人员<br>
                            • 支持从文件名自动提取人员姓名<br>
                            • 每张照片最大5MB，支持JPG、PNG格式
                        </div>

                        <div class="mb-4">
                            <label class="form-label fw-bold">
                                <i class="bi bi-upload me-1"></i>选择人脸照片
                            </label>
                            <div class="upload-area border-2 border-dashed border-primary rounded p-4 text-center mb-3" 
                                 id="batchUploadArea" onclick="document.getElementById('batchFaceFiles').click()">
                                <i class="bi bi-cloud-upload text-primary mb-2" style="font-size: 3rem;"></i>
                                <h6 class="text-primary">点击选择或拖拽照片到此处</h6>
                                <p class="text-muted small mb-0">支持多选，系统将从文件名自动提取人员姓名</p>
                                <input type="file" class="d-none" id="batchFaceFiles" multiple accept="image/*">
                            </div>
                            
                            <div id="batchFacePreview" class="d-none">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <h6 class="small text-muted mb-0">预览 (<span id="previewCount">0</span> 张照片)：</h6>
                                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="this.parentElement.parentElement.parentElement.querySelector('#batchFaceFiles').click()">
                                        <i class="bi bi-plus me-1"></i>添加更多
                                    </button>
                                </div>
                                <div id="batchFaceImages" class="row g-2" style="max-height: 300px; overflow-y: auto;"></div>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-6">
                                <label class="form-label">
                                    <i class="bi bi-gear me-1"></i>入库模式
                                </label>
                                <div class="form-check">
                                    <input class="form-check-input" type="radio" name="enrollmentMode" id="autoMode" value="auto" checked>
                                    <label class="form-check-label" for="autoMode">
                                        <strong>自动模式</strong><br>
                                        <small class="text-muted">从文件名自动提取姓名</small>
                                    </label>
                                </div>
                                <div class="form-check mt-2">
                                    <input class="form-check-input" type="radio" name="enrollmentMode" id="manualMode" value="manual">
                                    <label class="form-check-label" for="manualMode">
                                        <strong>手动模式</strong><br>
                                        <small class="text-muted">手动指定人员信息</small>
                                    </label>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div id="manualModeOptions" class="d-none">
                                    <label for="batchPersonName" class="form-label">
                                        <i class="bi bi-person me-1"></i>统一姓名（可选）
                                    </label>
                                    <input type="text" class="form-control mb-2" id="batchPersonName" 
                                           placeholder="留空则使用文件名">
                                    
                                    <label for="batchPersonDesc" class="form-label">
                                        <i class="bi bi-card-text me-1"></i>统一描述（可选）
                                    </label>
                                    <input type="text" class="form-control" id="batchPersonDesc" 
                                           placeholder="为所有照片添加统一描述">
                                </div>
                                <div id="autoModeInfo" class="">
                                    <div class="alert alert-light border mb-0">
                                        <small class="text-muted">
                                            <i class="bi bi-lightbulb me-1"></i>
                                            <strong>文件命名建议：</strong><br>
                                            • 张三.jpg → 姓名：张三<br>
                                            • John_Smith.png → 姓名：John Smith<br>
                                            • 员工001.jpg → 姓名：员工001
                                        </small>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="batchResults" class="mt-3 d-none">
                            <h6 class="text-muted mb-2">
                                <i class="bi bi-list-check me-1"></i>入库结果：
                            </h6>
                            <div id="batchResultsContent"></div>
                        </div>
                    </div>
                    <div class="modal-footer border-0">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="bi bi-x me-1"></i>关闭
                        </button>
                        <button type="button" class="btn btn-primary" id="startBatchEnrollment" disabled>
                            <i class="bi bi-database-add me-1"></i>开始批量入库
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        if (window.bootstrap) {
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();

            // 绑定事件
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

        // 文件选择事件
        fileInput.addEventListener('change', (e) => {
            this.handleBatchFaceFiles(e.target.files, modal);
        });

        // 拖拽上传
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

        // 模式切换
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

        // 开始批量入库
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

        // 保存文件到模态框数据中
        modal._batchFiles = Array.from(files);
        countSpan.textContent = files.length;

        container.innerHTML = '';

        Array.from(files).forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const col = document.createElement('div');
                col.className = 'col-3 mb-2';
                
                // 从文件名提取可能的姓名
                const fileName = file.name;
                const nameFromFile = fileName.replace(/\.(jpg|jpeg|png|gif|bmp|webp)$/i, '')
                                             .replace(/[_-]/g, ' ')
                                             .trim() || '未命名';

                col.innerHTML = `
                    <div class="position-relative">
                        <img src="${e.target.result}" class="img-fluid rounded border" 
                             style="height: 80px; object-fit: cover; width: 100%;" 
                             alt="${fileName}">
                        <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 m-1" 
                                onclick="this.closest('.col-3').remove(); window.personManagement.updateBatchFileCount()" 
                                title="移除">
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
            this.showMessage('请先选择人脸照片', 'warning');
            return;
        }

        const startBtn = modal.querySelector('#startBatchEnrollment');
        const results = modal.querySelector('#batchResults');
        const resultsContent = modal.querySelector('#batchResultsContent');
        const autoMode = modal.querySelector('#autoMode').checked;
        const manualName = modal.querySelector('#batchPersonName').value.trim();
        const manualDesc = modal.querySelector('#batchPersonDesc').value.trim();

        const originalBtnText = startBtn.innerHTML;
        startBtn.innerHTML = '<i class="bi bi-spinner bi-spin me-1"></i>批量入库中...';
        startBtn.disabled = true;

        try {
            const formData = new FormData();
            
            // 添加文件
            files.forEach(file => {
                formData.append('files', file);
            });

            // 如果是手动模式且指定了姓名，添加姓名参数
            if (!autoMode && manualName) {
                formData.append('names', manualName);
            }

            // 如果指定了描述，添加描述参数
            if (manualDesc) {
                formData.append('descriptions', manualDesc);
            }

            const response = await fetch('/api/batch_enroll', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            // 显示结果
            this.displayBatchEnrollmentResults(result, resultsContent);
            results.classList.remove('d-none');

            if (result.success && result.success_count > 0) {
                this.showMessage(`批量入库完成：成功 ${result.success_count} 个，失败 ${result.error_count} 个`, 
                    result.error_count === 0 ? 'success' : 'warning');
                this.addRecentOperation('批量人脸入库', `批量入库了 ${result.success_count} 张人脸照片`);
                
                // 刷新人员列表
                await this.loadPersons();
            } else {
                this.showMessage('批量入库失败', 'error');
            }

        } catch (error) {
            console.error('Batch face enrollment error:', error);
            this.showMessage(`批量入库失败: ${error.message}`, 'error');
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
                    <strong>批量入库完成</strong>
                </div>
                <div class="row text-center">
                    <div class="col-4">
                        <div class="fs-4 fw-bold">${result.total_files || 0}</div>
                        <small class="text-muted">总计</small>
                    </div>
                    <div class="col-4">
                        <div class="fs-4 fw-bold text-success">${result.success_count || 0}</div>
                        <small class="text-muted">成功</small>
                    </div>
                    <div class="col-4">
                        <div class="fs-4 fw-bold text-danger">${result.error_count || 0}</div>
                        <small class="text-muted">失败</small>
                    </div>
                </div>
            </div>
        `;

        if (result.results && result.results.length > 0) {
            html += '<div class="mt-3"><h6 class="small text-muted mb-2">详细结果：</h6>';
            
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
                                        ${item.name ? `姓名: ${item.name}` : ''}
                                        ${item.success ? 
                                            `${item.person_id ? ` | ID: ${item.person_id}` : ''}${item.quality_score ? ` | 质量: ${(item.quality_score * 100).toFixed(1)}%` : ''}` :
                                            ` | 错误: ${item.error}`
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

// 全局函数
function showBulkOperations() {
    const panel = document.getElementById('bulkOperationsPanel');
    if (panel) {
        const isVisible = panel.style.display !== 'none';
        panel.style.display = isVisible ? 'none' : 'block';
        
        if (window.personManagement) {
            window.personManagement.showMessage(
                isVisible ? '批量操作面板已隐藏' : '批量操作面板已显示', 
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
        
        // 更新所有复选框状态
        window.personManagement.filteredPersons.forEach(person => {
            const checkbox1 = document.getElementById(`person_${person.id}`);
            const checkbox2 = document.getElementById(`person_list_${person.id}`);
            if (checkbox1) checkbox1.checked = true;
            if (checkbox2) checkbox2.checked = true;
        });
        
        window.personManagement.updateBulkOperationButtons();
        window.personManagement.showMessage(`已选择 ${window.personManagement.selectedPersons.size} 个人员`, 'info');
    }
}

function clearSelection() {
    if (window.personManagement) {
        window.personManagement.selectedPersons.clear();
        
        // 清除所有复选框状态
        document.querySelectorAll('input[type="checkbox"][data-person-id]').forEach(cb => {
            cb.checked = false;
        });
        
        const selectAllCheckbox = document.getElementById('selectAll');
        if (selectAllCheckbox) selectAllCheckbox.checked = false;
        
        window.personManagement.updateBulkOperationButtons();
        window.personManagement.showMessage('已清除所有选择', 'info');
    }
}

function bulkDeletePersons() {
    if (window.personManagement) {
        window.personManagement.bulkDeletePersons();
    } else {
        alert('人员管理模块未加载');
    }
}

function exportSelectedPersons() {
    if (window.personManagement) {
        window.personManagement.exportSelectedPersons();
    } else {
        alert('人员管理模块未加载');
    }
}

// 批量人脸入库功能
function showBatchFaceEnrollment() {
    if (window.personManagement) {
        window.personManagement.showBatchFaceEnrollmentModal();
    } else {
        alert('人员管理模块未加载');
    }
}

// 导出到全局作用域
window.PersonManagement = PersonManagement;

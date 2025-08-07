/**
 * 人员管理模块
 * @description 处理人员管理相关的所有功能
 */

import { eventManager, APP_EVENTS } from '../services/event-manager.js';
import { faceRecognitionService } from '../services/face-recognition-api.js';
import { showToast, showLoader, hideLoader, Modal } from '../utils/ui-components.js';
import { $, formatDate, debounce } from '../utils/helpers.js';
import { CONFIG } from '../config.js';

/**
 * 人员管理模块类
 */
class ManagementModule {
  constructor() {
    this.persons = [];
    this.filteredPersons = [];
    this.currentPage = 1;
    this.pageSize = 10;
    this.viewMode = 'list'; // 'list' or 'card'
    this.searchQuery = '';
    this.sortBy = 'name_asc';
    this.filterBy = 'all';
    this.selectedPersons = new Set();
    this.isLoading = false;
    
    this.init();
  }

  /**
   * 初始化模块
   */
  init() {
    console.log('👥 初始化人员管理模块...');
    
    this._setupElements();
    this._setupEventListeners();
    
    console.log('✅ 人员管理模块初始化完成');
  }

  /**
   * 设置DOM元素引用
   * @private
   */
  _setupElements() {
    this.elements = {
      searchInput: $('#searchPersons'),
      sortSelect: $('#sortPersons'),
      filterSelect: $('#filterPersons'),
      listViewBtn: $('#listViewBtn'),
      cardViewBtn: $('#cardViewBtn'),
      listView: $('#listView'),
      cardView: $('#cardView'),
      tableBody: $('#personsTableBody'),
      cardContainer: $('#personsCardContainer'),
      selectAll: $('#selectAll'),
      batchOperations: $('#batchOperations'),
      selectedCount: $('#selectedCount'),
      totalCount: $('#totalPersonsCount'),
      currentPageInfo: $('#currentPageInfo'),
      pagination: $('#pagination')
    };
  }

  /**
   * 设置事件监听器
   * @private
   */
  _setupEventListeners() {
    // 搜索输入
    if (this.elements.searchInput) {
      this.elements.searchInput.addEventListener('input', 
        debounce((e) => this.handleSearch(e.target.value), 300)
      );
    }

    // 排序选择
    if (this.elements.sortSelect) {
      this.elements.sortSelect.addEventListener('change', (e) => {
        this.handleSort(e.target.value);
      });
    }

    // 筛选选择
    if (this.elements.filterSelect) {
      this.elements.filterSelect.addEventListener('change', (e) => {
        this.handleFilter(e.target.value);
      });
    }

    // 视图切换
    if (this.elements.listViewBtn) {
      this.elements.listViewBtn.addEventListener('click', () => {
        this.switchView('list');
      });
    }

    if (this.elements.cardViewBtn) {
      this.elements.cardViewBtn.addEventListener('click', () => {
        this.switchView('card');
      });
    }

    // 全选
    if (this.elements.selectAll) {
      this.elements.selectAll.addEventListener('change', (e) => {
        this.toggleSelectAll(e.target.checked);
      });
    }

    // Tab切换事件
    eventManager.on(APP_EVENTS.TAB_CHANGE, (data) => {
      if (data.tab === 'management') {
        this._onTabActivated();
      }
    });

    // 监听入库成功事件，刷新人员列表
    eventManager.on(APP_EVENTS.ENROLLMENT_SUCCESS, () => {
      this.loadPersons();
    });
  }

  /**
   * Tab激活时的处理
   * @private
   */
  async _onTabActivated() {
    console.log('人员管理Tab已激活');
    if (this.persons.length === 0) {
      await this.loadPersons();
    }
  }

  /**
   * 加载人员列表
   */
  async loadPersons() {
    if (this.isLoading) return;

    try {
      this.isLoading = true;
      this._showLoading();

      console.log('📊 加载人员列表...');
      const response = await faceRecognitionService.getPersons();
      
      this.persons = response.persons || response || [];
      this._applyFiltersAndSort();
      this._updateDisplay();
      
      console.log(`✅ 加载了 ${this.persons.length} 个人员`);
      
    } catch (error) {
      console.error('❌ 加载人员列表失败:', error);
      this._showError('加载人员列表失败: ' + (error.message || '未知错误'));
      showToast('加载失败', '无法加载人员列表', 'error');
    } finally {
      this.isLoading = false;
      this._hideLoading();
    }
  }

  /**
   * 搜索人员
   */
  handleSearch(query) {
    this.searchQuery = query.toLowerCase();
    this.currentPage = 1;
    this._applyFiltersAndSort();
    this._updateDisplay();
  }

  /**
   * 排序人员
   */
  handleSort(sortBy) {
    this.sortBy = sortBy;
    this._applyFiltersAndSort();
    this._updateDisplay();
  }

  /**
   * 筛选人员
   */
  handleFilter(filterBy) {
    this.filterBy = filterBy;
    this.currentPage = 1;
    this._applyFiltersAndSort();
    this._updateDisplay();
  }

  /**
   * 切换视图模式
   */
  switchView(mode) {
    this.viewMode = mode;
    this._updateViewMode();
    this._updateDisplay();
  }

  /**
   * 应用筛选和排序
   * @private
   */
  _applyFiltersAndSort() {
    let filtered = [...this.persons];

    // 应用搜索
    if (this.searchQuery) {
      filtered = filtered.filter(person => 
        person.name.toLowerCase().includes(this.searchQuery) ||
        (person.description && person.description.toLowerCase().includes(this.searchQuery))
      );
    }

    // 应用筛选
    switch (this.filterBy) {
      case 'with_faces':
        filtered = filtered.filter(person => person.face_count > 0);
        break;
      case 'no_faces':
        filtered = filtered.filter(person => person.face_count === 0);
        break;
      case 'recent':
        const oneWeekAgo = new Date();
        oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
        filtered = filtered.filter(person => 
          new Date(person.created_at) > oneWeekAgo
        );
        break;
    }

    // 应用排序
    filtered.sort((a, b) => {
      switch (this.sortBy) {
        case 'name_asc':
          return a.name.localeCompare(b.name);
        case 'name_desc':
          return b.name.localeCompare(a.name);
        case 'date_desc':
          return new Date(b.created_at) - new Date(a.created_at);
        case 'date_asc':
          return new Date(a.created_at) - new Date(b.created_at);
        case 'faces_desc':
          return b.face_count - a.face_count;
        case 'faces_asc':
          return a.face_count - b.face_count;
        default:
          return 0;
      }
    });

    this.filteredPersons = filtered;
  }

  /**
   * 更新视图模式
   * @private
   */
  _updateViewMode() {
    if (this.elements.listView && this.elements.cardView) {
      if (this.viewMode === 'list') {
        this.elements.listView.style.display = 'block';
        this.elements.cardView.style.display = 'none';
        this.elements.listViewBtn?.classList.add('active');
        this.elements.cardViewBtn?.classList.remove('active');
      } else {
        this.elements.listView.style.display = 'none';
        this.elements.cardView.style.display = 'block';
        this.elements.listViewBtn?.classList.remove('active');
        this.elements.cardViewBtn?.classList.add('active');
      }
    }
  }

  /**
   * 更新显示
   * @private
   */
  _updateDisplay() {
    this._updateStats();
    this._updatePagination();
    
    if (this.viewMode === 'list') {
      this._updateListView();
    } else {
      this._updateCardView();
    }
    
    this._updateBatchOperations();
  }

  /**
   * 更新统计信息
   * @private
   */
  _updateStats() {
    if (this.elements.totalCount) {
      this.elements.totalCount.textContent = this.filteredPersons.length;
    }
    
    if (this.elements.currentPageInfo) {
      const start = (this.currentPage - 1) * this.pageSize + 1;
      const end = Math.min(this.currentPage * this.pageSize, this.filteredPersons.length);
      this.elements.currentPageInfo.textContent = 
        this.filteredPersons.length > 0 ? `${start}-${end}` : '0';
    }
  }

  /**
   * 更新列表视图
   * @private
   */
  _updateListView() {
    if (!this.elements.tableBody) return;

    if (this.filteredPersons.length === 0) {
      this.elements.tableBody.innerHTML = `
        <tr>
          <td colspan="7" class="text-center text-muted py-4">
            <i class="bi bi-people fs-1 d-block mb-2"></i>
            ${this.searchQuery ? '没有找到匹配的人员' : '暂无人员数据'}
          </td>
        </tr>
      `;
      return;
    }

    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    const pagePersons = this.filteredPersons.slice(start, end);

    const rows = pagePersons.map(person => `
      <tr>
        <td>
          <input type="checkbox" class="person-checkbox" 
                 value="${person.id}" ${this.selectedPersons.has(person.id) ? 'checked' : ''}>
        </td>
        <td>${person.id}</td>
        <td>
          <strong>${person.name}</strong>
          ${person.face_count > 0 ? '<i class="bi bi-camera-fill text-success ms-1"></i>' : ''}
        </td>
        <td>
          <span class="text-muted">${person.description || '-'}</span>
        </td>
        <td>
          <span class="badge bg-${person.face_count > 0 ? 'success' : 'secondary'}">
            ${person.face_count}
          </span>
        </td>
        <td>
          <small class="text-muted">${formatDate(person.created_at)}</small>
        </td>
        <td>
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-primary" onclick="managementModule.viewPerson(${person.id})" 
                    title="查看详情">
              <i class="bi bi-eye"></i>
            </button>
            <button class="btn btn-outline-danger" onclick="managementModule.deletePerson(${person.id})" 
                    title="删除">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `).join('');

    this.elements.tableBody.innerHTML = rows;

    // 重新绑定checkbox事件
    this._bindCheckboxEvents();
  }

  /**
   * 更新卡片视图
   * @private
   */
  _updateCardView() {
    if (!this.elements.cardContainer) return;

    if (this.filteredPersons.length === 0) {
      this.elements.cardContainer.innerHTML = `
        <div class="col-12 text-center text-muted py-5">
          <i class="bi bi-people fs-1 d-block mb-3"></i>
          <h5>${this.searchQuery ? '没有找到匹配的人员' : '暂无人员数据'}</h5>
        </div>
      `;
      return;
    }

    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    const pagePersons = this.filteredPersons.slice(start, end);

    const cards = pagePersons.map(person => `
      <div class="col-md-4 col-lg-3 mb-4">
        <div class="card h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <h6 class="card-title mb-0">${person.name}</h6>
              <input type="checkbox" class="person-checkbox" 
                     value="${person.id}" ${this.selectedPersons.has(person.id) ? 'checked' : ''}>
            </div>
            <p class="card-text text-muted small">
              ${person.description || '无描述'}
            </p>
            <div class="d-flex justify-content-between align-items-center">
              <span class="badge bg-${person.face_count > 0 ? 'success' : 'secondary'}">
                ${person.face_count} 张人脸
              </span>
              <small class="text-muted">${formatDate(person.created_at)}</small>
            </div>
          </div>
          <div class="card-footer bg-transparent">
            <div class="btn-group w-100">
              <button class="btn btn-outline-primary btn-sm" 
                      onclick="managementModule.viewPerson(${person.id})">
                <i class="bi bi-eye me-1"></i>查看
              </button>
              <button class="btn btn-outline-danger btn-sm" 
                      onclick="managementModule.deletePerson(${person.id})">
                <i class="bi bi-trash me-1"></i>删除
              </button>
            </div>
          </div>
        </div>
      </div>
    `).join('');

    this.elements.cardContainer.innerHTML = cards;

    // 重新绑定checkbox事件
    this._bindCheckboxEvents();
  }

  /**
   * 绑定checkbox事件
   * @private
   */
  _bindCheckboxEvents() {
    const checkboxes = document.querySelectorAll('.person-checkbox');
    checkboxes.forEach(checkbox => {
      checkbox.addEventListener('change', (e) => {
        const personId = parseInt(e.target.value);
        if (e.target.checked) {
          this.selectedPersons.add(personId);
        } else {
          this.selectedPersons.delete(personId);
        }
        this._updateBatchOperations();
        this._updateSelectAllState();
      });
    });
  }

  /**
   * 更新分页
   * @private
   */
  _updatePagination() {
    if (!this.elements.pagination) return;

    const totalPages = Math.ceil(this.filteredPersons.length / this.pageSize);
    
    if (totalPages <= 1) {
      this.elements.pagination.innerHTML = '';
      return;
    }

    let html = '';
    
    // 上一页
    html += `
      <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="managementModule.goToPage(${this.currentPage - 1})">
          <i class="bi bi-chevron-left"></i>
        </a>
      </li>
    `;
    
    // 页码
    for (let i = 1; i <= totalPages; i++) {
      if (i === 1 || i === totalPages || (i >= this.currentPage - 2 && i <= this.currentPage + 2)) {
        html += `
          <li class="page-item ${i === this.currentPage ? 'active' : ''}">
            <a class="page-link" href="#" onclick="managementModule.goToPage(${i})">${i}</a>
          </li>
        `;
      } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
        html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
      }
    }
    
    // 下一页
    html += `
      <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="managementModule.goToPage(${this.currentPage + 1})">
          <i class="bi bi-chevron-right"></i>
        </a>
      </li>
    `;
    
    this.elements.pagination.innerHTML = html;
  }

  /**
   * 跳转到指定页面
   */
  goToPage(page) {
    const totalPages = Math.ceil(this.filteredPersons.length / this.pageSize);
    if (page >= 1 && page <= totalPages) {
      this.currentPage = page;
      this._updateDisplay();
    }
  }

  /**
   * 切换全选
   */
  toggleSelectAll(checked) {
    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    const pagePersons = this.filteredPersons.slice(start, end);
    
    pagePersons.forEach(person => {
      if (checked) {
        this.selectedPersons.add(person.id);
      } else {
        this.selectedPersons.delete(person.id);
      }
    });
    
    this._updateDisplay();
  }

  /**
   * 更新全选状态
   * @private
   */
  _updateSelectAllState() {
    if (!this.elements.selectAll) return;

    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    const pagePersons = this.filteredPersons.slice(start, end);
    
    const selectedInPage = pagePersons.filter(p => this.selectedPersons.has(p.id)).length;
    
    if (selectedInPage === 0) {
      this.elements.selectAll.checked = false;
      this.elements.selectAll.indeterminate = false;
    } else if (selectedInPage === pagePersons.length) {
      this.elements.selectAll.checked = true;
      this.elements.selectAll.indeterminate = false;
    } else {
      this.elements.selectAll.checked = false;
      this.elements.selectAll.indeterminate = true;
    }
  }

  /**
   * 更新批量操作
   * @private
   */
  _updateBatchOperations() {
    if (this.elements.batchOperations && this.elements.selectedCount) {
      const hasSelection = this.selectedPersons.size > 0;
      this.elements.batchOperations.style.display = hasSelection ? 'block' : 'none';
      this.elements.selectedCount.textContent = this.selectedPersons.size;
    }
  }

  /**
   * 查看人员详情
   */
  async viewPerson(personId) {
    try {
      showLoader('加载人员详情...');
      
      const person = await faceRecognitionService.getPerson(personId);
      this._showPersonDetail(person);
      
    } catch (error) {
      console.error('查看人员详情失败:', error);
      showToast('加载失败', '无法加载人员详情', 'error');
    } finally {
      hideLoader();
    }
  }

  /**
   * 删除人员
   */
  async deletePerson(personId) {
    const person = this.persons.find(p => p.id === personId);
    const confirmed = await Modal.confirm(
      '确认删除',
      `确定要删除人员 "${person?.name || personId}" 吗？此操作无法撤销。`
    );
    
    if (!confirmed) return;

    try {
      showLoader('删除中...');
      
      await faceRecognitionService.deletePerson(personId);
      
      showToast('删除成功', '人员已删除', 'success');
      
      // 重新加载列表
      await this.loadPersons();
      
    } catch (error) {
      console.error('删除人员失败:', error);
      showToast('删除失败', error.message || '删除人员时发生错误', 'error');
    } finally {
      hideLoader();
    }
  }

  /**
   * 批量删除人员
   */
  async batchDeletePersons() {
    if (this.selectedPersons.size === 0) return;

    const confirmed = await Modal.confirm(
      '批量删除',
      `确定要删除选中的 ${this.selectedPersons.size} 个人员吗？此操作无法撤销。`
    );
    
    if (!confirmed) return;

    try {
      showLoader('批量删除中...');
      
      const deletePromises = Array.from(this.selectedPersons).map(id => 
        faceRecognitionService.deletePerson(id)
      );
      
      await Promise.all(deletePromises);
      
      showToast('删除成功', `已删除 ${this.selectedPersons.size} 个人员`, 'success');
      
      // 清除选择
      this.selectedPersons.clear();
      
      // 重新加载列表
      await this.loadPersons();
      
    } catch (error) {
      console.error('批量删除失败:', error);
      showToast('删除失败', '批量删除时发生错误', 'error');
    } finally {
      hideLoader();
    }
  }

  /**
   * 清除选择
   */
  clearSelection() {
    this.selectedPersons.clear();
    this._updateDisplay();
  }

  /**
   * 显示人员详情
   * @private
   */
  _showPersonDetail(person) {
    const modal = document.getElementById('personDetailModal');
    const title = document.getElementById('personDetailModalTitle');
    const body = document.getElementById('personDetailModalBody');
    
    if (!modal || !title || !body) return;

    title.textContent = `人员详情 - ${person.name}`;
    
    body.innerHTML = `
      <div class="row">
        <div class="col-md-6">
          <h6>基本信息</h6>
          <table class="table table-sm">
            <tr><td>ID</td><td>${person.id}</td></tr>
            <tr><td>姓名</td><td>${person.name}</td></tr>
            <tr><td>描述</td><td>${person.description || '-'}</td></tr>
            <tr><td>创建时间</td><td>${formatDate(person.created_at)}</td></tr>
            <tr><td>人脸数量</td><td>${person.faces?.length || 0}</td></tr>
          </table>
        </div>
        <div class="col-md-6">
          <h6>人脸图片</h6>
          <div class="row">
            ${person.faces?.map((face, index) => `
              <div class="col-6 mb-2">
                <img src="/api/face_image/${face.id}" class="img-thumbnail" 
                     alt="人脸 ${index + 1}" style="width: 100%; height: 100px; object-fit: cover;">
              </div>
            `).join('') || '<p class="text-muted">暂无人脸图片</p>'}
          </div>
        </div>
      </div>
    `;
    
    new bootstrap.Modal(modal).show();
  }

  /**
   * 显示加载状态
   * @private
   */
  _showLoading() {
    const containers = [this.elements.tableBody, this.elements.cardContainer];
    containers.forEach(container => {
      if (container) {
        container.innerHTML = `
          <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">加载中...</span>
            </div>
            <div class="mt-2">加载中...</div>
          </div>
        `;
      }
    });
  }

  /**
   * 隐藏加载状态
   * @private
   */
  _hideLoading() {
    // 由_updateDisplay处理
  }

  /**
   * 显示错误
   * @private
   */
  _showError(message) {
    const containers = [this.elements.tableBody, this.elements.cardContainer];
    containers.forEach(container => {
      if (container) {
        container.innerHTML = `
          <div class="text-center py-5 text-danger">
            <i class="bi bi-exclamation-triangle fs-1 d-block mb-2"></i>
            <div>${message}</div>
            <button class="btn btn-outline-primary btn-sm mt-2" onclick="managementModule.loadPersons()">
              <i class="bi bi-arrow-clockwise me-1"></i>重试
            </button>
          </div>
        `;
      }
    });
  }

  /**
   * 导出人员数据
   */
  async exportPersonsData() {
    try {
      showLoader('准备导出数据...');
      
      const data = {
        export_time: new Date().toISOString(),
        total_persons: this.persons.length,
        persons: this.persons.map(person => ({
          id: person.id,
          name: person.name,
          description: person.description,
          created_at: person.created_at,
          face_count: person.face_count
        }))
      };
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { 
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
      
      showToast('导出成功', '人员数据已导出', 'success');
      
    } catch (error) {
      console.error('导出失败:', error);
      showToast('导出失败', '导出人员数据时发生错误', 'error');
    } finally {
      hideLoader();
    }
  }

  /**
   * 清除搜索
   */
  clearSearch() {
    if (this.elements.searchInput) {
      this.elements.searchInput.value = '';
      this.handleSearch('');
    }
  }

  /**
   * 获取模块状态
   */
  getStatus() {
    return {
      isLoading: this.isLoading,
      totalPersons: this.persons.length,
      filteredPersons: this.filteredPersons.length,
      selectedPersons: this.selectedPersons.size,
      currentPage: this.currentPage,
      viewMode: this.viewMode
    };
  }
}

// 创建并导出模块实例
const managementModule = new ManagementModule();

// 将模块实例添加到全局对象以便调试和HTML中使用
window.managementModule = managementModule;

export { ManagementModule };
export default managementModule;

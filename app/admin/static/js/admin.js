// Основной JavaScript для админ-панели
class AdminPanel {
    constructor() {
        this.init();
        this.setupEventListeners();
    }

    init() {
        // Инициализация компонентов
        this.setupTooltips();
        this.setupModals();
        this.setupTables();
        this.setupForms();
    }

    setupEventListeners() {
        // Обработчики событий для основных действий
        document.addEventListener('DOMContentLoaded', () => {
            this.handleOrderActions();
            this.handleFileOperations();
            this.handleStatusChanges();
            this.handleSearch();
        });
    }

    setupTooltips() {
        // Инициализация Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    setupModals() {
        // Настройка модальных окон
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('hidden.bs.modal', function () {
                // Очистка формы при закрытии модального окна
                const form = modal.querySelector('form');
                if (form) {
                    form.reset();
                }
            });
        });
    }

    setupTables() {
        // Настройка таблиц
        const tables = document.querySelectorAll('.table');
        tables.forEach(table => {
            // Добавление обработчиков для сортировки
            const headers = table.querySelectorAll('th[data-sort]');
            headers.forEach(header => {
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => {
                    this.sortTable(table, header.dataset.sort);
                });
            });
        });
    }

    setupForms() {
        // Настройка форм
        const forms = document.querySelectorAll('form[data-ajax]');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitAjaxForm(form);
            });
        });
    }

    // Обработка действий с заказами
    handleOrderActions() {
        // Изменение статуса заказа
        document.addEventListener('click', (e) => {
            if (e.target.matches('.change-status-btn')) {
                const orderId = e.target.dataset.orderId;
                const newStatus = e.target.dataset.status;
                this.changeOrderStatus(orderId, newStatus);
            }

            // Установка цены
            if (e.target.matches('.set-price-btn')) {
                const orderId = e.target.dataset.orderId;
                this.showPriceModal(orderId);
            }

            // Удаление заказа
            if (e.target.matches('.delete-order-btn')) {
                const orderId = e.target.dataset.orderId;
                this.confirmDeleteOrder(orderId);
            }
        });
    }

    // Обработка файловых операций
    handleFileOperations() {
        // Загрузка файлов
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.handleFileUpload(e.target);
            });
        });

        // Скачивание файлов
        document.addEventListener('click', (e) => {
            if (e.target.matches('.download-file-btn')) {
                const fileId = e.target.dataset.fileId;
                this.downloadFile(fileId);
            }

            // Удаление файлов
            if (e.target.matches('.delete-file-btn')) {
                const fileId = e.target.dataset.fileId;
                this.deleteFile(fileId);
            }
        });
    }

    // Изменение статуса заказа
    async changeOrderStatus(orderId, newStatus) {
        try {
            this.showLoading();
            
            const response = await fetch(`/api/orders/${orderId}/status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: newStatus })
            });

            if (response.ok) {
                this.showSuccess('Статус заказа успешно изменен');
                this.refreshOrderStatus(orderId);
            } else {
                this.showError('Ошибка при изменении статуса');
            }
        } catch (error) {
            this.showError('Произошла ошибка: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    // Установка цены заказа
    showPriceModal(orderId) {
        const modal = document.getElementById('priceModal');
        const orderIdInput = modal.querySelector('#orderId');
        const priceInput = modal.querySelector('#orderPrice');
        
        orderIdInput.value = orderId;
        priceInput.value = '';
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    async setPriceOrder(orderId, price) {
        try {
            this.showLoading();
            
            const response = await fetch(`/api/orders/${orderId}/price`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ price: parseFloat(price) })
            });

            if (response.ok) {
                this.showSuccess('Цена успешно установлена');
                this.refreshOrderRow(orderId);
            } else {
                this.showError('Ошибка при установке цены');
            }
        } catch (error) {
            this.showError('Произошла ошибка: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    // Загрузка файла
    async handleFileUpload(fileInput) {
        const files = fileInput.files;
        if (files.length === 0) return;

        const formData = new FormData();
        const orderId = fileInput.dataset.orderId;
        
        for (let file of files) {
            if (file.size > 20 * 1024 * 1024) { // 20MB
                this.showError(`Файл ${file.name} слишком большой (максимум 20MB)`);
                return;
            }
            formData.append('files', file);
        }

        try {
            this.showLoading();
            
            const response = await fetch(`/api/orders/${orderId}/files`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                this.showSuccess('Файлы успешно загружены');
                this.refreshFilesList(orderId);
            } else {
                this.showError('Ошибка при загрузке файлов');
            }
        } catch (error) {
            this.showError('Произошла ошибка: ' + error.message);
        } finally {
            this.hideLoading();
            fileInput.value = '';
        }
    }

    // Скачивание файла
    async downloadFile(fileId) {
        try {
            const response = await fetch(`/api/files/${fileId}/download`);
            if (response.ok) {
                const blob = await response.blob();
                const filename = response.headers.get('Content-Disposition')
                    ?.split('filename=')[1]?.replace(/"/g, '') || 'file';
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                this.showError('Ошибка при скачивании файла');
            }
        } catch (error) {
            this.showError('Произошла ошибка: ' + error.message);
        }
    }

    // Поиск
    handleSearch() {
        const searchInputs = document.querySelectorAll('input[data-search]');
        searchInputs.forEach(input => {
            let timeout;
            input.addEventListener('input', (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.performSearch(e.target.value, e.target.dataset.search);
                }, 300);
            });
        });
    }

    performSearch(query, type) {
        const tableBody = document.querySelector(`#${type}Table tbody`);
        if (!tableBody) return;

        const rows = tableBody.querySelectorAll('tr');
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const match = text.includes(query.toLowerCase());
            row.style.display = match ? '' : 'none';
        });
    }

    // Сортировка таблицы
    sortTable(table, column) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isAscending = table.dataset.sortOrder !== 'asc';
        
        rows.sort((a, b) => {
            const aValue = a.querySelector(`[data-${column}]`)?.textContent || '';
            const bValue = b.querySelector(`[data-${column}]`)?.textContent || '';
            
            if (isAscending) {
                return aValue.localeCompare(bValue, 'ru', { numeric: true });
            } else {
                return bValue.localeCompare(aValue, 'ru', { numeric: true });
            }
        });

        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));
        
        table.dataset.sortOrder = isAscending ? 'asc' : 'desc';
        
        // Обновление иконок сортировки
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            const icon = header.querySelector('.sort-icon');
            if (icon) {
                if (header.dataset.sort === column) {
                    icon.textContent = isAscending ? '↑' : '↓';
                } else {
                    icon.textContent = '↕';
                }
            }
        });
    }

    // Отправка AJAX формы
    async submitAjaxForm(form) {
        const formData = new FormData(form);
        const action = form.action;
        const method = form.method || 'POST';

        try {
            this.showLoading();
            
            const response = await fetch(action, {
                method: method,
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.showSuccess(result.message || 'Операция выполнена успешно');
                
                // Закрытие модального окна если есть
                const modal = form.closest('.modal');
                if (modal) {
                    bootstrap.Modal.getInstance(modal).hide();
                }
                
                // Обновление страницы или части контента
                if (result.reload) {
                    location.reload();
                }
            } else {
                const error = await response.json();
                this.showError(error.message || 'Произошла ошибка');
            }
        } catch (error) {
            this.showError('Произошла ошибка: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    // Обновление строки заказа
    async refreshOrderRow(orderId) {
        try {
            const response = await fetch(`/api/orders/${orderId}`);
            if (response.ok) {
                const order = await response.json();
                const row = document.querySelector(`tr[data-order-id="${orderId}"]`);
                if (row) {
                    // Обновление содержимого строки
                    this.updateOrderRowContent(row, order);
                }
            }
        } catch (error) {
            console.error('Ошибка обновления строки:', error);
        }
    }

    // Уведомления
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'danger');
    }

    showWarning(message) {
        this.showNotification(message, 'warning');
    }

    showNotification(message, type = 'info') {
        const alertsContainer = document.getElementById('alerts-container') || this.createAlertsContainer();
        
        const alertId = 'alert-' + Date.now();
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertsContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // Автоматическое скрытие через 5 секунд
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    createAlertsContainer() {
        const container = document.createElement('div');
        container.id = 'alerts-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1060';
        document.body.appendChild(container);
        return container;
    }

    // Индикатор загрузки
    showLoading() {
        const existingLoader = document.getElementById('loading-overlay');
        if (existingLoader) return;

        const loader = document.createElement('div');
        loader.id = 'loading-overlay';
        loader.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
        loader.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        loader.style.zIndex = '9999';
        loader.innerHTML = `
            <div class="spinner-border text-light" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
        `;
        
        document.body.appendChild(loader);
    }

    hideLoading() {
        const loader = document.getElementById('loading-overlay');
        if (loader) {
            loader.remove();
        }
    }

    // Подтверждение удаления
    confirmDeleteOrder(orderId) {
        if (confirm('Вы уверены, что хотите удалить этот заказ? Это действие нельзя отменить.')) {
            this.deleteOrder(orderId);
        }
    }

    async deleteOrder(orderId) {
        try {
            this.showLoading();
            
            const response = await fetch(`/api/orders/${orderId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showSuccess('Заказ успешно удален');
                const row = document.querySelector(`tr[data-order-id="${orderId}"]`);
                if (row) {
                    row.remove();
                }
            } else {
                this.showError('Ошибка при удалении заказа');
            }
        } catch (error) {
            this.showError('Произошла ошибка: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    new AdminPanel();
});

// Дополнительные утилиты
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Б';
    const k = 1024;
    const sizes = ['Б', 'КБ', 'МБ', 'ГБ'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// static/js/inventario.js
// JavaScript para funcionalidades del módulo de inventario

/**
 * Clase principal para manejar el inventario
 */
class InventarioManager {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.setupAutoRefresh();
    }

    /**
     * Inicialización del módulo
     */
    init() {
        console.log('Inicializando módulo de inventario...');
        this.loadingStates = new Map();
        this.filters = this.getFiltersFromURL();
        this.setupAnimations();
    }

    /**
     * Configurar event listeners
     */
    setupEventListeners() {
        // Filtros automáticos
        const filtroSelects = document.querySelectorAll('select[name="ubicacion"], select[name="categoria"]');
        filtroSelects.forEach(select => {
            select.addEventListener('change', (e) => {
                this.handleFilterChange(e);
            });
        });

        // Búsqueda con debounce
        const searchInput = document.querySelector('input[name="busqueda"]');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.handleSearchChange(e);
                }, 500);
            });
        }

        // Botones de acción
        this.setupActionButtons();

        // Tooltips
        this.setupTooltips();

        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
    }

    /**
     * Manejar cambios en filtros
     */
    handleFilterChange(event) {
        const form = event.target.closest('form');
        if (form) {
            this.showLoadingState();
            form.submit();
        }
    }

    /**
     * Manejar cambios en búsqueda
     */
    handleSearchChange(event) {
        const form = event.target.closest('form');
        if (form && event.target.value.length >= 2) {
            this.showLoadingState();
            form.submit();
        }
    }

    /**
     * Configurar botones de acción
     */
    setupActionButtons() {
        // Botones de ver detalles
        const detailButtons = document.querySelectorAll('[data-action="view-detail"]');
        detailButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.viewProductDetail(button.dataset.productId);
            });
        });

        // Botones de edición rápida
        const editButtons = document.querySelectorAll('[data-action="quick-edit"]');
        editButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.showQuickEditModal(button.dataset.productId);
            });
        });

        // Botones de alerta de stock
        const stockAlertButtons = document.querySelectorAll('[data-action="stock-alert"]');
        stockAlertButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleStockAlert(button.dataset.productId);
            });
        });
    }

    /**
     * Ver detalle de producto
     */
    viewProductDetail(productId) {
        this.showLoadingState();
        window.location.href = `/inventario/producto/${productId}/`;
    }

    /**
     * Mostrar modal de edición rápida
     */
    showQuickEditModal(productId) {
        // Implementar modal de edición rápida
        console.log(`Editando producto: ${productId}`);
        
        // Crear modal dinámicamente
        const modal = this.createQuickEditModal(productId);
        document.body.appendChild(modal);
        
        // Mostrar modal con animación
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
    }

    /**
     * Crear modal de edición rápida
     */
    createQuickEditModal(productId) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 opacity-0 transition-opacity duration-300';
        modal.innerHTML = `
            <div class="bg-white rounded-xl shadow-2xl max-w-md w-full transform scale-95 transition-transform duration-300">
                <div class="px-6 py-4 border-b border-gray-200">
                    <h3 class="text-lg font-semibold text-gray-900">Edición Rápida</h3>
                </div>
                <div class="p-6">
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Existencia</label>
                            <input type="number" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent" placeholder="Cantidad actual">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Precio</label>
                            <input type="number" step="0.01" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent" placeholder="Precio unitario">
                        </div>
                    </div>
                </div>
                <div class="px-6 py-4 bg-gray-50 flex justify-end space-x-3">
                    <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                        Cancelar
                    </button>
                    <button class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors">
                        Guardar
                    </button>
                </div>
            </div>
        `;

        // Event listener para cerrar modal al hacer clic fuera
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal(modal);
            }
        });

        return modal;
    }

    /**
     * Cerrar modal con animación
     */
    closeModal(modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }

    /**
     * Manejar alertas de stock
     */
    handleStockAlert(productId) {
        // Mostrar notificación de alerta de stock
        this.showNotification('Alerta de stock configurada correctamente', 'success');
        
        // Aquí se podría hacer una llamada AJAX para configurar la alerta
        this.configureStockAlert(productId);
    }

    /**
     * Configurar alerta de stock
     */
    async configureStockAlert(productId) {
        try {
            const response = await fetch('/inventario/api/stock-alert/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    product_id: productId,
                    alert_enabled: true
                })
            });

            if (response.ok) {
                this.showNotification('Alerta de stock configurada', 'success');
            } else {
                throw new Error('Error al configurar alerta');
            }
        } catch (error) {
            this.showNotification('Error al configurar alerta de stock', 'error');
            console.error('Error:', error);
        }
    }

    /**
     * Configurar tooltips
     */
    setupTooltips() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        tooltipElements.forEach(element => {
            element.classList.add('tooltip-inventario');
        });
    }

    /**
     * Configurar atajos de teclado
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + F para enfocar búsqueda
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                const searchInput = document.querySelector('input[name="busqueda"]');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }

            // Escape para limpiar filtros
            if (e.key === 'Escape') {
                const activeModal = document.querySelector('.fixed.inset-0');
                if (activeModal) {
                    this.closeModal(activeModal);
                } else {
                    this.clearFilters();
                }
            }
        });
    }

    /**
     * Limpiar filtros
     */
    clearFilters() {
        const url = new URL(window.location);
        url.search = '';
        window.location.href = url.toString();
    }

    /**
     * Configurar animaciones
     */
    setupAnimations() {
        // Animación de entrada para tarjetas
        const cards = document.querySelectorAll('.producto-card');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
                    }, index * 100);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        cards.forEach(card => {
            card.style.opacity = '0';
            observer.observe(card);
        });

        // Animación para medidores de stock
        this.animateStockMeters();
    }

    /**
     * Animar medidores de stock
     */
    animateStockMeters() {
        const stockFills = document.querySelectorAll('.stock-fill');
        stockFills.forEach((fill, index) => {
            const width = fill.style.width || fill.getAttribute('data-width');
            fill.style.width = '0%';
            setTimeout(() => {
                fill.style.width = width;
            }, 500 + (index * 100));
        });
    }

    /**
     * Configurar auto-refresh
     */
    setupAutoRefresh() {
        // Actualizar estadísticas cada 5 minutos
        setInterval(() => {
            this.refreshStats();
        }, 300000);
    }

    /**
     * Actualizar estadísticas
     */
    async refreshStats() {
        try {
            const response = await fetch('/inventario/api/stats/');
            if (response.ok) {
                const stats = await response.json();
                this.updateStatsDisplay(stats);
            }
        } catch (error) {
            console.error('Error al actualizar estadísticas:', error);
        }
    }

    /**
     * Actualizar display de estadísticas
     */
    updateStatsDisplay(stats) {
        // Actualizar contadores en tiempo real
        const totalProductos = document.querySelector('[data-stat="total-productos"]');
        const bajoStock = document.querySelector('[data-stat="bajo-stock"]');
        
        if (totalProductos) {
            this.animateCounter(totalProductos, stats.total_productos);
        }
        
        if (bajoStock) {
            this.animateCounter(bajoStock, stats.productos_bajo_stock);
        }
    }

    /**
     * Animar contador
     */
    animateCounter(element, targetValue) {
        const currentValue = parseInt(element.textContent) || 0;
        const increment = (targetValue - currentValue) / 20;
        let current = currentValue;

        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= targetValue) || 
                (increment < 0 && current <= targetValue)) {
                current = targetValue;
                clearInterval(timer);
            }
            element.textContent = Math.round(current);
        }, 50);
    }

    /**
     * Mostrar estado de carga
     */
    showLoadingState() {
        const loader = document.createElement('div');
        loader.className = 'fixed inset-0 bg-white bg-opacity-75 z-50 flex items-center justify-center';
        loader.innerHTML = `
            <div class="text-center">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                <p class="text-gray-600">Cargando inventario...</p>
            </div>
        `;
        document.body.appendChild(loader);

        // Remover después de 10 segundos máximo
        setTimeout(() => {
            if (loader.parentNode) {
                loader.remove();
            }
        }, 10000);
    }

    /**
     * Mostrar notificación
     */
    showNotification(message, type = 'info') {
        if (typeof showNotification === 'function') {
            showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    /**
     * Obtener filtros de la URL
     */
    getFiltersFromURL() {
        const params = new URLSearchParams(window.location.search);
        return {
            busqueda: params.get('busqueda') || '',
            ubicacion: params.get('ubicacion') || '',
            categoria: params.get('categoria') || ''
        };
    }

    /**
     * Obtener token CSRF
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               window.NEXO?.csrf_token || '';
    }
}

/**
 * Utilidades para el inventario
 */
class InventarioUtils {
    /**
     * Formatear números con separadores de miles
     */
    static formatNumber(num) {
        return new Intl.NumberFormat('es-NI').format(num);
    }

    /**
     * Formatear precios
     */
    static formatPrice(price) {
        return new Intl.NumberFormat('es-NI', {
            style: 'currency',
            currency: 'NIO'
        }).format(price);
    }

    /**
     * Calcular nivel de stock
     */
    static getStockLevel(current, minimum = 5) {
        if (current === 0) return 'agotado';
        if (current <= minimum) return 'bajo';
        if (current <= 20) return 'medio';
        return 'alto';
    }

    /**
     * Obtener color para nivel de stock
     */
    static getStockColor(level) {
        const colors = {
            'agotado': '#6b7280',
            'bajo': '#ef4444',
            'medio': '#f59e0b',
            'alto': '#10b981'
        };
        return colors[level] || colors.alto;
    }

    /**
     * Validar formularios
     */
    static validateForm(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('border-red-500');
                isValid = false;
            } else {
                field.classList.remove('border-red-500');
            }
        });

        return isValid;
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar el manager de inventario
    window.inventarioManager = new InventarioManager();
    
    // Hacer disponibles las utilidades globalmente
    window.InventarioUtils = InventarioUtils;
    
    console.log('Módulo de inventario inicializado correctamente');
});

// Exportar para uso en otros módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { InventarioManager, InventarioUtils };
}
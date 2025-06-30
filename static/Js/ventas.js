// static/js/ventas.js
// JavaScript para funcionalidades del módulo de ventas

/**
 * Clase principal para manejar las ventas
 */
class VentasManager {
  constructor() {
    this.init()
    this.setupEventListeners()
    this.setupAutoRefresh()
  }

  /**
   * Inicialización del módulo
   */
  init() {
    console.log("Inicializando módulo de ventas...")
    this.carritoProductos = []
    this.totalVenta = 0
    this.setupAnimations()
  }

  /**
   * Configurar event listeners
   */
  setupEventListeners() {
    // Filtros automáticos
    const filtroSelects = document.querySelectorAll('select[name="cliente"], select[name="estado"]')
    filtroSelects.forEach((select) => {
      select.addEventListener("change", (e) => {
        this.handleFilterChange(e)
      })
    })

    // Búsqueda con debounce
    const searchInput = document.querySelector('input[name="q"]')
    if (searchInput) {
      let searchTimeout
      searchInput.addEventListener("input", (e) => {
        clearTimeout(searchTimeout)
        searchTimeout = setTimeout(() => {
          this.handleSearchChange(e)
        }, 500)
      })
    }

    // Botones de acción
    this.setupActionButtons()

    // Keyboard shortcuts
    this.setupKeyboardShortcuts()
  }

  /**
   * Manejar cambios en filtros
   */
  handleFilterChange(event) {
    const form = event.target.closest("form")
    if (form) {
      this.showLoadingState()
      form.submit()
    }
  }

  /**
   * Manejar cambios en búsqueda
   */
  handleSearchChange(event) {
    const form = event.target.closest("form")
    if (form && event.target.value.length >= 2) {
      this.showLoadingState()
      form.submit()
    }
  }

  /**
   * Configurar botones de acción
   */
  setupActionButtons() {
    // Botones de ver detalle
    const detailButtons = document.querySelectorAll('[data-action="view-detail"]')
    detailButtons.forEach((button) => {
      button.addEventListener("click", (e) => {
        e.preventDefault()
        this.viewVentaDetail(button.dataset.ventaId)
      })
    })

    // Botones de edición
    const editButtons = document.querySelectorAll('[data-action="edit-venta"]')
    editButtons.forEach((button) => {
      button.addEventListener("click", (e) => {
        e.preventDefault()
        this.editVenta(button.dataset.ventaId)
      })
    })

    // Botones de anulación
    const cancelButtons = document.querySelectorAll('[data-action="cancel-venta"]')
    cancelButtons.forEach((button) => {
      button.addEventListener("click", (e) => {
        e.preventDefault()
        this.showCancelConfirmation(button.dataset.ventaId)
      })
    })
  }

  /**
   * Ver detalle de venta
   */
  viewVentaDetail(ventaId) {
    this.showLoadingState()
    window.location.href = `/ventas/detalle/${ventaId}/`
  }

  /**
   * Editar venta
   */
  editVenta(ventaId) {
    this.showLoadingState()
    window.location.href = `/ventas/editar/${ventaId}/`
  }

  /**
   * Mostrar confirmación de anulación
   */
  showCancelConfirmation(ventaId) {
    const modal = this.createCancelModal(ventaId)
    document.body.appendChild(modal)

    setTimeout(() => {
      modal.classList.add("show")
    }, 10)
  }

  /**
   * Crear modal de confirmación de anulación
   */
  createCancelModal(ventaId) {
    const modal = document.createElement("div")
    modal.className =
      "fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 opacity-0 transition-opacity duration-300"
    modal.innerHTML = `
            <div class="bg-white rounded-xl shadow-2xl max-w-md w-full transform scale-95 transition-transform duration-300">
                <div class="px-6 py-4 border-b border-gray-200">
                    <h3 class="text-lg font-semibold text-gray-900 flex items-center">
                        <i class="fas fa-exclamation-triangle text-red-500 mr-2"></i>
                        Anular Venta
                    </h3>
                </div>
                <div class="p-6">
                    <p class="text-gray-600 mb-4">
                        ¿Está seguro de que desea anular la venta #${ventaId}?
                    </p>
                    <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                        <div class="flex items-center">
                            <i class="fas fa-info-circle text-yellow-600 mr-2"></i>
                            <span class="text-sm text-yellow-800">
                                Esta acción devolverá el stock de los productos y no se puede deshacer.
                            </span>
                        </div>
                    </div>
                </div>
                <div class="px-6 py-4 bg-gray-50 flex justify-end space-x-3">
                    <button onclick="this.closest('.fixed').remove()" 
                            class="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                        Cancelar
                    </button>
                    <button onclick="window.location.href='/ventas/anular/${ventaId}/'" 
                            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
                        <i class="fas fa-ban mr-2"></i>Anular Venta
                    </button>
                </div>
            </div>
        `

    // Event listener para cerrar modal al hacer clic fuera
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        this.closeModal(modal)
      }
    })

    return modal
  }

  /**
   * Cerrar modal con animación
   */
  closeModal(modal) {
    modal.classList.remove("show")
    setTimeout(() => {
      modal.remove()
    }, 300)
  }

  /**
   * Configurar atajos de teclado
   */
  setupKeyboardShortcuts() {
    document.addEventListener("keydown", (e) => {
      // Ctrl/Cmd + N para nueva venta
      if ((e.ctrlKey || e.metaKey) && e.key === "n") {
        e.preventDefault()
        window.location.href = "/ventas/crear/"
      }

      // Ctrl/Cmd + F para enfocar búsqueda
      if ((e.ctrlKey || e.metaKey) && e.key === "f") {
        e.preventDefault()
        const searchInput = document.querySelector('input[name="q"]')
        if (searchInput) {
          searchInput.focus()
          searchInput.select()
        }
      }

      // Escape para cerrar modales
      if (e.key === "Escape") {
        const activeModal = document.querySelector(".fixed.inset-0")
        if (activeModal) {
          this.closeModal(activeModal)
        }
      }
    })
  }

  /**
   * Configurar animaciones
   */
  setupAnimations() {
    // Animación de entrada para filas de tabla
    const rows = document.querySelectorAll(".venta-row")
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry, index) => {
          if (entry.isIntersecting) {
            setTimeout(() => {
              entry.target.style.animation = "fadeInUp 0.6s ease forwards"
            }, index * 50)
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.1 },
    )

    rows.forEach((row) => {
      row.style.opacity = "0"
      observer.observe(row)
    })

    // Animación para tarjetas de estadísticas
    this.animateStatsCards()
  }

  /**
   * Animar tarjetas de estadísticas
   */
  animateStatsCards() {
    const statsCards = document.querySelectorAll(".stats-card")
    statsCards.forEach((card, index) => {
      card.style.opacity = "0"
      card.style.transform = "translateY(20px)"
      setTimeout(() => {
        card.style.transition = "all 0.5s ease"
        card.style.opacity = "1"
        card.style.transform = "translateY(0)"
      }, index * 100)
    })
  }

  /**
   * Configurar auto-refresh
   */
  setupAutoRefresh() {
    // Actualizar estadísticas cada 2 minutos
    setInterval(() => {
      this.refreshStats()
    }, 120000)
  }

  /**
   * Actualizar estadísticas
   */
  async refreshStats() {
    try {
      const response = await fetch("/ventas/api/estadisticas/")
      if (response.ok) {
        const data = await response.json()
        this.updateStatsDisplay(data.estadisticas)
      }
    } catch (error) {
      console.error("Error al actualizar estadísticas:", error)
    }
  }

  /**
   * Actualizar display de estadísticas
   */
  updateStatsDisplay(stats) {
    // Actualizar ventas de hoy
    const ventasHoyTotal = document.querySelector('[data-stat="ventas-hoy-total"]')
    const ventasHoyCantidad = document.querySelector('[data-stat="ventas-hoy-cantidad"]')

    if (ventasHoyTotal && stats.ventas_hoy) {
      this.animateCounter(ventasHoyTotal, stats.ventas_hoy.total)
    }

    if (ventasHoyCantidad && stats.ventas_hoy) {
      this.animateCounter(ventasHoyCantidad, stats.ventas_hoy.cantidad)
    }
  }

  /**
   * Animar contador
   */
  animateCounter(element, targetValue) {
    const currentValue = Number.parseFloat(element.textContent.replace(/[^0-9.-]+/g, "")) || 0
    const increment = (targetValue - currentValue) / 20
    let current = currentValue

    const timer = setInterval(() => {
      current += increment
      if ((increment > 0 && current >= targetValue) || (increment < 0 && current <= targetValue)) {
        current = targetValue
        clearInterval(timer)
      }

      // Formatear según el tipo de dato
      if (element.textContent.includes("$")) {
        element.textContent = `$${current.toFixed(2)}`
      } else {
        element.textContent = Math.round(current)
      }
    }, 50)
  }

  /**
   * Mostrar estado de carga
   */
  showLoadingState() {
    const loader = document.createElement("div")
    loader.className = "fixed inset-0 bg-white bg-opacity-75 z-50 flex items-center justify-center"
    loader.innerHTML = `
            <div class="text-center">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                <p class="text-gray-600">Cargando ventas...</p>
            </div>
        `
    document.body.appendChild(loader)

    // Remover después de 10 segundos máximo
    setTimeout(() => {
      if (loader.parentNode) {
        loader.remove()
      }
    }, 10000)
  }

  /**
   * Mostrar notificación
   */
  showNotification(message, type = "info") {
    if (typeof window.showNotification === "function") {
      window.showNotification(message, type)
    } else {
      console.log(`${type.toUpperCase()}: ${message}`)
    }
  }

  /**
   * Obtener token CSRF
   */
  getCSRFToken() {
    return document.querySelector("[name=csrfmiddlewaretoken]")?.value || window.NEXO?.csrf_token || ""
  }
}

/**
 * Clase para manejar el carrito de ventas
 */
class CarritoVentas {
  constructor() {
    this.productos = []
    this.total = 0
    this.init()
  }

  init() {
    this.setupEventListeners()
  }

  setupEventListeners() {
    // Event listener para agregar productos
    const btnAgregar = document.getElementById("btn-agregar-producto")
    if (btnAgregar) {
      btnAgregar.addEventListener("click", () => {
        this.agregarProducto()
      })
    }

    // Event listener para cambios en producto
    const selectProducto = document.getElementById("id_producto")
    if (selectProducto) {
      selectProducto.addEventListener("change", (e) => {
        this.actualizarInfoProducto(e.target.value)
      })
    }

    // Event listener para cambios en cantidad
    const inputCantidad = document.getElementById("id_cantidad")
    if (inputCantidad) {
      inputCantidad.addEventListener("input", () => {
        this.calcularSubtotal()
      })
    }
  }

  async actualizarInfoProducto(productoId) {
    if (!productoId) {
      this.ocultarInfoProducto()
      return
    }

    try {
      const response = await fetch(`/ventas/api/producto-info/?producto_id=${productoId}`)
      const data = await response.json()

      if (data.success) {
        this.mostrarInfoProducto(data.producto)
      } else {
        this.mostrarError("Error al obtener información del producto")
      }
    } catch (error) {
      console.error("Error:", error)
      this.mostrarError("Error de conexión")
    }
  }

  mostrarInfoProducto(producto) {
    const infoContainer = document.getElementById("info-producto")
    const precioElement = document.getElementById("precio-producto")
    const stockElement = document.getElementById("stock-producto")
    const categoriaElement = document.getElementById("categoria-producto")

    if (infoContainer && precioElement && stockElement && categoriaElement) {
      precioElement.textContent = `C$${producto.precio_con_impuesto.toFixed(2)}`
      stockElement.textContent = producto.stock
      categoriaElement.textContent = producto.categoria || "Sin categoría"

      infoContainer.classList.remove("hidden")

      // Actualizar límite de cantidad
      const cantidadInput = document.getElementById("id_cantidad")
      if (cantidadInput) {
        cantidadInput.max = producto.stock
        cantidadInput.value = Math.min(cantidadInput.value || 1, producto.stock)
      }

      this.calcularSubtotal()
    }
  }

  ocultarInfoProducto() {
    const infoContainer = document.getElementById("info-producto")
    if (infoContainer) {
      infoContainer.classList.add("hidden")
    }
  }

  calcularSubtotal() {
    const cantidadInput = document.getElementById("id_cantidad")
    const precioElement = document.getElementById("precio-producto")
    const subtotalElement = document.getElementById("subtotal-producto")

    if (!cantidadInput || !precioElement || !subtotalElement) return

    const cantidad = Number.parseInt(cantidadInput.value) || 0
    const precio = Number.parseFloat(precioElement.textContent.replace("C$", "")) || 0
    const subtotal = cantidad * precio

    subtotalElement.textContent = `C$${subtotal.toFixed(2)}`
  }

  agregarProducto() {
    const selectProducto = document.getElementById("id_producto")
    const inputCantidad = document.getElementById("id_cantidad")

    if (!selectProducto.value || !inputCantidad.value) {
      this.mostrarError("Seleccione un producto y cantidad")
      return
    }

    const productoId = selectProducto.value
    const cantidad = Number.parseInt(inputCantidad.value)
    const productoNombre = selectProducto.options[selectProducto.selectedIndex].text
    const precio = Number.parseFloat(document.getElementById("precio-producto").textContent.replace("C$", ""))
    const stock = Number.parseInt(document.getElementById("stock-producto").textContent)

    // Validar stock
    // Verificar stock total incluyendo lo que ya está en el carrito
    const cantidadEnCarrito = this.productos.reduce((total, p) => {
      return p.id === productoId ? total + p.cantidad : total
    }, 0)

    if (cantidadEnCarrito + cantidad > stock) {
      this.mostrarNotificacion(`Stock insuficiente. Disponible: ${stock}, en carrito: ${cantidadEnCarrito}`, "error")
      return
    }

    // Verificar si el producto ya está en el carrito
    const productoExistente = this.productos.find((p) => p.id === productoId)
    if (productoExistente) {
      const nuevaCantidad = productoExistente.cantidad + cantidad
      if (nuevaCantidad > stock) {
        this.mostrarError(`Stock insuficiente. Ya tiene ${productoExistente.cantidad} en el carrito`)
        return
      }
      productoExistente.cantidad = nuevaCantidad
      productoExistente.subtotal = productoExistente.cantidad * precio
    } else {
      this.productos.push({
        id: productoId,
        nombre: productoNombre,
        precio: precio,
        cantidad: cantidad,
        subtotal: precio * cantidad,
      })
    }

    // Limpiar formulario
    selectProducto.value = ""
    inputCantidad.value = ""
    this.ocultarInfoProducto()

    // Actualizar vista del carrito
    this.actualizarCarrito()

    this.mostrarNotificacion("Producto agregado al carrito", "success")
  }

  actualizarCarrito() {
    this.renderizarCarrito()
    this.actualizarTotales()
    this.actualizarContador()
    this.habilitarBotonProcesar()
  }

  renderizarCarrito() {
    const carritoContainer = document.getElementById("carrito-productos")
    if (!carritoContainer) return

    if (this.productos.length === 0) {
      carritoContainer.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    <i class="fas fa-shopping-basket text-4xl mb-4"></i>
                    <p>No hay productos agregados</p>
                    <p class="text-sm">Seleccione productos para agregar a la venta</p>
                </div>
            `
    } else {
      let html = ""
      this.productos.forEach((producto, index) => {
        html += `
                    <div class="carrito-item p-4">
                        <div class="flex items-center justify-between">
                            <div class="flex-1">
                                <h4 class="font-medium text-gray-900">${producto.nombre}</h4>
                                <div class="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                                    <span>Precio: C$${producto.precio.toFixed(2)}</span>
                                    <span>Cantidad: ${producto.cantidad}</span>
                                    <span class="font-bold text-primary">Subtotal: C$${producto.subtotal.toFixed(2)}</span>
                                </div>
                            </div>
                            <div class="flex items-center space-x-2">
                                <button type="button" 
                                        onclick="carritoVentas.editarCantidad(${index})"
                                        class="text-blue-600 hover:text-blue-800"
                                        title="Editar cantidad">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button type="button" 
                                        onclick="carritoVentas.eliminarProducto(${index})"
                                        class="text-red-600 hover:text-red-800"
                                        title="Eliminar">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `
      })
      carritoContainer.innerHTML = html
    }
  }

  actualizarTotales() {
    const subtotal = this.productos.reduce((sum, producto) => sum + producto.subtotal, 0)
    const iva = subtotal * 0.15
    const total = subtotal + iva

    const subtotalElement = document.getElementById("subtotal-venta")
    const ivaElement = document.getElementById("iva-venta")
    const totalElement = document.getElementById("total-venta")

    if (subtotalElement) subtotalElement.textContent = `C$${subtotal.toFixed(2)}`
    if (ivaElement) ivaElement.textContent = `C$${iva.toFixed(2)}`
    if (totalElement) totalElement.textContent = `C$${total.toFixed(2)}`

    this.total = total
  }

  actualizarContador() {
    const contador = document.getElementById("contador-productos")
    if (contador) {
      contador.textContent = this.productos.length
    }
  }

  habilitarBotonProcesar() {
    const btnProcesar = document.getElementById("btn-procesar-venta")
    if (btnProcesar) {
      btnProcesar.disabled = this.productos.length === 0
    }
  }

  eliminarProducto(index) {
    if (confirm("¿Está seguro de eliminar este producto del carrito?")) {
      this.productos.splice(index, 1)
      this.actualizarCarrito()
      this.mostrarNotificacion("Producto eliminado del carrito", "info")
    }
  }

  editarCantidad(index) {
    const producto = this.productos[index]
    const nuevaCantidad = prompt(`Ingrese la nueva cantidad para ${producto.nombre}:`, producto.cantidad)

    if (nuevaCantidad && !isNaN(nuevaCantidad) && Number.parseInt(nuevaCantidad) > 0) {
      const cantidad = Number.parseInt(nuevaCantidad)
      producto.cantidad = cantidad
      producto.subtotal = producto.precio * cantidad
      this.actualizarCarrito()
      this.mostrarNotificacion("Cantidad actualizada", "success")
    }
  }

  limpiar() {
    if (this.productos.length === 0) return

    if (confirm("¿Está seguro de limpiar todo el carrito?")) {
      this.productos = []
      this.actualizarCarrito()
      this.mostrarNotificacion("Carrito limpiado", "info")
    }
  }

  obtenerDetalles() {
    return this.productos.map((producto) => ({
      idProVenta: producto.id,
      cantidadVenta: producto.cantidad,
    }))
  }

  mostrarError(mensaje) {
    this.mostrarNotificacion(mensaje, "error")
  }

  mostrarNotificacion(mensaje, tipo = "info") {
    if (typeof window.showNotification === "function") {
      window.showNotification(mensaje, tipo)
    } else {
      alert(mensaje)
    }
  }
}

// Inicializar cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", () => {
  // Inicializar el manager de ventas
  window.ventasManager = new VentasManager()

  // Inicializar el carrito si estamos en la página de crear venta
  if (document.getElementById("carrito-productos")) {
    window.carritoVentas = new CarritoVentas()

    // Función global para limpiar carrito
    window.limpiarCarrito = () => {
      window.carritoVentas.limpiar()
    }

    // Función global para procesar venta
    window.procesarVenta = () => {
      const clienteSelect = document.querySelector('select[name="codcliente"]')
      if (!clienteSelect.value) {
        window.carritoVentas.mostrarError("Seleccione un cliente")
        clienteSelect.focus()
        return
      }

      if (window.carritoVentas.productos.length === 0) {
        window.carritoVentas.mostrarError("Agregue productos al carrito")
        return
      }

      // Preparar datos
      const detalles = window.carritoVentas.obtenerDetalles()
      document.getElementById("detalles_venta").value = JSON.stringify(detalles)

      // Confirmar venta
      if (confirm(`¿Confirmar venta por un total de C$${window.carritoVentas.total.toFixed(2)}?`)) {
        const btnProcesar = document.getElementById("btn-procesar-venta")
        btnProcesar.disabled = true
        btnProcesar.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Procesando...'

        document.getElementById("form-venta").submit()
      }
    }
  }

  console.log("Módulo de ventas inicializado correctamente")
})

// Exportar para uso en otros módulos
if (typeof module !== "undefined" && module.exports) {
  module.exports = { VentasManager, CarritoVentas }
}

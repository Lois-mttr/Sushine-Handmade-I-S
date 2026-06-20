

// ===== CONFIGURACIÃ“N GLOBAL =====
const NEXO_CONFIG = {
  refresh_interval: 30000, // Intervalo de actualizaciÃ³n automÃ¡tica (30 segundos)
  chart_animation_duration: 0,
  notification_duration: 5000, // DuraciÃ³n de notificaciones
  chart_colors: [
    "#4ECDC4", // Color primario NEXO
    "#f2ce16", // Amarillo secundario
    "#f28627", // Naranja
    "#39bfb2", // Verde azulado oscuro
    "#f29d35", // Naranja claro
    "#10b981", // Verde Ã©xito
    "#3b82f6", // Azul
    "#8b5cf6", // PÃºrpura
    "#ef4444", // Rojo error
    "#06b6d4", // Cian
  ],
}

// ===== CLASE PRINCIPAL DEL DASHBOARD =====
class NexoDashboard {
  constructor() {
    this.charts = {} // Almacena las instancias de grÃ¡ficos
    this.updateTimers = {} // Almacena los timers de actualizaciÃ³n
    this.isUpdating = false // Flag para evitar actualizaciones simultÃ¡neas

    this.init()
  }

  async init() {
    console.log("ðŸš€ Inicializando NEXO Dashboard...")

    try {
      // Configurar Chart.js si estÃ¡ disponible
      this.setupChartDefaults()

      // Inicializar grÃ¡ficos
      await this.initCharts()

      // Configurar event listeners
      this.setupEventListeners()

      // Iniciar actualizaciones automÃ¡ticas
      this.startRealTimeUpdates()

      console.log("âœ… NEXO Dashboard inicializado correctamente")
    } catch (error) {
      console.error("âŒ Error inicializando dashboard:", error)
      this.showNotification("Error al inicializar el dashboard", "error")
    }
  }

  setupChartDefaults() {
    // ConfiguraciÃ³n global de Chart.js si estÃ¡ disponible
    if (typeof Chart !== "undefined") {
      Chart.defaults.font.family = "Inter, system-ui, sans-serif"
      Chart.defaults.color = "#6b7280"
      Chart.defaults.plugins.legend.display = false
    }
  }

  async initCharts() {
    try {
      // Verificar que Chart.js estÃ© disponible
      if (typeof Chart === "undefined") {
        console.warn("âš ï¸ Chart.js no estÃ¡ disponible")
        return
      }

      // Inicializar grÃ¡fico de productos mÃ¡s vendidos
      await this.createProductosVendidosChart()

      // Inicializar grÃ¡fico de productos mÃ¡s devueltos
      await this.createProductosDevueltosChart()

      console.log("ðŸ“Š GrÃ¡ficos inicializados correctamente")
    } catch (error) {
      console.error("âŒ Error inicializando grÃ¡ficos:", error)
    }
  }

  async createProductosVendidosChart() {
    const canvas = document.getElementById("productos-vendidos-chart")
    if (!canvas || typeof Chart === "undefined") return

    const ctx = canvas.getContext("2d")

    const data = this.extractChartData("productos_mas_vendidos")

    // Destruir grÃ¡fico existente si existe
    if (this.charts.productosVendidos) {
      this.charts.productosVendidos.destroy()
    }

    this.charts.productosVendidos = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: data.map((item) => item.nombre || "Sin nombre"),
        datasets: [
          {
            data: data.map((item) => item.cantidad || 0),
            backgroundColor: NEXO_CONFIG.chart_colors.slice(0, data.length),
            borderColor: "#ffffff",
            borderWidth: 2,
            hoverBorderWidth: 2,
            hoverOffset: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            titleColor: "white",
            bodyColor: "white",
            borderColor: "#4ECDC4",
            borderWidth: 1,
            cornerRadius: 8,
            callbacks: {
              label: (context) => {
                const total = context.dataset.data.reduce((a, b) => a + b, 0)
                const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0
                return `${context.label}: ${context.parsed} (${percentage}%)`
              },
            },
          },
        },
        animation: {
          animateRotate: false,
          duration: NEXO_CONFIG.chart_animation_duration,
        },
      },
    })

    // Crear leyenda personalizada
    this.createCustomLegend("productos-vendidos-legend", data, NEXO_CONFIG.chart_colors)
  }

  async createProductosDevueltosChart() {
    const canvas = document.getElementById("productos-devueltos-chart")
    if (!canvas || typeof Chart === "undefined") return

    const ctx = canvas.getContext("2d")

    const data = this.extractChartData("productos_mas_devueltos")

    // Destruir grÃ¡fico existente si existe
    if (this.charts.productosDevueltos) {
      this.charts.productosDevueltos.destroy()
    }

    this.charts.productosDevueltos = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: data.map((item) => item.nombre || "Sin nombre"),
        datasets: [
          {
            data: data.map((item) => item.cantidad || 0),
            backgroundColor: NEXO_CONFIG.chart_colors.slice(0, data.length),
            borderColor: "#ffffff",
            borderWidth: 2,
            hoverBorderWidth: 2,
            hoverOffset: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            titleColor: "white",
            bodyColor: "white",
            borderColor: "#4ECDC4",
            borderWidth: 1,
            cornerRadius: 8,
            callbacks: {
              label: (context) => {
                const total = context.dataset.data.reduce((a, b) => a + b, 0)
                const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0
                return `${context.label}: ${context.parsed} (${percentage}%)`
              },
            },
          },
        },
        animation: {
          animateRotate: false,
          duration: NEXO_CONFIG.chart_animation_duration,
        },
      },
    })

    // Crear leyenda personalizada
    this.createCustomLegend("productos-devueltos-legend", data, NEXO_CONFIG.chart_colors)
  }

  createCustomLegend(containerId, data, colors) {
    const container = document.getElementById(containerId)
    if (!container) return

    container.innerHTML = ""
    const chartCard = container.closest(".bg-white")
    const canvasWrapper = chartCard ? chartCard.querySelector(".relative.h-72") : null

    if (!data || data.length === 0) {
      if (canvasWrapper) canvasWrapper.classList.add("hidden")
      container.innerHTML = '<span class="text-xs text-gray-500">No hay datos reales disponibles</span>'
      return
    }

    if (canvasWrapper) canvasWrapper.classList.remove("hidden")

    data.forEach((item, index) => {
      const legendItem = document.createElement("div")
      legendItem.className = "flex items-center space-x-2 text-xs"
      legendItem.innerHTML = `
                <div class="w-3 h-3 rounded-full" style="background-color: ${colors[index]}"></div>
                <span class="text-gray-600">${item.nombre || "Sin nombre"}</span>
            `
      container.appendChild(legendItem)
    })
  }

  extractChartData(key) {
    if (!window.chartDataByLocation || typeof window.chartDataByLocation !== "object") return []

    const grouped = new Map()

    Object.values(window.chartDataByLocation).forEach((location) => {
      const rows = Array.isArray(location[key]) ? location[key] : []
      rows.forEach((item) => {
        const name = item.nombre || "Sin nombre"
        const current = grouped.get(name) || { ...item, nombre: name, cantidad: 0 }
        current.cantidad += Number(item.cantidad || 0)
        grouped.set(name, current)
      })
    })

    return Array.from(grouped.values())
      .filter((item) => item.cantidad > 0)
      .sort((a, b) => b.cantidad - a.cantidad)
      .slice(0, 5)
  }

  setupEventListeners() {
    // Listener para botÃ³n de actualizar
    const refreshButton = document.querySelector("[data-refresh-dashboard]")
    if (refreshButton) {
      refreshButton.addEventListener("click", (e) => {
        e.preventDefault()
        e.stopPropagation()
        this.refreshDashboard()
      })
    }

    // Listener para cambios de visibilidad de la pÃ¡gina
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        this.stopRealTimeUpdates()
      } else {
        this.startRealTimeUpdates()
        this.updateDashboardStats()
      }
    })

    // Listeners para conexiÃ³n de red
    window.addEventListener("online", () => {
      this.showNotification("ConexiÃ³n restaurada", "success")
      this.startRealTimeUpdates()
    })

    window.addEventListener("offline", () => {
      this.showNotification("Sin conexiÃ³n a internet", "error")
      this.stopRealTimeUpdates()
    })
  }

  startRealTimeUpdates() {
    // Limpiar timers existentes
    this.stopRealTimeUpdates()

    // Actualizar estadÃ­sticas cada 30 segundos
    this.updateTimers.stats = setInterval(() => {
      this.updateDashboardStats()
    }, NEXO_CONFIG.refresh_interval)

    console.log("ðŸ”„ Actualizaciones automÃ¡ticas iniciadas")
  }

  stopRealTimeUpdates() {
    Object.values(this.updateTimers).forEach((timer) => {
      clearInterval(timer)
    })
    this.updateTimers = {}
    console.log("â¹ï¸ Actualizaciones automÃ¡ticas detenidas")
  }

  async updateDashboardStats() {
    if (this.isUpdating) {
      console.log("â³ ActualizaciÃ³n ya en progreso, saltando...")
      return
    }

    this.isUpdating = true
    console.log("ðŸ”„ Iniciando actualizaciÃ³n de estadÃ­sticas...")

    try {
      // Verificar que las URLs estÃ©n disponibles
      if (!window.NEXO || !window.NEXO.urls || !window.NEXO.urls.dashboard_stats) {
        throw new Error("URLs de API no disponibles")
      }

      const response = await this.makeRequest(window.NEXO.urls.dashboard_stats)

      if (response.success) {
        console.log("âœ… Datos actualizados correctamente:", response.data)

        // Actualizar mÃ©tricas con animaciÃ³n
        this.updateStatsUI(response.data.metrics)

        // Actualizar grÃ¡ficos
        this.updateCharts(response.data.chart_data_by_location)

        // Actualizar timestamp
        this.updateLastUpdateTime()

        this.showNotification("EstadÃ­sticas actualizadas", "success", 2000)
      } else {
        throw new Error(response.error || "Error desconocido")
      }
    } catch (error) {
      console.error("âŒ Error actualizando estadÃ­sticas:", error)
      this.showNotification("Error al actualizar estadÃ­sticas: " + error.message, "error")
    } finally {
      this.isUpdating = false
    }
  }

  updateStatsUI(metrics) {
    // Actualizar mÃ©tricas principales con animaciÃ³n
    const metricsMap = {
      "total-productos": metrics.total_productos,
      "total-clientes": metrics.total_clientes,
      "ventas-mes": metrics.ventas_mes,
      "productos-bajo-stock": metrics.productos_bajo_stock,
    }

    Object.keys(metricsMap).forEach((key) => {
      const element = document.getElementById(key)
      if (element && typeof metricsMap[key] === "number") {
        element.textContent = metricsMap[key]
      }
    })
  }

  updateCharts(chartData) {
    if (!chartData || typeof chartData !== "object") {
      console.log("ðŸ“Š No hay datos de grÃ¡ficos para actualizar")
      return
    }

    console.log("ðŸ“Š Actualizando grÃ¡ficos con datos:", chartData)

    window.chartDataByLocation = chartData

    const productosVendidos = this.extractChartData("productos_mas_vendidos")
    if (this.charts.productosVendidos) {
      this.updateChart(this.charts.productosVendidos, productosVendidos)
      this.createCustomLegend("productos-vendidos-legend", productosVendidos, NEXO_CONFIG.chart_colors)
    }

    const productosDevueltos = this.extractChartData("productos_mas_devueltos")
    if (this.charts.productosDevueltos) {
      this.updateChart(this.charts.productosDevueltos, productosDevueltos)
      this.createCustomLegend("productos-devueltos-legend", productosDevueltos, NEXO_CONFIG.chart_colors)
    }
  }

  updateChart(chart, newData) {
    if (!chart || !newData || !Array.isArray(newData)) return

    chart.data.labels = newData.map((item) => item.nombre || "Sin nombre")
    chart.data.datasets[0].data = newData.map((item) => item.cantidad || 0)
    chart.update("none")
  }

  updateLastUpdateTime() {
    const now = new Date()
    const timeString = now.toLocaleString("es-ES")
    const lastUpdateElement = document.getElementById("last-update")
    if (lastUpdateElement) {
      lastUpdateElement.textContent = timeString
    }
  }

  async refreshDashboard() {
    console.log("ðŸ”„ Iniciando actualizaciÃ³n manual del dashboard...")

    const refreshIcon = document.querySelector("[data-refresh-dashboard] i")
    if (refreshIcon) {
      refreshIcon.classList.add("fa-spin")
    }

    try {
      // Ejecutar actualizaciones en paralelo
      await Promise.all([this.updateDashboardStats(), this.updateRecentData()])

      this.showNotification("Dashboard actualizado correctamente", "success")
      console.log("âœ… Dashboard actualizado exitosamente")
    } catch (error) {
      console.error("âŒ Error al actualizar dashboard:", error)
      this.showNotification("Error al actualizar dashboard: " + error.message, "error")
    } finally {
      setTimeout(() => {
        if (refreshIcon) {
          refreshIcon.classList.remove("fa-spin")
        }
      }, 1000)
    }
  }

  async updateRecentData() {
    try {
      if (!window.NEXO || !window.NEXO.urls || !window.NEXO.urls.recent_data) {
        throw new Error("URL de datos recientes no disponible")
      }

      const response = await this.makeRequest(window.NEXO.urls.recent_data)

      if (response.success) {
        this.updateRecentDataUI(response.data)
        console.log("âœ… Datos recientes actualizados")
      } else {
        throw new Error(response.error || "Error desconocido")
      }
    } catch (error) {
      console.error("âŒ Error actualizando datos recientes:", error)
    }
  }

  updateRecentDataUI(data) {
    // Actualizar tabla de entradas recientes
    this.updateTable("entradas-recientes", data.entradas_recientes, [
      { key: "fecha", label: "Fecha" },
      { key: "descripcion", label: "DescripciÃ³n" },
      { key: "usuario", label: "Usuario" },
    ])

    // Actualizar tabla de ventas recientes
    this.updateTable("ventas-recientes", data.ventas_recientes, [
      { key: "fecha", label: "Fecha" },
      { key: "total", label: "Total", format: "currency" },
      { key: "usuario", label: "Usuario" },
    ])
  }

  updateTable(tableId, data, columns) {
    const tbody = document.getElementById(tableId)
    if (!tbody) return

    tbody.innerHTML = ""

    if (data && data.length > 0) {
      data.forEach((row) => {
        const tr = document.createElement("tr")
        tr.className = "hover:bg-gray-50 transition-colors duration-200"

        columns.forEach((column) => {
          const td = document.createElement("td")
          td.className = "py-3 px-4 text-sm"

          let value = row[column.key] || "N/A"

          // Formatear valor segÃºn el tipo
          if (column.format === "currency" && typeof value === "number") {
            value = `C$ ${value.toFixed(2)}`
          }

          td.textContent = value
          tr.appendChild(td)
        })

        tbody.appendChild(tr)
      })
    } else {
      const tr = document.createElement("tr")
      const td = document.createElement("td")
      td.colSpan = columns.length
      td.className = "py-8 text-center text-gray-500"
      td.innerHTML = `
                <div class="flex flex-col items-center">
                    <i class="fas fa-inbox text-3xl mb-2 opacity-50"></i>
                    <span>No hay datos disponibles</span>
                </div>
            `
      tr.appendChild(td)
      tbody.appendChild(tr)
    }
  }

  async makeRequest(url, options = {}) {
    const defaultOptions = {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": this.getCSRFToken(),
      },
    }

    const finalOptions = { ...defaultOptions, ...options }

    try {
      console.log(`ðŸŒ Realizando peticiÃ³n a: ${url}`)
      const response = await fetch(url, finalOptions)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log(`âœ… Respuesta recibida:`, data)
      return data
    } catch (error) {
      console.error("âŒ Error en peticiÃ³n:", error)
      throw error
    }
  }

  getCSRFToken() {
    const token = document.querySelector("[name=csrfmiddlewaretoken]")
    return token ? token.value : window.NEXO?.csrf_token || ""
  }

  showNotification(message, type = "info", duration = null) {
    duration = duration || NEXO_CONFIG.notification_duration

    const notification = document.createElement("div")
    notification.className = `fixed p-4 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 translate-x-full`
    notification.style.top = "6rem"
    notification.style.right = "1rem"
    notification.style.zIndex = "9999"

    const bgColor = type === "success" ? "bg-green-500" : type === "error" ? "bg-red-500" : "bg-blue-500"
    notification.classList.add(bgColor, "text-white")

    notification.innerHTML = `
            <div class="flex items-center space-x-2">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
        `

    document.body.appendChild(notification)

    // Mostrar notificaciÃ³n
    setTimeout(() => {
      notification.classList.remove("translate-x-full")
    }, 100)

    // Auto-remover despuÃ©s del tiempo especificado
    setTimeout(() => {
      notification.classList.add("translate-x-full")
      setTimeout(() => {
        if (notification.parentElement) {
          notification.remove()
        }
      }, 300)
    }, duration)
  }

  destroy() {
    // Limpiar timers
    this.stopRealTimeUpdates()

    // Destruir grÃ¡ficos
    Object.values(this.charts).forEach((chart) => {
      if (chart && typeof chart.destroy === "function") {
        chart.destroy()
      }
    })

    console.log("ðŸ§¹ NEXO Dashboard destruido correctamente")
  }
}

// ===== FUNCIONES GLOBALES =====
function refreshDashboard() {
  console.log("ðŸ”„ FunciÃ³n global refreshDashboard llamada")
  if (window.nexoDashboard) {
    window.nexoDashboard.refreshDashboard()
  } else {
    console.error("âŒ Dashboard no inicializado")
  }
}

// ===== INICIALIZACIÃ“N =====
document.addEventListener("DOMContentLoaded", () => {
  console.log("ðŸš€ DOM cargado, inicializando dashboard...")

  // Verificar dependencias
  if (typeof Chart === "undefined") {
    console.warn("âš ï¸ Chart.js no estÃ¡ disponible")
  }

  // Inicializar dashboard
  window.nexoDashboard = new NexoDashboard()

  console.log("ðŸŽ‰ Sistema NEXO completamente inicializado")
})

// Limpiar recursos al salir de la pÃ¡gina
window.addEventListener("beforeunload", () => {
  if (window.nexoDashboard) {
    window.nexoDashboard.destroy()
  }
})


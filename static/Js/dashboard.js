

// ===== CONFIGURACIÓN GLOBAL =====
const NEXO_CONFIG = {
  refresh_interval: 30000, // Intervalo de actualización automática (30 segundos)
  chart_animation_duration: 1000, // Duración de animaciones de gráficos
  notification_duration: 5000, // Duración de notificaciones
  chart_colors: [
    "#4ECDC4", // Color primario NEXO
    "#f2ce16", // Amarillo secundario
    "#f28627", // Naranja
    "#39bfb2", // Verde azulado oscuro
    "#f29d35", // Naranja claro
    "#10b981", // Verde éxito
    "#3b82f6", // Azul
    "#8b5cf6", // Púrpura
    "#ef4444", // Rojo error
    "#06b6d4", // Cian
  ],
}

// ===== CLASE PRINCIPAL DEL DASHBOARD =====
class NexoDashboard {
  constructor() {
    this.charts = {} // Almacena las instancias de gráficos
    this.updateTimers = {} // Almacena los timers de actualización
    this.isUpdating = false // Flag para evitar actualizaciones simultáneas

    this.init()
  }

  async init() {
    console.log("🚀 Inicializando NEXO Dashboard...")

    try {
      // Configurar Chart.js si está disponible
      this.setupChartDefaults()

      // Inicializar gráficos
      await this.initCharts()

      // Configurar event listeners
      this.setupEventListeners()

      // Iniciar actualizaciones automáticas
      this.startRealTimeUpdates()

      console.log("✅ NEXO Dashboard inicializado correctamente")
    } catch (error) {
      console.error("❌ Error inicializando dashboard:", error)
      this.showNotification("Error al inicializar el dashboard", "error")
    }
  }

  setupChartDefaults() {
    // Configuración global de Chart.js si está disponible
    if (typeof Chart !== "undefined") {
      Chart.defaults.font.family = "Inter, system-ui, sans-serif"
      Chart.defaults.color = "#6b7280"
      Chart.defaults.plugins.legend.display = false
    }
  }

  async initCharts() {
    try {
      // Verificar que Chart.js esté disponible
      if (typeof Chart === "undefined") {
        console.warn("⚠️ Chart.js no está disponible")
        return
      }

      // Inicializar gráfico de productos más vendidos
      await this.createProductosVendidosChart()

      // Inicializar gráfico de productos más devueltos
      await this.createProductosDevueltosChart()

      console.log("📊 Gráficos inicializados correctamente")
    } catch (error) {
      console.error("❌ Error inicializando gráficos:", error)
    }
  }

  async createProductosVendidosChart() {
    const canvas = document.getElementById("productos-vendidos-chart")
    if (!canvas || typeof Chart === "undefined") return

    const ctx = canvas.getContext("2d")

    // Datos por defecto si no hay datos del servidor
    let data = [
      { nombre: "Monedero", cantidad: 45 },
      { nombre: "Bolso", cantidad: 32 },
      { nombre: "Cartera", cantidad: 28 },
      { nombre: "Billetera", cantidad: 20 },
      { nombre: "Mochila", cantidad: 15 },
    ]

    // Usar datos del servidor si están disponibles
    if (window.chartDataByLocation && typeof window.chartDataByLocation === "object") {
      const allLocations = Object.values(window.chartDataByLocation)
      if (
        allLocations.length > 0 &&
        allLocations[0].productos_mas_vendidos &&
        allLocations[0].productos_mas_vendidos.length > 0
      ) {
        data = allLocations[0].productos_mas_vendidos
      }
    }

    // Destruir gráfico existente si existe
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
            hoverBorderWidth: 3,
            hoverOffset: 10,
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
          animateRotate: true,
          duration: NEXO_CONFIG.chart_animation_duration,
          easing: "easeOutQuart",
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

    // Datos por defecto si no hay datos del servidor
    let data = [
      { nombre: "Monedero", cantidad: 8 },
      { nombre: "Bolso", cantidad: 5 },
      { nombre: "Cartera", cantidad: 3 },
      { nombre: "Billetera", cantidad: 2 },
      { nombre: "Mochila", cantidad: 1 },
    ]

    // Usar datos del servidor si están disponibles
    if (window.chartDataByLocation && typeof window.chartDataByLocation === "object") {
      const allLocations = Object.values(window.chartDataByLocation)
      if (
        allLocations.length > 0 &&
        allLocations[0].productos_mas_devueltos &&
        allLocations[0].productos_mas_devueltos.length > 0
      ) {
        data = allLocations[0].productos_mas_devueltos
      }
    }

    // Destruir gráfico existente si existe
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
            hoverBorderWidth: 3,
            hoverOffset: 10,
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
          animateRotate: true,
          duration: NEXO_CONFIG.chart_animation_duration,
          easing: "easeOutQuart",
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

  setupEventListeners() {
    // Listener para botón de actualizar
    const refreshButton = document.querySelector("[data-refresh-dashboard]")
    if (refreshButton) {
      refreshButton.addEventListener("click", (e) => {
        e.preventDefault()
        e.stopPropagation()
        this.refreshDashboard()
      })
    }

    // Listener para cambios de visibilidad de la página
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        this.stopRealTimeUpdates()
      } else {
        this.startRealTimeUpdates()
        this.updateDashboardStats()
      }
    })

    // Listeners para conexión de red
    window.addEventListener("online", () => {
      this.showNotification("Conexión restaurada", "success")
      this.startRealTimeUpdates()
    })

    window.addEventListener("offline", () => {
      this.showNotification("Sin conexión a internet", "error")
      this.stopRealTimeUpdates()
    })
  }

  startRealTimeUpdates() {
    // Limpiar timers existentes
    this.stopRealTimeUpdates()

    // Actualizar estadísticas cada 30 segundos
    this.updateTimers.stats = setInterval(() => {
      this.updateDashboardStats()
    }, NEXO_CONFIG.refresh_interval)

    console.log("🔄 Actualizaciones automáticas iniciadas")
  }

  stopRealTimeUpdates() {
    Object.values(this.updateTimers).forEach((timer) => {
      clearInterval(timer)
    })
    this.updateTimers = {}
    console.log("⏹️ Actualizaciones automáticas detenidas")
  }

  async updateDashboardStats() {
    if (this.isUpdating) {
      console.log("⏳ Actualización ya en progreso, saltando...")
      return
    }

    this.isUpdating = true
    console.log("🔄 Iniciando actualización de estadísticas...")

    try {
      // Verificar que las URLs estén disponibles
      if (!window.NEXO || !window.NEXO.urls || !window.NEXO.urls.dashboard_stats) {
        throw new Error("URLs de API no disponibles")
      }

      const response = await this.makeRequest(window.NEXO.urls.dashboard_stats)

      if (response.success) {
        console.log("✅ Datos actualizados correctamente:", response.data)

        // Actualizar métricas con animación
        this.updateStatsUI(response.data.metrics)

        // Actualizar gráficos
        this.updateCharts(response.data.chart_data_by_location)

        // Actualizar timestamp
        this.updateLastUpdateTime()

        this.showNotification("Estadísticas actualizadas", "success", 2000)
      } else {
        throw new Error(response.error || "Error desconocido")
      }
    } catch (error) {
      console.error("❌ Error actualizando estadísticas:", error)
      this.showNotification("Error al actualizar estadísticas: " + error.message, "error")
    } finally {
      this.isUpdating = false
    }
  }

  updateStatsUI(metrics) {
    // Actualizar métricas principales con animación
    const metricsMap = {
      "total-productos": metrics.total_productos,
      "total-clientes": metrics.total_clientes,
      "ventas-mes": metrics.ventas_mes,
      "productos-bajo-stock": metrics.productos_bajo_stock,
    }

    Object.keys(metricsMap).forEach((key) => {
      const element = document.getElementById(key)
      if (element && typeof metricsMap[key] === "number") {
        this.animateCounterUpdate(element, metricsMap[key])
      }
    })
  }

  animateCounterUpdate(element, newValue) {
    const currentValue = Number.parseInt(element.textContent) || 0
    const increment = (newValue - currentValue) / 20
    let current = currentValue

    const timer = setInterval(() => {
      current += increment
      if ((increment > 0 && current >= newValue) || (increment < 0 && current <= newValue)) {
        current = newValue
        clearInterval(timer)
      }
      element.textContent = Math.round(current)
    }, 50)
  }

  updateCharts(chartData) {
    if (!chartData || typeof chartData !== "object") {
      console.log("📊 No hay datos de gráficos para actualizar")
      return
    }

    console.log("📊 Actualizando gráficos con datos:", chartData)

    // Actualizar gráfico de productos más vendidos
    const allLocations = Object.values(chartData)
    if (allLocations.length > 0) {
      if (this.charts.productosVendidos && allLocations[0].productos_mas_vendidos) {
        this.updateChart(this.charts.productosVendidos, allLocations[0].productos_mas_vendidos)
        this.createCustomLegend(
          "productos-vendidos-legend",
          allLocations[0].productos_mas_vendidos,
          NEXO_CONFIG.chart_colors,
        )
      }

      if (this.charts.productosDevueltos && allLocations[0].productos_mas_devueltos) {
        this.updateChart(this.charts.productosDevueltos, allLocations[0].productos_mas_devueltos)
        this.createCustomLegend(
          "productos-devueltos-legend",
          allLocations[0].productos_mas_devueltos,
          NEXO_CONFIG.chart_colors,
        )
      }
    }
  }

  updateChart(chart, newData) {
    if (!chart || !newData || !Array.isArray(newData)) return

    chart.data.labels = newData.map((item) => item.nombre || "Sin nombre")
    chart.data.datasets[0].data = newData.map((item) => item.cantidad || 0)
    chart.update("active")
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
    console.log("🔄 Iniciando actualización manual del dashboard...")

    const refreshIcon = document.querySelector("[data-refresh-dashboard] i")
    if (refreshIcon) {
      refreshIcon.classList.add("fa-spin")
    }

    try {
      // Ejecutar actualizaciones en paralelo
      await Promise.all([this.updateDashboardStats(), this.updateRecentData()])

      this.showNotification("Dashboard actualizado correctamente", "success")
      console.log("✅ Dashboard actualizado exitosamente")
    } catch (error) {
      console.error("❌ Error al actualizar dashboard:", error)
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
        console.log("✅ Datos recientes actualizados")
      } else {
        throw new Error(response.error || "Error desconocido")
      }
    } catch (error) {
      console.error("❌ Error actualizando datos recientes:", error)
    }
  }

  updateRecentDataUI(data) {
    // Actualizar tabla de entradas recientes
    this.updateTable("entradas-recientes", data.entradas_recientes, [
      { key: "fecha", label: "Fecha" },
      { key: "descripcion", label: "Descripción" },
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

          // Formatear valor según el tipo
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
      console.log(`🌐 Realizando petición a: ${url}`)
      const response = await fetch(url, finalOptions)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log(`✅ Respuesta recibida:`, data)
      return data
    } catch (error) {
      console.error("❌ Error en petición:", error)
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
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 translate-x-full`

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

    // Mostrar notificación
    setTimeout(() => {
      notification.classList.remove("translate-x-full")
    }, 100)

    // Auto-remover después del tiempo especificado
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

    // Destruir gráficos
    Object.values(this.charts).forEach((chart) => {
      if (chart && typeof chart.destroy === "function") {
        chart.destroy()
      }
    })

    console.log("🧹 NEXO Dashboard destruido correctamente")
  }
}

// ===== FUNCIONES GLOBALES =====
function refreshDashboard() {
  console.log("🔄 Función global refreshDashboard llamada")
  if (window.nexoDashboard) {
    window.nexoDashboard.refreshDashboard()
  } else {
    console.error("❌ Dashboard no inicializado")
  }
}

// ===== INICIALIZACIÓN =====
document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 DOM cargado, inicializando dashboard...")

  // Verificar dependencias
  if (typeof Chart === "undefined") {
    console.warn("⚠️ Chart.js no está disponible")
  }

  // Inicializar dashboard
  window.nexoDashboard = new NexoDashboard()

  console.log("🎉 Sistema NEXO completamente inicializado")
})

// Limpiar recursos al salir de la página
window.addEventListener("beforeunload", () => {
  if (window.nexoDashboard) {
    window.nexoDashboard.destroy()
  }
})

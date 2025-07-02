/**
 * NEXO - Sistema de Gestión de Inventario
 * Scripts JavaScript personalizados
 */

// Configuración global
const NEXO = {
  config: {
    animationDuration: 300,
    toastDuration: 5000,
    ajaxTimeout: 30000,
  },

  // Inicialización del sistema
  init: function () {
    this.setupEventListeners()
    this.initializeComponents()
    this.setupAjaxDefaults()
    console.log("NEXO System initialized successfully")
  },

  // Configurar event listeners globales
  setupEventListeners: () => {
    // Confirmar acciones peligrosas
    document.addEventListener("click", (e) => {
      if (e.target.classList.contains("nexo-confirm-action")) {
        e.preventDefault()
        NEXO.confirmAction(e.target)
      }
    })

    // Auto-submit de formularios de filtros
    document.addEventListener("change", (e) => {
      if (e.target.classList.contains("nexo-auto-submit")) {
        e.target.closest("form").submit()
      }
    })

    // Tooltips automáticos
    document.addEventListener("DOMContentLoaded", () => {
      NEXO.initializeTooltips()
    })
  },

  // Inicializar componentes
  initializeComponents: function () {
    // Inicializar tooltips de Bootstrap
    this.initializeTooltips()

    // Inicializar popovers
    this.initializePopovers()

    // Configurar tablas responsivas
    this.setupResponsiveTables()

    // Configurar animaciones de entrada
    this.setupAnimations()
  },

  // Configurar AJAX por defecto
  setupAjaxDefaults: () => {
    // Configurar CSRF token para Django
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")
    if (csrfToken) {
      // Configurar headers AJAX si se usa jQuery
      const $ = window.jQuery // Declare the jQuery variable
      if (typeof $ !== "undefined") {
        $.ajaxSetup({
          beforeSend: function (xhr, settings) {
            if (!this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrfToken.value)
            }
          },
        })
      }
    }
  },

  // Inicializar tooltips
  initializeTooltips: () => {
    const bootstrap = window.bootstrap // Declare the bootstrap variable
    if (typeof bootstrap !== "undefined") {
      const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
      tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl))
    }
  },

  // Inicializar popovers
  initializePopovers: () => {
    const bootstrap = window.bootstrap // Declare the bootstrap variable
    if (typeof bootstrap !== "undefined") {
      const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
      popoverTriggerList.map((popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl))
    }
  },

  // Configurar tablas responsivas
  setupResponsiveTables: () => {
    const tables = document.querySelectorAll(".nexo-table")
    tables.forEach((table) => {
      if (!table.closest(".table-responsive")) {
        const wrapper = document.createElement("div")
        wrapper.className = "table-responsive"
        table.parentNode.insertBefore(wrapper, table)
        wrapper.appendChild(table)
      }
    })
  },

  // Configurar animaciones
  setupAnimations: () => {
    // Observador de intersección para animaciones de entrada
    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("nexo-fade-in")
            observer.unobserve(entry.target)
          }
        })
      })

      // Observar elementos con clase de animación
      document.querySelectorAll(".nexo-animate-on-scroll").forEach((el) => {
        observer.observe(el)
      })
    }
  },

  // Confirmar acciones
  confirmAction: (element) => {
    const message = element.getAttribute("data-confirm-message") || "¿Estás seguro de que deseas realizar esta acción?"
    const title = element.getAttribute("data-confirm-title") || "Confirmar Acción"

    const Swal = window.Swal // Declare the Swal variable
    if (typeof Swal !== "undefined") {
      // Usar SweetAlert2 si está disponible
      Swal.fire({
        title: title,
        text: message,
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#39bfb2",
        cancelButtonColor: "#F28627",
        confirmButtonText: "Sí, continuar",
        cancelButtonText: "Cancelar",
      }).then((result) => {
        if (result.isConfirmed) {
          if (element.tagName === "A") {
            window.location.href = element.href
          } else if (element.tagName === "BUTTON") {
            element.closest("form").submit()
          }
        }
      })
    } else {
      // Usar confirm nativo como fallback
      if (confirm(message)) {
        if (element.tagName === "A") {
          window.location.href = element.href
        } else if (element.tagName === "BUTTON") {
          element.closest("form").submit()
        }
      }
    }
  },

  // Mostrar notificaciones
  showNotification: function (message, type = "info", duration = null) {
    duration = duration || this.config.toastDuration

    const Swal = window.Swal // Declare the Swal variable
    if (typeof Swal !== "undefined") {
      // Usar SweetAlert2 toast
      const Toast = Swal.mixin({
        toast: true,
        position: "top-end",
        showConfirmButton: false,
        timer: duration,
        timerProgressBar: true,
        didOpen: (toast) => {
          toast.addEventListener("mouseenter", Swal.stopTimer)
          toast.addEventListener("mouseleave", Swal.resumeTimer)
        },
      })

      Toast.fire({
        icon: type,
        title: message,
      })
    } else {
      // Crear notificación personalizada
      this.createCustomNotification(message, type, duration)
    }
  },

  // Crear notificación personalizada
  createCustomNotification: function (message, type, duration) {
    const notification = document.createElement("div")
    notification.className = `alert alert-${type} nexo-notification`
    notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${this.getIconForType(type)} me-2"></i>
                <span>${message}</span>
                <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `

    // Agregar estilos
    notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        `

    document.body.appendChild(notification)

    // Auto-remover después del tiempo especificado
    setTimeout(() => {
      if (notification.parentNode) {
        notification.remove()
      }
    }, duration)
  },

  // Obtener icono según el tipo de notificación
  getIconForType: (type) => {
    const icons = {
      success: "check-circle",
      error: "exclamation-circle",
      warning: "exclamation-triangle",
      info: "info-circle",
    }
    return icons[type] || "info-circle"
  },

  // Utilidades para formularios
  form: {
    // Validar formulario
    validate: (formElement) => {
      const requiredFields = formElement.querySelectorAll("[required]")
      let isValid = true

      requiredFields.forEach((field) => {
        if (!field.value.trim()) {
          field.classList.add("is-invalid")
          isValid = false
        } else {
          field.classList.remove("is-invalid")
        }
      })

      return isValid
    },

    // Limpiar formulario
    reset: (formElement) => {
      formElement.reset()
      formElement.querySelectorAll(".is-invalid").forEach((field) => {
        field.classList.remove("is-invalid")
      })
    },

    // Serializar formulario a objeto
    serialize: (formElement) => {
      const formData = new FormData(formElement)
      const data = {}

      for (const [key, value] of formData.entries()) {
        if (data[key]) {
          if (Array.isArray(data[key])) {
            data[key].push(value)
          } else {
            data[key] = [data[key], value]
          }
        } else {
          data[key] = value
        }
      }

      return data
    },
  },

  // Utilidades para tablas
  table: {
    // Filtrar tabla
    filter: (tableElement, searchTerm) => {
      const rows = tableElement.querySelectorAll("tbody tr")
      const term = searchTerm.toLowerCase()

      rows.forEach((row) => {
        const text = row.textContent.toLowerCase()
        if (text.includes(term)) {
          row.style.display = ""
        } else {
          row.style.display = "none"
        }
      })
    },

    // Ordenar tabla
    sort: (tableElement, columnIndex, direction = "asc") => {
      const tbody = tableElement.querySelector("tbody")
      const rows = Array.from(tbody.querySelectorAll("tr"))

      rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim()
        const bText = b.cells[columnIndex].textContent.trim()

        // Intentar comparar como números
        const aNum = Number.parseFloat(aText)
        const bNum = Number.parseFloat(bText)

        if (!isNaN(aNum) && !isNaN(bNum)) {
          return direction === "asc" ? aNum - bNum : bNum - aNum
        } else {
          return direction === "asc" ? aText.localeCompare(bText) : bText.localeCompare(aText)
        }
      })

      // Reordenar filas en el DOM
      rows.forEach((row) => {
        tbody.appendChild(row)
      })
    },
  },

  // Utilidades para exportación
  export: {
    // Exportar tabla a CSV
    tableToCSV: function (tableElement, filename = "export.csv") {
      const rows = tableElement.querySelectorAll("tr")
      const csvContent = []

      rows.forEach((row) => {
        const cols = row.querySelectorAll("td, th")
        const rowData = []

        cols.forEach((col) => {
          rowData.push('"' + col.textContent.trim().replace(/"/g, '""') + '"')
        })

        csvContent.push(rowData.join(","))
      })

      const csvString = csvContent.join("\n")
      this.downloadFile(csvString, filename, "text/csv")
    },

    // Descargar archivo
    downloadFile: (content, filename, mimeType) => {
      const blob = new Blob([content], { type: mimeType })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")

      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    },
  },

  // Utilidades de formato
  format: {
    // Formatear número como moneda
    currency: (amount, currency = "USD") =>
      new Intl.NumberFormat("es-NI", {
        style: "currency",
        currency: currency,
      }).format(amount),

    // Formatear fecha
    date: (date, options = {}) => {
      const defaultOptions = {
        year: "numeric",
        month: "long",
        day: "numeric",
      }

      return new Intl.DateTimeFormat("es-NI", {
        ...defaultOptions,
        ...options,
      }).format(new Date(date))
    },

    // Formatear número
    number: (number, decimals = 2) =>
      new Intl.NumberFormat("es-NI", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(number),
  },
}

// Inicializar el sistema cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", () => {
  NEXO.init()
})

// Exponer NEXO globalmente
window.NEXO = NEXO

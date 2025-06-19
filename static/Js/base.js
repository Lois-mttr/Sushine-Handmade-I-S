// ===== NAMESPACE GLOBAL DEL SISTEMA =====
window.NEXO = window.NEXO || {}

// ===== CONFIGURACIÓN GLOBAL =====
NEXO.config = {
  // URLs de la API
  apiUrls: {
    login: "/login/",
    logout: "/logout/",
    checkSession: "/check-session/",
  },

  // Configuración de notificaciones
  notifications: {
    duration: 5000,
    maxVisible: 5,
  },

  // Configuración de validación
  validation: {
    minPasswordLength: 6,
    maxUsernameLength: 15,
  },

  // Configuración de seguridad
  security: {
    maxLoginAttempts: 3,
    lockoutDuration: 20000, // 20 segundos en milisegundos
    sessionCheckInterval: 300000, // 5 minutos
  },
}

// ===== UTILIDADES GENERALES =====
NEXO.utils = {
  /**
   * Mostrar notificación al usuario
   * @param {string} message - Mensaje a mostrar
   * @param {string} type - Tipo de notificación (success, error, warning, info)
   * @param {number} duration - Duración en milisegundos (opcional)
   */
  showNotification: function (message, type = "info", duration = null) {
    const container = document.getElementById("notificationsContainer")
    if (!container) {
      console.warn("Contenedor de notificaciones no encontrado")
      return
    }

    // Usar duración por defecto si no se especifica
    duration = duration || NEXO.config.notifications.duration

    // Crear elemento de notificación
    const notification = document.createElement("div")
    notification.className = `notification ${type}`
    notification.textContent = message
    notification.setAttribute("role", "alert")
    notification.setAttribute("aria-live", "polite")

    // Agregar al contenedor
    container.appendChild(notification)

    // Limitar número de notificaciones visibles
    this.limitVisibleNotifications(container)

    // Auto-remover después del tiempo especificado
    setTimeout(() => {
      this.removeNotification(notification)
    }, duration)
  },

  /**
   * Remover notificación con animación
   * @param {HTMLElement} notification - Elemento de notificación a remover
   */
  removeNotification: (notification) => {
    if (notification && notification.parentNode) {
      notification.style.opacity = "0"
      notification.style.transform = "translateX(100%)"

      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove()
        }
      }, 300)
    }
  },

  /**
   * Limitar número de notificaciones visibles
   * @param {HTMLElement} container - Contenedor de notificaciones
   */
  limitVisibleNotifications: function (container) {
    const notifications = container.querySelectorAll(".notification")
    const maxVisible = NEXO.config.notifications.maxVisible

    if (notifications.length > maxVisible) {
      // Remover las notificaciones más antiguas
      for (let i = 0; i < notifications.length - maxVisible; i++) {
        this.removeNotification(notifications[i])
      }
    }
  },

  /**
   * Validar campo de formulario
   * @param {HTMLElement} field - Campo a validar
   * @param {string} fieldName - Nombre del campo para mensajes de error
   * @param {Object} rules - Reglas de validación
   * @returns {boolean} - True si es válido, false si no
   */
  validateField: function (field, fieldName, rules = {}) {
    const value = field.value.trim()
    const errorElement = document.getElementById(`${field.id}-error`)

    // Limpiar errores previos
    this.clearFieldError(field, errorElement)

    // Validar campo requerido
    if (rules.required && !value) {
      this.showFieldError(field, errorElement, `${fieldName} es obligatorio`)
      return false
    }

    // Validar longitud mínima
    if (rules.minLength && value.length < rules.minLength) {
      this.showFieldError(field, errorElement, `${fieldName} debe tener al menos ${rules.minLength} caracteres`)
      return false
    }

    // Validar longitud máxima
    if (rules.maxLength && value.length > rules.maxLength) {
      this.showFieldError(field, errorElement, `${fieldName} no puede tener más de ${rules.maxLength} caracteres`)
      return false
    }

    // Validar patrón
    if (rules.pattern && !rules.pattern.test(value)) {
      this.showFieldError(field, errorElement, rules.patternMessage || `${fieldName} tiene un formato inválido`)
      return false
    }

    return true
  },

  /**
   * Mostrar error en campo específico
   * @param {HTMLElement} field - Campo con error
   * @param {HTMLElement} errorElement - Elemento para mostrar el error
   * @param {string} message - Mensaje de error
   */
  showFieldError: (field, errorElement, message) => {
    field.classList.add("error")
    if (errorElement) {
      errorElement.textContent = message
      errorElement.classList.add("show")
    }
  },

  /**
   * Limpiar error en campo específico
   * @param {HTMLElement} field - Campo a limpiar
   * @param {HTMLElement} errorElement - Elemento de error a limpiar
   */
  clearFieldError: (field, errorElement) => {
    field.classList.remove("error")
    if (errorElement) {
      errorElement.textContent = ""
      errorElement.classList.remove("show")
    }
  },

  /**
   * Hacer shake a un elemento
   * @param {HTMLElement} element - Elemento a animar
   */
  shakeElement: (element) => {
    element.classList.add("shake")
    setTimeout(() => {
      element.classList.remove("shake")
    }, 500)
  },

  /**
   * Formatear tiempo en formato MM:SS
   * @param {number} seconds - Segundos a formatear
   * @returns {string} - Tiempo formateado
   */
  formatTime: (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  },

  /**
   * Debounce function para limitar ejecución de funciones
   * @param {Function} func - Función a ejecutar
   * @param {number} wait - Tiempo de espera en milisegundos
   * @returns {Function} - Función debounced
   */
  debounce: (func, wait) => {
    let timeout
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout)
        func(...args)
      }
      clearTimeout(timeout)
      timeout = setTimeout(later, wait)
    }
  },

  /**
   * Throttle function para limitar ejecución de funciones
   * @param {Function} func - Función a ejecutar
   * @param {number} limit - Límite de tiempo en milisegundos
   * @returns {Function} - Función throttled
   */
  throttle: (func, limit) => {
    let inThrottle
    return function () {
      const args = arguments
      
      if (!inThrottle) {
        func.apply(this, args)
        inThrottle = true
        setTimeout(() => (inThrottle = false), limit)
      }
    }
  },

  /**
   * Obtener token CSRF de Django
   * @returns {string} - Token CSRF
   */
  getCSRFToken: () => {
    const token = document.querySelector("[name=csrfmiddlewaretoken]")
    return token ? token.value : ""
  },

  /**
   * Realizar petición AJAX con manejo de errores
   * @param {string} url - URL de la petición
   * @param {Object} options - Opciones de la petición
   * @returns {Promise} - Promesa de la petición
   */
  ajax: function (url, options = {}) {
    const defaultOptions = {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": this.getCSRFToken(),
        "X-Requested-With": "XMLHttpRequest",
      },
    }

    const finalOptions = { ...defaultOptions, ...options }

    return fetch(url, finalOptions)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        return response.json()
      })
      .catch((error) => {
        console.error("Error en petición AJAX:", error)
        this.showNotification("Error de conexión. Intenta nuevamente.", "error")
        throw error
      })
  },
}

// ===== GESTIÓN DE SESIONES =====
NEXO.session = {
  /**
   * Verificar estado de la sesión
   */
  checkSession: function () {
    return NEXO.utils
      .ajax(NEXO.config.apiUrls.checkSession)
      .then((data) => {
        if (!data.authenticated) {
          this.handleSessionExpired()
        }
        return data
      })
      .catch((error) => {
        console.error("Error al verificar sesión:", error)
      })
  },

  /**
   * Manejar sesión expirada
   */
  handleSessionExpired: () => {
    NEXO.utils.showNotification("Tu sesión ha expirado. Redirigiendo al login...", "warning")
    setTimeout(() => {
      window.location.href = NEXO.config.apiUrls.login
    }, 2000)
  },

  /**
   * Iniciar verificación periódica de sesión
   */
  startSessionCheck: function () {
    setInterval(() => {
      this.checkSession()
    }, NEXO.config.security.sessionCheckInterval)
  },
}

// ===== GESTIÓN DE ALMACENAMIENTO LOCAL =====
NEXO.storage = {
  /**
   * Guardar datos en localStorage con manejo de errores
   * @param {string} key - Clave del dato
   * @param {*} value - Valor a guardar
   */
  set: (key, value) => {
    try {
      localStorage.setItem(`nexo_${key}`, JSON.stringify(value))
    } catch (error) {
      console.error("Error al guardar en localStorage:", error)
    }
  },

  /**
   * Obtener datos de localStorage
   * @param {string} key - Clave del dato
   * @param {*} defaultValue - Valor por defecto si no existe
   * @returns {*} - Valor almacenado o valor por defecto
   */
  get: (key, defaultValue = null) => {
    try {
      const item = localStorage.getItem(`nexo_${key}`)
      return item ? JSON.parse(item) : defaultValue
    } catch (error) {
      console.error("Error al leer de localStorage:", error)
      return defaultValue
    }
  },

  /**
   * Remover dato de localStorage
   * @param {string} key - Clave del dato a remover
   */
  remove: (key) => {
    try {
      localStorage.removeItem(`nexo_${key}`)
    } catch (error) {
      console.error("Error al remover de localStorage:", error)
    }
  },

  /**
   * Limpiar todos los datos de NEXO de localStorage
   */
  clear: () => {
    try {
      Object.keys(localStorage).forEach((key) => {
        if (key.startsWith("nexo_")) {
          localStorage.removeItem(key)
        }
      })
    } catch (error) {
      console.error("Error al limpiar localStorage:", error)
    }
  },
}

// ===== INICIALIZACIÓN =====
document.addEventListener("DOMContentLoaded", () => {
  // Inicializar verificación de sesión si no estamos en la página de login
  if (!window.location.pathname.includes("/login/")) {
    NEXO.session.startSessionCheck()
  }

  // Manejar errores globales de JavaScript
  window.addEventListener("error", (event) => {
    console.error("Error global capturado:", event.error)
    // En producción, aquí se podría enviar el error a un servicio de logging
  })

  // Manejar promesas rechazadas no capturadas
  window.addEventListener("unhandledrejection", (event) => {
    console.error("Promesa rechazada no capturada:", event.reason)
    // En producción, aquí se podría enviar el error a un servicio de logging
  })

  console.log("Sistema NEXO inicializado correctamente")
})

// ===== EXPORTAR PARA USO GLOBAL =====
window.NEXO = NEXO

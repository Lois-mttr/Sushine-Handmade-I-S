// Sidebar JavaScript - Menú interactivo
document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("sidebar")
  const sidebarToggle = document.getElementById("sidebar-toggle")
  const sidebarToggleBtn = document.getElementById("sidebar-toggle-btn")
  const sidebarOverlay = document.getElementById("sidebar-overlay")
  const mainContent = document.getElementById("main-content")

  // Función para alternar el sidebar
  function toggleSidebar() {
    if (window.innerWidth <= 768) {
      // Móvil: mostrar/ocultar con overlay
      sidebar.classList.toggle("active")
      sidebarOverlay.classList.toggle("active")
      document.body.style.overflow = sidebar.classList.contains("active") ? "hidden" : ""
    } else {
      // Desktop: colapsar/expandir
      sidebar.classList.toggle("collapsed")
      localStorage.setItem("sidebarCollapsed", sidebar.classList.contains("collapsed"))
    }
  }

  // Event listeners para los botones de toggle
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", toggleSidebar)
  }

  if (sidebarToggleBtn) {
    sidebarToggleBtn.addEventListener("click", toggleSidebar)
  }

  // Cerrar sidebar al hacer click en el overlay (móvil)
  if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", () => {
      sidebar.classList.remove("active")
      sidebarOverlay.classList.remove("active")
      document.body.style.overflow = ""
    })
  }

  // Restaurar estado del sidebar desde localStorage
  if (window.innerWidth > 768) {
    const sidebarCollapsed = localStorage.getItem("sidebarCollapsed") === "true"
    if (sidebarCollapsed) {
      sidebar.classList.add("collapsed")
    }
  }

  // Manejar redimensionamiento de ventana
  window.addEventListener("resize", () => {
    if (window.innerWidth > 768) {
      // Desktop: remover clases de móvil
      sidebar.classList.remove("active")
      sidebarOverlay.classList.remove("active")
      document.body.style.overflow = ""
    } else {
      // Móvil: remover clases de desktop
      sidebar.classList.remove("collapsed")
    }
  })

  // Efecto hover para los enlaces del menú
  const navLinks = document.querySelectorAll(".nav-link")
  navLinks.forEach((link) => {
    link.addEventListener("mouseenter", function () {
      this.style.transform = "translateX(5px)"
    })

    link.addEventListener("mouseleave", function () {
      if (!this.classList.contains("active")) {
        this.style.transform = "translateX(0)"
      }
    })
  })

  // Animación de carga para los elementos del menú
  navLinks.forEach((link, index) => {
    link.style.opacity = "0"
    link.style.transform = "translateX(-20px)"

    setTimeout(() => {
      link.style.transition = "all 0.3s ease"
      link.style.opacity = "1"
      link.style.transform = "translateX(0)"
    }, index * 100)
  })
})

// Función para marcar el enlace activo basado en la URL actual
function setActiveNavLink() {
  const currentPath = window.location.pathname
  const navLinks = document.querySelectorAll(".nav-link")

  navLinks.forEach((link) => {
    link.classList.remove("active")
    if (link.getAttribute("href") === currentPath) {
      link.classList.add("active")
    }
  })
}

// Ejecutar al cargar la página
document.addEventListener("DOMContentLoaded", setActiveNavLink)

document.addEventListener("DOMContentLoaded", () => {
  // Elementos del DOM
const usernameInput = document.getElementById("username")
const passwordInput = document.getElementById("password")
const passwordToggle = document.getElementById("password-toggle")
const loginButton = document.getElementById("login-button")
const usernameError = document.getElementById("username-error")
const passwordError = document.getElementById("password-error")
const loginAttemptsMessage = document.getElementById("login-attempts-message")
const timerContainer = document.getElementById("timer-container")
const timerElement = document.getElementById("timer")

// Variables para el control de intentos
let loginAttempts = 0
const maxLoginAttempts = 3
let isLocked = false
let timerInterval

 // Función para alternar la visibilidad de la contraseña
passwordToggle.addEventListener("click", () => {
const eyeIcon = passwordToggle.querySelector(".eye-icon")
const eyeOffIcon = passwordToggle.querySelector(".eye-off-icon")

    if (passwordInput.type === "password") {
    passwordInput.type = "text"
    eyeIcon.classList.add("active")
    eyeOffIcon.classList.remove("active")
    } else {
    passwordInput.type = "password"
    eyeIcon.classList.remove("active")
    eyeOffIcon.classList.add("active")
    }
})

  // Función para manejar los placeholders dinámicos
function setupDynamicPlaceholder(input) {
    const originalPlaceholder = input.placeholder

    input.addEventListener("focus", () => {
    input.placeholder = ""
    })

    input.addEventListener("blur", () => {
    if (input.value === "") {
        input.placeholder = originalPlaceholder
    }
    })
}

  // Configurar placeholders dinámicos
setupDynamicPlaceholder(usernameInput)
setupDynamicPlaceholder(passwordInput)

  // Función para validar el formulario
function validateForm() {
    let isValid = true

    // Validar nombre de usuario
    if (!usernameInput.value.trim()) {
    usernameError.textContent = "El campo de usuario no puede estar vacío"
    isValid = false
    } else {
    usernameError.textContent = ""
    }

    // Validar contraseña
    if (!passwordInput.value.trim()) {
    passwordError.textContent = "El campo de contraseña no puede estar vacío"
    isValid = false
    } else {
    passwordError.textContent = ""
    }

    return isValid
}

  // Función para iniciar el temporizador de bloqueo
function startLockTimer() {
    let secondsLeft = 30
    timerElement.textContent = secondsLeft
    timerContainer.style.display = "block"

    timerInterval = setInterval(() => {
    secondsLeft--
    timerElement.textContent = secondsLeft

    if (secondsLeft <= 0) {
        clearInterval(timerInterval)
        isLocked = false
        loginAttempts = 0
        timerContainer.style.display = "none"
        loginAttemptsMessage.textContent = ""
        loginButton.disabled = false
    }
    }, 1000)
}

  // Función para manejar el inicio de sesión
loginButton.addEventListener("click", () => {
    // Verificar si la cuenta está bloqueada
    if (isLocked) {
return
    }

    // Validar el formulario
    if (!validateForm()) {
      return
    }

    // Datos para enviar al servidor
    const data = {
      username: usernameInput.value.trim(),
      password: passwordInput.value.trim(),
    }

    // Enviar solicitud al servidor
    fetch("/validate_login/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          // Redireccionar al dashboard
          window.location.href = data.redirect
        } else {
          // Incrementar contador de intentos fallidos
          loginAttempts++

          // Mostrar mensaje de error
          if (loginAttempts >= maxLoginAttempts) {
            isLocked = true
            loginButton.disabled = true
            loginAttemptsMessage.textContent = "Ha excedido el número máximo de intentos."
            startLockTimer()
          } else {
            const remainingAttempts = maxLoginAttempts - loginAttempts
            loginAttemptsMessage.textContent = `Credenciales incorrectas. Intentos restantes: ${remainingAttempts}`
          }
        }
      })
      .catch((error) => {
        console.error("Error:", error)
        loginAttemptsMessage.textContent = "Error de conexión. Intente nuevamente."
      })
  })

  // Permitir enviar el formulario con la tecla Enter
passwordInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
    loginButton.click()
    }
})

usernameInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
    loginButton.click()
    }
})
})

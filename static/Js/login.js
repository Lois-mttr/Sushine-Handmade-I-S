document.addEventListener("DOMContentLoaded", () => {
  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");
  const loginButton = document.getElementById("loginButton");
  const attemptsInfo = document.getElementById("attemptsInfo");
  const attemptsText = document.getElementById("attemptsText");
  const lockoutModal = document.getElementById("lockoutModal");
  const countdownNumber = document.getElementById("countdownNumber");
  const progressBar = document.getElementById("progressBar");
  const loginForm = document.getElementById("loginForm");
  const notificationContainer = document.getElementById("notificationContainer");

  const maxLoginAttempts = 3;
  let attemptsRemaining = maxLoginAttempts;
  let isLocked = false;
  let timerInterval = null;

  initializePage();

  function initializePage() {
    clearStoredLockout();
    updateAttemptsDisplay();
    setupEventListeners();
  }

  function setupEventListeners() {
    if (loginForm) {
      loginForm.addEventListener("submit", handleLogin);
    } else if (loginButton) {
      loginButton.addEventListener("click", handleLogin);
    }

    usernameInput?.addEventListener("keypress", (e) => {
      if (e.key === "Enter") passwordInput?.focus();
    });
    usernameInput?.addEventListener("input", () => clearFieldError("username"));
    passwordInput?.addEventListener("input", () => clearFieldError("password"));
  }

  async function handleLogin(e) {
    e.preventDefault();

    if (isLocked) {
      showNotification("Cuenta bloqueada. Espera a que termine el temporizador.", "warning");
      return;
    }

    if (!validateForm()) {
      showNotification("Por favor, corrige los errores en el formulario.", "error");
      return;
    }

    setLoadingState(true);

    try {
      const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
      const passwordHash = await sha256(passwordInput.value.trim());
      const data = {
        username: usernameInput.value.trim(),
        password: passwordHash,
        csrfmiddlewaretoken: csrfToken,
      };

      const response = await fetch(window.location.href, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(data),
      });

      const responseData = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(responseData.message || `Error HTTP: ${response.status}`);
      }

      if (responseData.success) {
        handleSuccessfulLogin(responseData);
      } else {
        handleFailedLogin(responseData);
      }
    } catch (error) {
      console.error("Error en login:", error);
      const errorMessage = error.message.includes("Failed to fetch")
        ? "Error de conexion. Verifica que el servidor este encendido."
        : error.message || "Error en el servidor. Intenta nuevamente.";

      showNotification(errorMessage, "error");
      updateAttemptsDisplay();
    } finally {
      setLoadingState(false);
    }
  }

  async function sha256(message) {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest("SHA-256", msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  function handleSuccessfulLogin(data) {
    attemptsRemaining = maxLoginAttempts;
    clearStoredLockout();

    showNotification("Inicio de sesión exitoso. Redirigiendo...", "success");
    setTimeout(() => {
      window.location.href = data.redirect_url || "/dashboard/";
    }, 800);
  }

  function handleFailedLogin(data) {
    attemptsRemaining = Number.isInteger(data.attempts_remaining)
      ? data.attempts_remaining
      : Math.max(0, attemptsRemaining - 1);

    const errorMessage = data.message || "Credenciales incorrectas";

    if (data.blocked) {
      lockAccount(data.lock_seconds || 20, errorMessage);
      return;
    }

    const attemptsUsed = maxLoginAttempts - attemptsRemaining;
    showNotification(`Intento ${attemptsUsed}/${maxLoginAttempts}: ${errorMessage}`, "error");
    updateAttemptsDisplay();
  }

  function lockAccount(seconds = 20, message = "Demasiados intentos fallidos. Intenta nuevamente en unos segundos.") {
    isLocked = true;
    attemptsRemaining = 0;
    showNotification(message, "error");
    updateAttemptsDisplay();
    startLockoutTimer(seconds);
  }

  function startLockoutTimer(seconds) {
    let remainingSeconds = seconds;

    if (!lockoutModal || !countdownNumber || !progressBar || !loginButton) return;

    lockoutModal.classList.add("show");
    document.body.style.overflow = "hidden";
    loginButton.disabled = true;
    countdownNumber.textContent = remainingSeconds;
    progressBar.style.width = "100%";

    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      remainingSeconds--;
      countdownNumber.textContent = remainingSeconds;
      progressBar.style.width = `${(remainingSeconds / seconds) * 100}%`;

      if (remainingSeconds <= 0) {
        clearInterval(timerInterval);
        unlockAccount();
      }
    }, 1000);
  }

  function unlockAccount() {
    isLocked = false;
    attemptsRemaining = maxLoginAttempts;
    clearStoredLockout();

    lockoutModal?.classList.remove("show");
    document.body.style.overflow = "";
    if (loginButton) loginButton.disabled = false;
    clearAllFieldErrors();
    resetForm();
    updateAttemptsDisplay();

    showNotification("Bloqueo terminado. Puedes intentar nuevamente.", "success");
  }

  function clearStoredLockout() {
    localStorage.removeItem("nexo_login_attempts");
    localStorage.removeItem("nexo_lock_end_time");
  }

  function validateForm() {
    let isValid = true;
    clearAllFieldErrors();

    const username = usernameInput?.value.trim() || "";
    const password = passwordInput?.value.trim() || "";

    if (!username) {
      showFieldError("username", "El campo de usuario es obligatorio");
      isValid = false;
    } else if (username.length > 15) {
      showFieldError("username", "El usuario no puede tener más de 15 caracteres");
      isValid = false;
    }

    if (!password) {
      showFieldError("password", "El campo de contraseña es obligatorio");
      isValid = false;
    }

    return isValid;
  }

  function showFieldError(fieldName, message) {
    const input = document.getElementById(fieldName);
    const errorElement = document.getElementById(`${fieldName}-error`);

    input?.classList.add("error");
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.classList.add("show");
    }
  }

  function clearFieldError(fieldName) {
    const input = document.getElementById(fieldName);
    const errorElement = document.getElementById(`${fieldName}-error`);

    input?.classList.remove("error");
    if (errorElement) {
      errorElement.classList.remove("show");
      errorElement.textContent = "";
    }
  }

  function clearAllFieldErrors() {
    clearFieldError("username");
    clearFieldError("password");
  }

  function updateAttemptsDisplay() {
    if (!attemptsText) return;

    attemptsText.textContent = `Intentos restantes: ${attemptsRemaining}`;
    attemptsInfo?.classList.remove("warning", "danger");

    if (attemptsRemaining <= 1) {
      attemptsInfo?.classList.add("danger");
    } else if (attemptsRemaining <= 2) {
      attemptsInfo?.classList.add("warning");
    }
  }

  function setLoadingState(loading) {
    if (!loginButton) return;

    if (loading) {
      loginButton.innerHTML = `<div class="loading-spinner"></div><span>Iniciando sesión...</span>`;
      loginButton.disabled = true;
    } else {
      loginButton.innerHTML = `
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
        </svg>
        <span>Iniciar sesión</span>`;
      loginButton.disabled = isLocked;
    }
  }

  function resetForm() {
    if (passwordInput) passwordInput.value = "";
  }

  function showNotification(message, type = "info", duration = 5000) {
    if (!notificationContainer) return;

    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.innerHTML = `
      <div class="flex items-start">
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-900">${message}</p>
        </div>
        <button class="ml-3 flex-shrink-0 text-gray-400 hover:text-gray-600" onclick="this.parentElement.parentElement.remove()">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
    `;

    notificationContainer.appendChild(notification);
    requestAnimationFrame(() => notification.classList.add("show"));

    setTimeout(() => {
      notification.classList.remove("show");
      setTimeout(() => notification.remove(), 300);
    }, duration);
  }
});

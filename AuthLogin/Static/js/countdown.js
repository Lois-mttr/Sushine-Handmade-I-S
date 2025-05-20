function setupCountdown(initialTime) {
    const countdownElement = document.getElementById('countdown');
    const submitBtn = document.getElementById('submitBtn');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const eyeToggle = document.getElementById('eye-toggle');
    const messageContainer = document.querySelector('.message-container');

    let timeLeft = initialTime;

    const timer = setInterval(() => {
        timeLeft -= 1;
        countdownElement.textContent = timeLeft;

        if (timeLeft <= 0) {
            clearInterval(timer);
            // Habilitar elementos
            if (usernameInput) usernameInput.disabled = false;
            if (passwordInput) passwordInput.disabled = false;
            if (eyeToggle) eyeToggle.disabled = false;
            if (submitBtn) submitBtn.disabled = false;
            // Ocultar mensaje de bloqueo
            if (messageContainer && messageContainer.querySelector('.text-red-500')) {
                messageContainer.style.display = 'none';
            }
        }
    }, 1000);
}

// Inicializar solo si está en una página con bloqueo
if (document.getElementById('countdown')) {
    const initialTime = parseInt(document.getElementById('countdown').textContent);
    document.addEventListener('DOMContentLoaded', () => setupCountdown(initialTime));
}
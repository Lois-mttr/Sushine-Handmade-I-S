// Toast CRUD y modal CRUD reutilizable
function showNotification(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return alert(message);
    const icons = {
        success: '<i class="fas fa-check-circle"></i>',
        error: '<i class="fas fa-times-circle"></i>',
        warning: '<i class="fas fa-exclamation-triangle"></i>',
        info: '<i class="fas fa-info-circle"></i>'
    };
    const classes = {
        success: 'toast toast-success',
        error: 'toast toast-error',
        warning: 'toast toast-warning',
        info: 'toast toast-info'
    };
    const toast = document.createElement('div');
    toast.className = `${classes[type] || classes.info} animate-fade-in-up`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span style="flex:1;">${message}</span>
        <button class="toast-close" aria-label="Cerrar">&times;</button>
    `;
    toast.querySelector('.toast-close').onclick = () => toast.remove();
    setTimeout(() => {
        toast.classList.add('animate-fade-out');
        setTimeout(() => toast.remove(), 500);
    }, 3500);
    toastContainer.appendChild(toast);
}

function showModal(html, onClose) {
    const bg = document.getElementById('modal-bg');
    const content = document.getElementById('modal-content');
    content.innerHTML = html;
    bg.style.display = 'flex';
    content.style.display = 'flex';
    content.style.pointerEvents = 'auto';
    function closeModal() {
        bg.style.display = 'none';
        content.style.display = 'none';
        content.innerHTML = '';
        content.style.pointerEvents = 'none';
        if (onClose) onClose();
    }
    bg.onclick = function(e) { if (e.target === bg) closeModal(); };
    const closeBtn = content.querySelector('.modal-close-x');
    if (closeBtn) closeBtn.onclick = closeModal;
    return closeModal;
}

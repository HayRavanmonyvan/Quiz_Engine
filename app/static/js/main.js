// app/static/js/main.js
/**
 * Global UI utilities for Quiz Engine (Google Forms Theme)
 */

/**
 * Shows a Google Forms / Material non-blocking Bootstrap toast alert
 * @param {string} message - Message text to display
 * @param {'danger'|'warning'|'success'|'info'} type - Toast variant
 */
function showGfToast(message, type = 'danger') {
    const container = document.getElementById('gfToastContainer');
    if (!container) return;

    const toastId = 'toast_' + Date.now();
    let bgClass = 'text-bg-danger';
    let icon = 'bi-exclamation-triangle-fill';

    if (type === 'success') {
        bgClass = 'text-bg-success';
        icon = 'bi-check-circle-fill';
    } else if (type === 'warning') {
        bgClass = 'text-bg-warning';
        icon = 'bi-exclamation-triangle-fill';
    } else if (type === 'info') {
        bgClass = 'text-bg-info';
        icon = 'bi-info-circle-fill';
    }

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center ${bgClass} border-0 shadow`;
    toastEl.id = toastId;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body d-flex align-items-center gap-2">
                <i class="bi ${icon}"></i>
                <span>${message}</span>
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    container.appendChild(toastEl);

    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
        toast.show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }
}

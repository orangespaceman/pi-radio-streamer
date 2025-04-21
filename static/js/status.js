export function showStatus(message, type) {
    const status = document.querySelector('.Status');
    status.textContent = message;
    status.classList.remove('Status--success', 'Status--error');
    status.classList.add(`Status--${type}`, 'is-visible');

    // Hide after x seconds
    setTimeout(() => {
        status.classList.remove('is-visible');
    }, 5000);
}

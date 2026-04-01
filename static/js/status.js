/**
 * Status message handling
 */

export const initializeStatus = () => {
    // Auto-hide status messages after 5 seconds if present
    const statusElements = document.querySelectorAll('.Status.is-visible');

    if (statusElements.length > 0) {
        setTimeout(() => {
            statusElements.forEach((element) => {
                element.classList.remove('is-visible');
            });
        }, 5000);
    }
};

/**
 * Show a status message
 * @param {string} message - Message to display
 * @param {string} type - Type of message ('success' or 'error')
 */
export const showStatus = (message, type = 'success') => {
    // Find or create status element
    let statusElement = document.querySelector('.Status');

    if (!statusElement) {
        statusElement = document.createElement('div');
        statusElement.classList.add('Status');
        document.body.appendChild(statusElement);
    }

    // Update content and classes
    statusElement.textContent = message;

    // Reset classes first
    statusElement.classList.remove(
        'Status--success',
        'Status--error',
        'is-visible'
    );
    // Add new classes
    statusElement.classList.add(`Status--${type}`, 'is-visible');

    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusElement.classList.remove('is-visible');
    }, 5000);
};

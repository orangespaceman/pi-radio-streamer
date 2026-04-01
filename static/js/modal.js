/**
 * Modal handling
 */

/**
 * Initialize all modals
 */
export const initializeModals = () => {
    const modals = document.querySelectorAll('.Modal');

    modals.forEach((modal) => {
        const closeButton = modal.querySelector('.Modal-close');

        if (closeButton) {
            closeButton.addEventListener('click', () => {
                closeModal(modal);
            });
        }

        // Close modal when clicking on the backdrop
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                closeModal(modal);
            }
        });
    });

    // Close modals with Escape key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            const visibleModal = document.querySelector('.Modal.is-visible');
            if (visibleModal) {
                closeModal(visibleModal);
            }
        }
    });
};

/**
 * Show a specific modal
 * @param {string} modalId - ID of the modal to show
 */
export const showModal = (modalId) => {
    const modal = document.querySelector(`#${modalId}`);
    if (modal) {
        modal.classList.add('is-visible');
        return true;
    }
    console.error(`Modal not found: ${modalId}`);
    return false;
};

/**
 * Close a modal
 * @param {Element} modal - The modal element to close
 */
export const closeModal = (modal) => {
    modal.classList.remove('is-visible');
};

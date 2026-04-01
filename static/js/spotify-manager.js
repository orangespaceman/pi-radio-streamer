/**
 * Spotify Item Manager
 */
import { initializeModals, showModal, closeModal } from './modal.js';
import { showStatus } from './status.js';

// DOM elements
const itemsList = document.querySelector('#items-list');
const noItemsMessage = document.querySelector('#no-items-message');
const addItemForm = document.querySelector('#add-item-form');
const editItemForm = document.querySelector('#edit-item-form');
const editModal = document.querySelector('#edit-modal');
const confirmModal = document.querySelector('#confirm-modal');
const confirmDeleteButton = document.querySelector('#confirm-delete');
let deleteItemId = null;

// Initialize the manager
async function initializeManager() {
    // Initialize modals
    initializeModals();

    // Add event listeners
    addItemForm.addEventListener('submit', handleAddItem);
    editItemForm.addEventListener('submit', handleEditItem);

    // Close buttons for modals
    document
        .querySelectorAll('.SpotifyManager-cancelButton')
        .forEach((button) => {
            button.addEventListener('click', () => {
                closeModal(button.closest('.Modal'));
            });
        });

    // Delete confirmation
    confirmDeleteButton.addEventListener('click', handleConfirmDelete);

    // Load initial items
    await loadItems();
}

// Load items from the server
async function loadItems() {
    try {
        const response = await fetch('/spotify/items');
        if (!response.ok) {
            throw new Error('Failed to load items');
        }

        const data = await response.json();
        renderItems(data.items);
    } catch (error) {
        console.error('Error loading items:', error);
        showStatus('Error loading items: ' + error.message, 'error');
    }
}

// Render items in the table
function renderItems(items) {
    itemsList.innerHTML = '';

    if (items.length === 0) {
        noItemsMessage.classList.remove('is-hidden');
        document.querySelector('#items-table').classList.add('is-hidden');
        return;
    }

    noItemsMessage.classList.add('is-hidden');
    document.querySelector('#items-table').classList.remove('is-hidden');

    items.forEach((item) => {
        const row = document.createElement('tr');

        const nameCell = document.createElement('td');
        nameCell.textContent = item.name;
        row.appendChild(nameCell);

        const actionsCell = document.createElement('td');
        actionsCell.className = 'SpotifyManager-actionButtons';

        const editButton = document.createElement('button');
        editButton.className =
            'SpotifyManager-actionButton SpotifyManager-actionButton--edit';
        editButton.textContent = 'Edit';
        editButton.addEventListener('click', () => openEditModal(item));
        actionsCell.appendChild(editButton);

        const deleteButton = document.createElement('button');
        deleteButton.className =
            'SpotifyManager-actionButton SpotifyManager-actionButton--delete';
        deleteButton.textContent = 'Delete';
        deleteButton.addEventListener('click', () =>
            openDeleteConfirmation(item.id)
        );
        actionsCell.appendChild(deleteButton);

        row.appendChild(actionsCell);

        itemsList.appendChild(row);
    });
}

// Handle adding a new item
async function handleAddItem(event) {
    event.preventDefault();

    const name = document.querySelector('#name').value.trim();
    const uri = document.querySelector('#uri').value.trim();

    if (!name || !uri) {
        showStatus('Please fill out all fields', 'error');
        return;
    }

    try {
        const response = await fetch('/spotify/items', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, uri }),
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(data.message, 'success');
            addItemForm.reset();
            await loadItems();
        } else {
            showStatus(data.error || 'Failed to add item', 'error');
        }
    } catch (error) {
        console.error('Error adding item:', error);
        showStatus('Error adding item: ' + error.message, 'error');
    }
}

// Open the edit modal for an item
function openEditModal(item) {
    document.querySelector('#edit-item-id').value = item.id;
    document.querySelector('#edit-name').value = item.name;
    document.querySelector('#edit-uri').value = item.uri;

    showModal('edit-modal');
}

// Handle editing an item
async function handleEditItem(event) {
    event.preventDefault();

    const id = document.querySelector('#edit-item-id').value;
    const name = document.querySelector('#edit-name').value.trim();
    const uri = document.querySelector('#edit-uri').value.trim();

    if (!name || !uri) {
        showStatus('Please fill out all fields', 'error');
        return;
    }

    try {
        const response = await fetch(`/spotify/items/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, uri }),
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(data.message, 'success');
            closeModal(editModal);
            await loadItems();
        } else {
            showStatus(data.error || 'Failed to update item', 'error');
        }
    } catch (error) {
        console.error('Error updating item:', error);
        showStatus('Error updating item: ' + error.message, 'error');
    }
}

// Open delete confirmation modal
function openDeleteConfirmation(id) {
    deleteItemId = id;
    showModal('confirm-modal');
}

// Handle confirming deletion
async function handleConfirmDelete() {
    if (deleteItemId === null) return;

    try {
        const response = await fetch(`/spotify/items/${deleteItemId}`, {
            method: 'DELETE',
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(data.message, 'success');
            closeModal(confirmModal);
            await loadItems();
        } else {
            showStatus(data.error || 'Failed to delete item', 'error');
        }
    } catch (error) {
        console.error('Error deleting item:', error);
        showStatus('Error deleting item: ' + error.message, 'error');
    } finally {
        deleteItemId = null;
    }
}

initializeManager();

import { showStatus } from './status.js';

function updateButtonState(button, isLoading) {
    button.classList.toggle('is-loading', isLoading);
    button.disabled = isLoading;
}

function clearActiveStations() {
    document.querySelectorAll('.Button').forEach((button) => {
        button.classList.remove('is-active');
    });
}

async function checkCurrentStation() {
    try {
        const response = await fetch('/now-playing');
        const data = await response.json();

        if (data.playing && data.station_id) {
            const button = document.querySelector(
                `[data-station-id="${data.station_id}"]`
            );
            if (button) {
                clearActiveStations();
                button.classList.add('is-active');
            }
        }
    } catch (error) {
        console.error('Error checking current station:', error);
    }
}

async function handleStationClick(event) {
    const button = event.currentTarget;
    const stationId = button.dataset.stationId;

    // Clear any previously active stations
    clearActiveStations();

    try {
        updateButtonState(button, true);
        const response = await fetch(`/play/${stationId}`);
        const data = await response.json();

        if (data.success) {
            showStatus(data.message, 'success');
            button.classList.add('is-active');
        } else {
            showStatus(data.error || 'Unknown error', 'error');
        }
    } catch (error) {
        console.error('Error playing station:', error);
        showStatus('Error playing station', 'error');
    } finally {
        updateButtonState(button, false);
    }
}

async function handleStopClick(event) {
    const button = event.currentTarget;

    try {
        updateButtonState(button, true);
        const response = await fetch('/stop');
        const data = await response.json();

        if (data.success) {
            showStatus(data.message, 'success');
            clearActiveStations();
        } else {
            showStatus(data.error || 'Unknown error', 'error');
        }
    } catch (error) {
        console.error('Error stopping playback:', error);
        showStatus('Error stopping playback', 'error');
    } finally {
        updateButtonState(button, false);
    }
}

function handleRefreshClick(event) {
    event.preventDefault();
    window.location.reload();
}

export function initializePlaybackControls() {
    // Add click handlers to all station buttons
    document.querySelectorAll('.Button--station').forEach((button) => {
        button.addEventListener('click', handleStationClick);
    });

    // Add click handler to stop button
    const stopButton = document.querySelector('.Button--stop');
    stopButton.addEventListener('click', handleStopClick);

    const refreshButton = document.querySelector('.IP-address');
    refreshButton.addEventListener('click', handleRefreshClick);

    // Check current station on page load
    checkCurrentStation();
}

import { showStatus } from './status.js';

const stopButton = document.querySelector('.ControlButton--stop');
const playButton = document.querySelector('.ControlButton--play');
const pauseButton = document.querySelector('.ControlButton--pause');
const prevButton = document.querySelector('.ControlButton--prev');
const nextButton = document.querySelector('.ControlButton--next');

function updateButtonState(button, isLoading) {
    button.classList.toggle('is-loading', isLoading);
    button.disabled = isLoading;
}

function clearActiveStations() {
    document.querySelectorAll('.StationButton').forEach((button) => {
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
        updateControls(data);
    } catch (error) {
        console.error('Error checking current station:', error);
    }
}

export function updateControls(data) {
    if (data.source === 'Spotify') {
        stopButton.classList.add('is-hidden');
        prevButton.classList.remove('is-hidden');
        nextButton.classList.remove('is-hidden');

        if (data.playing) {
            playButton.classList.add('is-hidden');
            pauseButton.classList.remove('is-hidden');
        } else {
            playButton.classList.remove('is-hidden');
            pauseButton.classList.add('is-hidden');
        }
    } else {
        stopButton.classList.remove('is-hidden');
        prevButton.classList.add('is-hidden');
        nextButton.classList.add('is-hidden');
        playButton.classList.add('is-hidden');
        pauseButton.classList.add('is-hidden');
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

async function handleControlClick(event, control) {
    const button = event.currentTarget;

    try {
        updateButtonState(button, true);
        const response = await fetch(`/${control}`);
        const data = await response.json();

        if (!data.success) {
            showStatus(data.error || 'Unknown error', 'error');
        }
    } catch (error) {
        console.error('Error updating playback:', error);
        showStatus('Error updating playback', 'error');
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
    document.querySelectorAll('.StationButton').forEach((button) => {
        button.addEventListener('click', handleStationClick);
    });

    // Add click handler to control buttons
    stopButton.addEventListener('click', handleStopClick);
    playButton.addEventListener('click', (e) => handleControlClick(e, 'play'));
    pauseButton.addEventListener('click', (e) =>
        handleControlClick(e, 'pause')
    );
    prevButton.addEventListener('click', (e) => handleControlClick(e, 'prev'));
    nextButton.addEventListener('click', (e) => handleControlClick(e, 'next'));

    const refreshButton = document.querySelector('.TopBar-ipAddress');
    refreshButton.addEventListener('click', handleRefreshClick);

    // Check current station on page load
    checkCurrentStation();
}

import { showStatus } from './status.js';
import { updateNowPlaying } from './now-playing.js';

const stopButton = document.querySelector('.ControlButton--stop');
const playButton = document.querySelector('.ControlButton--play');
const pauseButton = document.querySelector('.ControlButton--pause');
const prevButton = document.querySelector('.ControlButton--prev');
const nextButton = document.querySelector('.ControlButton--next');
const randomPlaylistButton = document.querySelector('#random-playlist-button');

async function fetchJsonOrError(url, options) {
    const response = await fetch(url, options);
    let data = null;

    try {
        data = await response.json();
    } catch (_error) {
        data = null;
    }

    if (!response.ok) {
        const detail = data?.error || `${response.status} ${response.statusText}`;
        throw new Error(detail);
    }

    return data || {};
}

function updateButtonState(button, isLoading) {
    button.classList.toggle('is-loading', isLoading);
    button.disabled = isLoading;
}

function clearActiveStations() {
    document.querySelectorAll('.StationButton').forEach((button) => {
        button.classList.remove('is-active');
    });
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

        // Show or hide the random playlist button based on Spotify control availability
        if (data.spotify_control_available) {
            randomPlaylistButton.classList.remove('is-hidden');
        } else {
            randomPlaylistButton.classList.add('is-hidden');
        }
    } else {
        stopButton.classList.remove('is-hidden');
        prevButton.classList.add('is-hidden');
        nextButton.classList.add('is-hidden');
        playButton.classList.add('is-hidden');
        pauseButton.classList.add('is-hidden');
        randomPlaylistButton.classList.add('is-hidden');
    }
}

async function handleStationClick(event) {
    const button = event.currentTarget;
    const stationId = button.dataset.stationId;

    // Clear any previously active stations
    clearActiveStations();

    try {
        updateButtonState(button, true);
        const data = await fetchJsonOrError(`/play/${stationId}`);

        if (data.success) {
            showStatus(data.message, 'success');
            button.classList.add('is-active');
            updateNowPlaying(data);
            updateControls(data);
        } else {
            showStatus(data.error || 'Unknown error', 'error');
        }
    } catch (error) {
        console.error('Error playing station:', error);
        showStatus(error.message || 'Error playing station', 'error');
    } finally {
        updateButtonState(button, false);
    }
}

async function handleStopClick(event) {
    const button = event.currentTarget;

    try {
        updateButtonState(button, true);
        const data = await fetchJsonOrError('/stop');

        if (data.success) {
            showStatus(data.message, 'success');
            clearActiveStations();
            updateNowPlaying(data);
            updateControls(data);
        } else {
            showStatus(data.error || 'Unknown error', 'error');
        }
    } catch (error) {
        console.error('Error stopping playback:', error);
        showStatus(error.message || 'Error stopping playback', 'error');
    } finally {
        updateButtonState(button, false);
    }
}

async function handleControlClick(event, control) {
    const button = event.currentTarget;

    try {
        updateButtonState(button, true);
        const data = await fetchJsonOrError(`/${control}`);

        if (data.success) {
            updateNowPlaying(data);
            updateControls(data);
        } else {
            showStatus(data.error || 'Unknown error', 'error');
        }
    } catch (error) {
        console.error('Error updating playback:', error);
        showStatus(error.message || 'Error updating playback', 'error');
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
}

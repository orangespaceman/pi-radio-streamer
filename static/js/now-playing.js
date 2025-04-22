import { updateControls } from './playback.js';

let currentTrack = null;

function showPanel(panelClass) {
    document.querySelectorAll('.Panels-panel').forEach((panel) => {
        panel.classList.toggle(
            'is-visible',
            panel.classList.contains(panelClass)
        );
    });
    updateNavigationButtons();
}

function updateNavigationButtons() {
    const nowPlayingPanel = document.querySelector('.Panels-panel--nowPlaying');
    const backButton = document.querySelector('.NavButton--back');
    const forwardButton = document.querySelector('.NavButton--forward');
    const isNowPlayingVisible =
        nowPlayingPanel.classList.contains('is-visible');
    const isPlaying = currentTrack && currentTrack.playing;

    // Back button: only show when viewing now playing panel
    backButton.classList.toggle('is-visible', isNowPlayingVisible);

    // Forward button: only show when viewing stations panel AND something is playing
    forwardButton.classList.toggle(
        'is-visible',
        !isNowPlayingVisible && isPlaying
    );
}

function startProgress() {
    const progressBar = document.querySelector('.TopBar-updateProgressBar');
    progressBar.classList.remove('is-progressing');
    // Force a reflow to restart the animation
    void progressBar.offsetWidth;
    progressBar.classList.add('is-progressing');
}

function updateNowPlaying(data) {
    const nowPlayingPanel = document.querySelector('.Panels-panel--nowPlaying');
    const stationsPanel = document.querySelector('.Panels-panel--stations');
    const artwork = nowPlayingPanel.querySelector('.NowPlaying-artwork');
    const track = nowPlayingPanel.querySelector('.NowPlaying-track');
    const artist = nowPlayingPanel.querySelector('.NowPlaying-artist');
    const album = nowPlayingPanel.querySelector('.NowPlaying-album');
    const playlist = nowPlayingPanel.querySelector('.NowPlaying-playlist');
    const releaseDate = nowPlayingPanel.querySelector(
        '.NowPlaying-releaseDate'
    );
    const source = nowPlayingPanel.querySelector('.NowPlaying-source');

    updateControls(data);

    // If we're already showing this track, don't update
    if (
        currentTrack &&
        currentTrack.title === data.title &&
        currentTrack.artist === data.artist &&
        currentTrack.artwork === data.artwork &&
        currentTrack.album === data.album &&
        currentTrack.playlist === data.playlist
    ) {
        return;
    }

    currentTrack = data;

    if (data.playing) {
        artwork.src = data.artwork || '';
        track.textContent = '🎵 ' + (data.title || 'Unknown Track');

        if (data.artist) {
            artist.textContent = '👤 ' + (data.artist || '');
            artist.classList.add('is-visible');
        } else {
            artist.textContent = '';
            artist.classList.remove('is-visible');
        }

        if (data.album) {
            album.textContent = '💿 ' + (data.album || '');
            album.classList.add('is-visible');
        } else {
            album.textContent = '';
            album.classList.remove('is-visible');
        }

        if (data.release_date) {
            releaseDate.textContent = '🗓️ ' + (data.release_date || '');
            releaseDate.classList.add('is-visible');
        } else {
            releaseDate.textContent = '';
            releaseDate.classList.remove('is-visible');
        }

        if (data.playlist) {
            playlist.textContent = '📑 ' + (data.playlist || '');
            playlist.classList.add('is-visible');
        } else {
            playlist.textContent = '';
            playlist.classList.remove('is-visible');
        }

        source.textContent = data.source || '';

        // Show now playing panel if not already visible
        if (!nowPlayingPanel.classList.contains('is-visible')) {
            showPanel('Panels-panel--nowPlaying');
        }
    } else {
        // Show stations panel if not already visible
        if (!stationsPanel.classList.contains('is-visible')) {
            showPanel('Panels-panel--stations');
        }
    }

    // Update navigation buttons based on new state
    updateNavigationButtons();
}

function initializeNowPlaying() {
    // Add click handler for back button
    const backButton = document.querySelector('.NavButton--back');
    backButton.addEventListener('click', () => {
        showPanel('Panels-panel--stations');
    });

    // Add click handler for forward button
    const forwardButton = document.querySelector('.NavButton--forward');
    forwardButton.addEventListener('click', () => {
        showPanel('Panels-panel--nowPlaying');
    });

    // Start polling for now playing info
    async function checkNowPlaying() {
        try {
            startProgress();
            const response = await fetch('/now-playing');
            const data = await response.json();
            updateNowPlaying(data);
        } catch (error) {
            console.error('Error polling now playing:', error);
        }

        setTimeout(checkNowPlaying, 10000);
    }

    // Poll every x seconds
    checkNowPlaying();
}

export { initializeNowPlaying };

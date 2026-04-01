/**
 * Spotify button functionality
 */
import { showStatus } from './status.js';
import { showModal } from './modal.js';
import { updateControls } from './playback.js';
import { updateNowPlaying } from './now-playing.js';

export const initializeSpotifyButton = () => {
    const spotifyButton = document.querySelector('#random-playlist-button');
    if (!spotifyButton) return;

    // Check if the user is authenticated with Spotify
    const checkSpotifyAuth = async () => {
        try {
            // Use the dedicated auth status endpoint instead of now_playing
            const response = await fetch('/spotify/auth-status');
            if (response.status === 200) {
                // User is authenticated, show the button
                spotifyButton.classList.remove('is-hidden');
            } else {
                // User is not authenticated, keep button hidden
                spotifyButton.classList.add('is-hidden');
            }
        } catch (error) {
            console.error('Error checking Spotify auth:', error);
            // Assume not authenticated if there's an error
            spotifyButton.classList.add('is-hidden');
        }
    };

    // Run the auth check on load
    checkSpotifyAuth();

    spotifyButton.addEventListener('click', async () => {
        if (spotifyButton.disabled) return;

        spotifyButton.classList.add('is-loading');
        spotifyButton.disabled = true;

        try {
            // Use the updated endpoint
            const response = await fetch('/play-random-playlist');
            const contentType = response.headers.get('content-type') || '';
            const isJson = contentType.includes('application/json');

            if (response.status === 401) {
                // Authentication needed
                // Make sure button is no longer loading before showing modal
                spotifyButton.classList.remove('is-loading');
                spotifyButton.disabled = false;
                // Show the authentication modal
                showModal('spotify-auth-modal');
                return;
            }

            if (!response.ok) {
                let message = `Spotify request failed (${response.status})`;
                if (isJson) {
                    const errorData = await response.json();
                    if (errorData?.error) {
                        message = errorData.error;
                    }
                }
                throw new Error(message);
            }

            // Process result for successful request
            const data = isJson ? await response.json() : {};

            if (data.success) {
                showStatus(
                    data.message || 'Playing random Spotify content',
                    'success'
                );

                // Update UI with new playback info
                updateNowPlaying(data);
                updateControls(data);
            } else {
                throw new Error(
                    data.error || 'Failed to start Spotify playback'
                );
            }
        } catch (error) {
            console.error('Spotify playback error:', error);

            // Show the error message
            showStatus(
                error.message || 'Error starting Spotify playback',
                'error'
            );
        } finally {
            spotifyButton.classList.remove('is-loading');
            spotifyButton.disabled = false;
        }
    });
};

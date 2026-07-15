import logging
import os
import datetime
import random
import secrets
import time
from .base import NowPlayingService
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheFileHandler
from . import spotify_items

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
# Anchor to the project directory so the cache survives running from any CWD
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(BASE_DIR, ".spotify_cache")
SPOTIFY_CHROMECAST_APP_ID = "CC32E753"

class SpotifyService(NowPlayingService):
    def __init__(self, cast=None, redirect_uri=None):
        super().__init__(cast)
        self.cast = cast
        self.sp = None
        self.oauth_manager = None
        self.auth_state = None

        # Use provided redirect URI if available, otherwise use default
        self.redirect_uri = redirect_uri
        logger.info(f"SpotifyService using redirect URI: {self.redirect_uri}")

        # Only initialize the OAuth manager here, not the client yet
        if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET and self.redirect_uri:
            scope = "user-read-playback-state,user-modify-playback-state"
            try:
                # Create the OAuth manager
                self.oauth_manager = SpotifyOAuth(
                    client_id=SPOTIFY_CLIENT_ID,
                    client_secret=SPOTIFY_CLIENT_SECRET,
                    redirect_uri=self.redirect_uri,
                    scope=scope,
                    cache_handler=CacheFileHandler(cache_path=CACHE_PATH)
                )

                if self._ensure_client():
                    logger.info("Spotify client initialized using cached token")
                else:
                    logger.info("No valid Spotify token found. Authentication needed.")
            except Exception as e:
                logger.error(f"Error initializing Spotify OAuth: {e}")

    def _ensure_client(self):
        """Return the Spotify client, initializing it from a cached token if needed"""
        if self.sp:
            return self.sp
        if not self.oauth_manager:
            return None

        try:
            token_info = self.oauth_manager.validate_token(
                self.oauth_manager.get_cached_token()
            )
            if token_info:
                self.sp = spotipy.Spotify(auth_manager=self.oauth_manager)
            else:
                logger.debug("No valid cached Spotify token")
        except Exception as e:
            logger.debug(f"Unable to initialize Spotify client from cache: {e}")
        return self.sp

    def is_authenticated(self):
        """Check if the Spotify client is initialized and has a valid token"""
        if not self._ensure_client():
            return False

        try:
            # Test API access to verify the client is working
            self.sp.me()
            return True
        except Exception as e:
            logger.error(f"Spotify client failed API test: {e}")
            self.sp = None  # Clear the broken client
            return False

    def get_auth_url(self):
        """Get the Spotify authorization URL to direct the user to"""
        if not self.oauth_manager:
            logger.error("OAuth manager not initialized")
            return None

        try:
            # Generate a random state for security
            self.auth_state = secrets.token_urlsafe(16)

            # Get the authorization URL
            auth_url = self.oauth_manager.get_authorize_url(state=self.auth_state)
            logger.info("Generated Spotify authorization URL")
            return auth_url
        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            return None

    def handle_auth_callback(self, code):
        """Handle the authentication callback from Spotify"""
        if not self.oauth_manager:
            logger.error("OAuth manager not initialized")
            return False

        try:
            # Exchange the code for a token
            token_info = self.oauth_manager.get_access_token(code)
            logger.info(f"Obtained access token successfully: {token_info is not None}")

            # Create the Spotify client with the new token
            self.sp = spotipy.Spotify(auth_manager=self.oauth_manager)

            # Verify the client was initialized properly
            if self.sp:
                try:
                    # Test API access to verify the client is working
                    me = self.sp.me()
                    logger.info(f"Spotify authentication successful - connected as {me['display_name']}")
                    return True
                except Exception as e:
                    logger.error(f"Spotify client created but API test failed: {e}")
                    return False
            else:
                logger.error("Failed to create Spotify client")
                return False

        except Exception as e:
            logger.error(f"Error handling auth callback: {e}")
            return False

    def get_track(self, current_track):
        # Try to initialize client if not already done
        self._ensure_client()

        if not self.cast or not self.cast.media_controller.status:
            logger.debug("No cast or media controller status available")
            return None

        cast_status = self.cast.status
        media_controller_status = self.cast.media_controller.status
        if not media_controller_status or not media_controller_status.media_metadata:
            logger.debug(f"No media metadata available in status: {media_controller_status}")
            return None

        metadata = media_controller_status.media_metadata
        logger.debug(f"Cast status: {cast_status}")
        logger.debug(f"Full Spotify metadata: {metadata}")
        logger.debug(f"Full media controller status: {media_controller_status}")

        # Get artwork from Spotify
        image_url = None
        if metadata.get('images'):
            image_url = metadata['images'][0].get('url')
            logger.debug(f"Found image URL: {image_url}")

        # Get track details from media_metadata
        title = metadata.get('songName') or metadata.get('title', 'Unknown')
        artist = metadata.get('artist', 'Unknown')
        album = metadata.get('albumName')

        # If the current track is the same as the one we're getting,
        # use the cached release date to prevent extra API calls
        if (current_track and current_track['title'] == title
            and current_track['artist'] == artist):
            release_date = current_track['release_date']
            logger.debug(f"Using cached release date: {release_date}")
        else:
            release_date = self.get_release_date(media_controller_status)

        # Get playlist name from context
        playlist_name = None
        if hasattr(media_controller_status, 'media_custom_data'):
            custom_data = media_controller_status.media_custom_data
            if isinstance(custom_data, dict):
                player_state = custom_data.get('playerPlaybackState', {})
                context = player_state.get('context', {})
                if context:
                    metadata = context.get('metadata', {})
                    playlist_name = metadata.get('context_description')

        track_info = {
            'title': title,
            'artist': artist,
            'image_url': image_url,
            'album': album,
            'playlist': playlist_name,
            'release_date': release_date,
            'source': 'Spotify'
        }
        logger.debug(f"Returning track info: {track_info}")
        return track_info

    def has_key_deep(self, data, *names):
        for name in names:
            if name not in data:
                return False
            data = data[name]
        return True

    def get_release_date(self, media_controller_status):
        if not self.sp:
            return None

        try:
            track = self.sp.track(media_controller_status.content_id)
            if self.has_key_deep(track, "album", "release_date"):
                try:
                    date_string = track["album"]["release_date"]
                    date_precision = track["album"]["release_date_precision"]
                    if date_precision == "year":
                        return date_string
                    elif date_precision == "month":
                        date_obj = datetime.datetime.strptime(date_string, "%Y-%m")
                        return date_obj.strftime("%B %Y")
                    else:
                        date_obj = datetime.datetime.strptime(
                            date_string, "%Y-%m-%d"
                        )
                        return date_obj.strftime("%-d %B %Y")
                except Exception as e:
                    logger.error(f"Error getting release date: {e}")

        except Exception as e:
            logger.error(f"Error getting release date: {e}")

    def is_chromecast_available(self):
        """Check if the current Chromecast is available as a Spotify device"""
        try:
            return self._find_spotify_device() is not None
        except Exception as e:
            logger.error(f"Error checking Spotify devices: {e}")
            return False

    def play_random_content(self):
        """Start playing random content (playlist, album, or track) from the configured list"""
        if not self._ensure_client():
            logger.error("Spotify authentication required")
            return {'error': 'Spotify authentication required'}

        # Get all available Spotify items
        spotify_config_items = spotify_items.get_items()

        # Check if we have any items configured
        if not spotify_config_items:
            logger.error("No Spotify items configured")
            return {'error': 'No Spotify items configured'}

        try:
            # Get a random item from the configured list
            selected_item = random.choice(spotify_config_items)
            random_item = str(selected_item.get('uri', '')).strip()
            selected_name = str(selected_item.get('name', '')).strip() or random_item
            if not random_item:
                logger.error("Selected empty Spotify item")
                return {'error': 'Selected Spotify item is empty'}

            # Ensure Chromecast appears as a Spotify device, even from idle.
            chromecast_device = self._ensure_spotify_device_ready()
            if not chromecast_device:
                cast_name = self.cast.name if self.cast else 'Chromecast'
                return {
                    'error': (
                        f'{cast_name} is not available in Spotify Connect. '
                        'Ensure Spotify is open on the Chromecast and try again.'
                    )
                }

            device_id = chromecast_device['id']
            cast_name = self.cast.name if self.cast else 'Chromecast'

            # Determine what type of content this is and create the proper URI if needed
            if random_item.startswith('spotify:'):
                # Already a URI
                context_uri = random_item
                content_type = random_item.split(':')[1]  # playlist, album, or track
            elif ':' not in random_item:
                # Assume it's a playlist ID
                context_uri = f"spotify:playlist:{random_item}"
                content_type = "playlist"
            else:
                # Invalid format
                logger.error(f"Invalid Spotify item format: {random_item}")
                return {'error': f'Invalid Spotify item format: {random_item}'}

            # Transfer playback first to make device activation more reliable.
            try:
                self.sp.transfer_playback(device_id=device_id, force_play=False)
            except Exception as e:
                logger.debug(f"Spotify transfer_playback failed, continuing: {e}")

            # Start playback on the Chromecast
            logger.info(f"Starting {content_type} playback: {context_uri}")
            self.sp.start_playback(
                device_id=device_id,
                context_uri=context_uri
            )

            logger.info(f"Started random {content_type} on {cast_name}")
            return {
                'context_uri': context_uri,
                'selected_name': selected_name,
                'content_type': content_type,
            }

        except Exception as e:
            logger.error(f"Error playing random content: {e}")
            return {'error': f'Error playing random content: {str(e)}'}

    def _find_spotify_device(self):
        if not self.sp or not self.cast:
            return None
        devices = self.sp.devices()
        if not devices or 'devices' not in devices:
            return None
        cast_name = self.cast.name
        return next((device for device in devices['devices'] if device['name'] == cast_name), None)

    def _ensure_spotify_device_ready(self, timeout_seconds=15):
        device = self._find_spotify_device()
        if device:
            return device

        if self.cast:
            try:
                self.cast.start_app(SPOTIFY_CHROMECAST_APP_ID)
            except Exception as e:
                logger.debug(f"Unable to start Spotify app on Chromecast: {e}")

        for _ in range(timeout_seconds):
            time.sleep(1)
            device = self._find_spotify_device()
            if device:
                return device
        return None

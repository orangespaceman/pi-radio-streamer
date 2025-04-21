import logging
import os
import datetime
from .base import NowPlayingService
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')


class SpotifyService(NowPlayingService):
    def get_track(self, current_track):
        if not self.cast or not self.cast.media_controller.status:
            logging.debug("No cast or media controller status available")
            return None

        cast_status = self.cast.status
        media_controller_status = self.cast.media_controller.status
        if not media_controller_status or not media_controller_status.media_metadata:
            logging.debug(f"No media metadata available in status: {media_controller_status}")
            return None

        metadata = media_controller_status.media_metadata
        logging.debug(f"Cast status: {cast_status}")
        logging.debug(f"Full Spotify metadata: {metadata}")
        logging.debug(f"Full media controller status: {media_controller_status}")

        # Get artwork from Spotify
        image_url = None
        if metadata.get('images'):
            image_url = metadata['images'][0].get('url')
            logging.debug(f"Found image URL: {image_url}")

        # Get track details from media_metadata
        title = metadata.get('songName') or metadata.get('title', 'Unknown')
        artist = metadata.get('artist', 'Unknown')
        album = metadata.get('albumName')

        # If the current track is the same as the one we're getting,
        # use the cached release date to prevent extra API calls
        if (current_track and current_track['title'] == title
            and current_track['artist'] == artist):
            release_date = current_track['release_date']
            logging.debug(f"Using cached release date: {release_date}")
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
        logging.debug(f"Returning track info: {track_info}")
        return track_info

    def has_key_deep(self, dict, *names):
        for name in names:
            if name not in dict:
                return False
            dict = dict[name]
        return True

    def get_release_date(self, media_controller_status):
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            return None

        try:
            sp = spotipy.Spotify(
                    auth_manager=SpotifyClientCredentials(
                        client_id=SPOTIFY_CLIENT_ID,
                        client_secret=SPOTIFY_CLIENT_SECRET,
                    )
                )

            track = sp.track(media_controller_status.content_id)
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
                    logging.error(f"Error getting release date: {e}")

        except Exception as e:
            logging.error(f"Error getting release date: {e}")


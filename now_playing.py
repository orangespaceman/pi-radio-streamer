import requests
import time
import os
import shutil
import logging
import re
from datetime import datetime
from config.stations import STATIONS
from services.bbc import BBC6Service
from services.fip import FIPService
from services.spotify import SpotifyService

class NowPlaying:
    def __init__(self, cast=None):
        self.cast = cast
        self.last_update = None
        self.current_track = None
        self.cache_dir = "./static/cache/"

        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)

        # Initialize services
        self.services = {
            'BBC6Service': BBC6Service(cast),
            'FIPService': FIPService(cast),
            'SpotifyService': SpotifyService(cast)
        }

    def cache_image(self, url, file_name):
        """Download and cache an image file"""
        if not url:
            return None

        file_path = os.path.join(self.cache_dir, file_name)

        # Return cached file if it exists
        if os.path.isfile(file_path):
            return file_name

        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(file_path, 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                return file_name
        except Exception:
            pass
        return None

    def get_current_track(self):
        """Get the currently playing track from any source"""
        # Only update every 10 seconds to avoid hammering APIs
        if self.last_update and time.time() - self.last_update < 10:
            return self.current_track

        if not self.cast:
            logging.debug("No cast device available")
            return None

        self.last_update = time.time()

        # Check what's playing on Chromecast
        if self.cast.media_controller.status:
            logging.debug(f"Chromecast app_id: {self.cast.app_id}")
            logging.debug(f"Media controller status: {self.cast.media_controller.status}")

            content_id = str(self.cast.media_controller.status.content_id or '').lower()
            title = str(self.cast.media_controller.status.title or '').lower()
            logging.debug(f"Content ID: {content_id}")
            logging.debug(f"Title: {title}")

            # First check if Spotify is playing
            if 'spotify:track:' in content_id:
                logging.debug("Spotify track detected")
                track = self.services['SpotifyService'].get_track(self.current_track)
                if track:
                    track['station_id'] = 'spotify'
                    self.current_track = track
                    return track

            # Find matching station based on content_matchers
            for station_id, station in STATIONS.items():
                for matcher in station.get('content_matchers', []):
                    if re.search(matcher, content_id) or re.search(matcher, title):
                        # If station has a now playing service, use it
                        if 'now_playing_service' in station:
                            track = self.services[station['now_playing_service']].get_track()
                            if track:
                                track['station_id'] = station_id
                                self.current_track = track
                                return track
                        # Otherwise return basic station info
                        return {
                            'title': station['name'],
                            'artist': None,
                            'image_url': station['image'],
                            'source': station['name'],
                            'station_id': station_id
                        }

        return None

    def to_dict(self):
        """Convert current track info to dictionary"""
        track = self.get_current_track()
        if not track:
            return {
                'playing': False,
                'timestamp': datetime.now().isoformat()
            }

        # Try to cache track artwork, fall back to station logo
        artwork_url = None
        if track.get('image_url'):
            image_filename = f"{track['image_url'].split('/')[-1]}.jpg"
            if self.cache_image(track['image_url'], image_filename):
                artwork_url = f"/static/cache/{image_filename}"
            elif track.get('station_id'):
                # Fall back to station logo
                artwork_url = STATIONS[track['station_id']]['image']
        elif track.get('station_id'):
            # No track artwork, use station logo
            artwork_url = STATIONS[track['station_id']]['image']

        return {
            'playing': True,
            'title': track.get('title'),
            'artist': track.get('artist'),
            'artwork': artwork_url,
            'album': track.get('album'),
            'playlist': track.get('playlist'),
            'source': track.get('source'),
            'station_id': track.get('station_id'),
            'release_date': track.get('release_date'),
            'timestamp': datetime.now().isoformat()
        }
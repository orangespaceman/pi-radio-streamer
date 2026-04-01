import requests
import logging
import time
from .base import NowPlayingService

class FIPService(NowPlayingService):
    API_URL = "https://api.radiofrance.fr/livemeta/pull/7"
    REQUEST_TIMEOUT_SECONDS = 5

    def get_track(self):
        try:
            response = requests.get(self.API_URL, timeout=self.REQUEST_TIMEOUT_SECONDS)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    now_ts = int(time.time())
                    steps = data.get('steps', {})
                    if isinstance(steps, dict) and steps:
                        current_track = None
                        current_start = -1

                        for step in steps.values():
                            if not isinstance(step, dict):
                                continue
                            if step.get('embedType') != 'song':
                                continue

                            start = step.get('start')
                            end = step.get('end')
                            if not isinstance(start, int) or not isinstance(end, int):
                                continue

                            if start <= now_ts < end and start > current_start:
                                current_track = step
                                current_start = start

                        if current_track:
                            return {
                                'title': current_track.get('title', 'Unknown'),
                                'artist': current_track.get('authors', 'Unknown'),
                                'image_url': current_track.get('visual'),
                                'album': current_track.get('titreAlbum'),
                                'release_date': current_track.get('anneeEditionMusique'),
                                'source': 'FIP Radio'
                            }
            # If we can't access the API but we know FIP is playing, return basic info
            if self.cast and self.cast.media_controller.status:
                return {
                    'title': 'FIP Radio',
                    'artist': 'Radio France',
                    'image_url': None,
                    'source': 'FIP Radio'
                }
        except Exception as e:
            logging.debug(f"Error getting FIP track: {str(e)}")
        return None
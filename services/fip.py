import requests
import logging
from .base import NowPlayingService

class FIPService(NowPlayingService):
    API_URL = "https://www.radiofrance.fr/fip/api/live"

    def get_track(self):
        try:
            response = requests.get(self.API_URL)
            if response.status_code == 200:
                data = response.json()
                if 'now' in data:
                    track = data['now']
                    return {
                        'title': track.get('firstLine', {}).get('title', 'Unknown'),
                        'artist': track.get('secondLine', {}).get('title', 'Unknown'),
                        'image_url': track.get('visuals', {}).get('card', {}).get('src'),
                        'album': track.get('song', {}).get('release', {}).get('title'),
                        'release_date': track.get('song', {}).get('year'),
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
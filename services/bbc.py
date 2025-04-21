import requests
import logging
from .base import NowPlayingService

class BBC6Service(NowPlayingService):
    API_URL = "https://rms.api.bbc.co.uk/v2/services/bbc_6music/segments/latest"

    def get_track(self):
        try:
            response = requests.get(self.API_URL)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    track = data['data'][0]
                    image_url = track.get('image_url', '').replace('{recipe}', '640x640')

                    return {
                        'title': track.get('titles', {}).get('secondary', 'Unknown'),
                        'artist': track.get('titles', {}).get('primary', 'Unknown'),
                        'image_url': image_url,
                        'source': 'BBC 6 Music'
                    }
        except Exception as e:
            logging.debug(f"Error getting BBC6 track: {str(e)}")
        return None
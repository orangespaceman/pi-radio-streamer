import logging
import time
import requests

from .base import NowPlayingService


class RadioParadiseService(NowPlayingService):
    API_URL = "https://api.radioparadise.com/api/nowplaying_list_v2022?chan=0&list_num=1"
    REQUEST_TIMEOUT_SECONDS = 5
    MAX_PLAY_TIME_AGE_MS = 60 * 60 * 1000

    def get_track(self):
        try:
            response = requests.get(self.API_URL, timeout=self.REQUEST_TIMEOUT_SECONDS)
            if response.status_code != 200:
                return None

            data = response.json()
            songs = data.get("song", [])
            if not songs:
                return None

            current_song = songs[0]
            play_time = current_song.get("play_time")
            if not isinstance(play_time, int):
                return None

            now_ms = int(time.time() * 1000)
            # Ignore stale entries if API data is delayed or cached.
            if abs(now_ms - play_time) > self.MAX_PLAY_TIME_AGE_MS:
                return None

            cover_base_url = data.get("cover_base_url", "")
            cover_path = current_song.get("cover_med") or current_song.get("cover")
            image_url = f"{cover_base_url}{cover_path}" if cover_base_url and cover_path else None

            return {
                "title": current_song.get("title", "Unknown"),
                "artist": current_song.get("artist", "Unknown"),
                "album": current_song.get("album"),
                "image_url": image_url,
                "source": "Radio Paradise",
            }
        except Exception as error:
            logging.debug(f"Error getting Radio Paradise track: {str(error)}")
        return None

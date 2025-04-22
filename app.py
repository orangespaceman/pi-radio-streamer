from flask import Flask, render_template, jsonify
import pychromecast
import os
import logging
import socket
from dotenv import load_dotenv
from now_playing import NowPlaying
from pychromecast.controllers.bbcsounds import BbcSoundsController
from config.stations import STATIONS

# Load environment variables
load_dotenv()
CHROMECAST_NAME = os.getenv('CHROMECAST_NAME', 'Chromecast Audio')
FLASK_PORT = int(os.getenv('FLASK_PORT', 3001))
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize Chromecast and NowPlaying
cast = None
now_playing = None

def get_chromecast():
    global cast, now_playing
    if cast is None:
        logger.debug("Searching for Chromecast devices...")
        chromecasts, browser = pychromecast.get_chromecasts()
        for cc in chromecasts:
            if cc.name == CHROMECAST_NAME:
                logger.info(f"Found Chromecast: {CHROMECAST_NAME}")
                cast = cc
                cast.wait()
                now_playing = NowPlaying(cast)
                return cast
        logger.error(f"Chromecast {CHROMECAST_NAME} not found")
    return cast

def get_ip():
    """Get the local IP address of the machine"""
    try:
        # Create a socket to get the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't need to be reachable
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return 'Unknown'

@app.route('/')
def index_route():
    ip_address = get_ip()
    return render_template('index.html', stations=STATIONS, ip_address=ip_address, port=FLASK_PORT)

@app.route('/play/<station>')
def play_station_route(station):
    if station not in STATIONS:
        error_msg = f'Station {station} not found'
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 404

    try:
        cast = get_chromecast()
        if not cast:
            error_msg = f'Chromecast {CHROMECAST_NAME} not found'
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 404

        logger.debug(f"Playing station: {station}")
        mc = cast.media_controller

        # Stop current media and wait for app to disconnect
        mc.stop()
        cast.wait()

        # Wait for current app to fully disconnect
        if cast.app_id is not None:
            cast.quit_app()
            cast.wait()

        station_info = STATIONS[station]

        # For BBC stations, use BBC Sounds app
        if station in ['bbc6', 'bbc5live', 'bbc5extra']:
            # Launch BBC Sounds app
            sounds = BbcSoundsController()
            cast.register_handler(sounds)

            # Play BBC station with metadata
            sounds.quick_play(
                media_id=station_info['url'],
                is_live=True,
                metadata={
                    'metadataType': 0,
                    'title': station_info['name'],
                    'images': [{'url': station_info['image']}]
                }
            )
            return jsonify({'success': True, 'message': f'Playing {station_info["name"]}'})

        # For other stations (FIP, TalkSport), use standard media player
        media = {
            'url': station_info['url'],
            'title': station_info['name'],
            'thumb': station_info['image'],
            'media_type': station_info.get('media_type', 'audio/mp3'),
            'stream_type': 'LIVE',
            'metadata_type': 0,
            'metadata': {
                'title': station_info['name'],
                'images': [{'url': station_info['image']}]
            }
        }

        logger.debug(f"Media info: {media}")
        mc.play_media(media['url'], media['media_type'],
                     title=media['title'],
                     thumb=media['thumb'],
                     stream_type=media['stream_type'],
                     metadata=media['metadata'])
        mc.block_until_active()
        success_msg = f'Playing {station_info["name"]}'
        logger.info(success_msg)
        return jsonify({'success': True, 'message': success_msg})
    except Exception as e:
        error_msg = f'Error playing {station}: {str(e)}'
        logger.error(error_msg, exc_info=True if DEBUG else False)
        return jsonify({'error': error_msg}), 500

@app.route('/stop')
def stop_route():
    try:
        cast = get_chromecast()
        if not cast:
            error_msg = f'Chromecast {CHROMECAST_NAME} not found'
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 404

        logger.debug("Stopping playback")
        mc = cast.media_controller
        mc.stop()
        cast.quit_app()
        cast.wait()
        success_msg = 'Playback stopped'
        logger.info(success_msg)
        now_playing.clear_current_track()
        return jsonify({'success': True, 'message': success_msg})
    except Exception as e:
        error_msg = f'Error stopping playback: {str(e)}'
        logger.error(error_msg, exc_info=True if DEBUG else False)
        return jsonify({'error': error_msg}), 500

@app.route('/next')
def next_route():
    mc = cast.media_controller
    return update_playback(mc.queue_next)

@app.route('/prev')
def prev_route():
    mc = cast.media_controller
    return update_playback(mc.queue_prev)

@app.route('/pause')
def pause_route():
    mc = cast.media_controller
    return update_playback(mc.pause)

@app.route('/play')
def play_route():
    mc = cast.media_controller
    return update_playback(mc.play)

def update_playback(action):
    try:
        cast = get_chromecast()
        if not cast:
            error_msg = f'Chromecast {CHROMECAST_NAME} not found'
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 404

        logger.debug("Update playback")
        action()
        cast.wait()
        success_msg = 'Playback updated'
        logger.info(success_msg)
        return jsonify({'success': True, 'message': success_msg})
    except Exception as e:
        error_msg = f'Error updating playback: {str(e)}'
        logger.error(error_msg, exc_info=True if DEBUG else False)
        return jsonify({'error': error_msg}), 500

@app.route('/now-playing')
def now_playing_route():
    try:
        cast = get_chromecast()
        if not cast or not now_playing:
            logger.debug("No active playback")
            return jsonify({'playing': False})
        track_info = now_playing.to_dict()
        logger.debug(f"Now playing: {track_info}")
        return jsonify(track_info)
    except Exception as e:
        error_msg = f'Error getting now playing info: {str(e)}'
        logger.error(error_msg, exc_info=True if DEBUG else False)
        return jsonify({'error': error_msg}), 500

# Run the app
if __name__ == '__main__':
    logger.info(f"Starting server on port {FLASK_PORT}")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=DEBUG)
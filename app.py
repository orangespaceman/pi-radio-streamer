from flask import Flask, render_template, jsonify, redirect, request
import pychromecast
import os
import logging
import socket
import threading
from dotenv import load_dotenv
from now_playing import NowPlaying
from pychromecast.controllers.bbcsounds import BbcSoundsController
from config.stations import STATIONS, INCLUDE_SPORT
from services import spotify_items
import time

# Load environment variables
load_dotenv()
CHROMECAST_NAME = os.getenv('CHROMECAST_NAME', 'Chromecast Audio')
FLASK_PORT = int(os.getenv('FLASK_PORT', 3001))
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize Chromecast and NowPlaying
cast = None
now_playing = None
spotify_svc = None
cast_init_lock = threading.Lock()

def get_chromecast():
    global cast, now_playing, spotify_svc
    if cast is not None:
        return cast

    with cast_init_lock:
        if cast is not None:
            return cast

        logger.debug("Searching for Chromecast devices...")
        browser = None
        try:
            chromecasts, browser = pychromecast.get_listed_chromecasts(
                friendly_names=[CHROMECAST_NAME],
                discovery_timeout=5,
            )
            if not chromecasts:
                logger.error(f"Chromecast {CHROMECAST_NAME} not found")
                return None

            cast = chromecasts[0]
            logger.info(f"Found Chromecast: {CHROMECAST_NAME}")
            cast.wait()

            # Create a spotify redirect URI for the app itself, unless explicitly configured.
            ip_address = get_ip()
            redirect_uri = SPOTIFY_REDIRECT_URI or f"http://{ip_address}:{FLASK_PORT}/spotify/auth/callback"
            logger.info(f"Using Spotify redirect URI: {redirect_uri}")

            now_playing = NowPlaying(cast, spotify_redirect_uri=redirect_uri)

            # Initialize Spotify service reference
            if 'SpotifyService' in now_playing.services:
                spotify_svc = now_playing.services['SpotifyService']
                logger.info("Spotify service initialized")
        finally:
            if browser is not None:
                browser.stop_discovery()

    return cast


def get_ip():
    """Get the local IP address of the machine"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(('8.8.8.8', 80))
            return sock.getsockname()[0]
    except Exception:
        return 'Unknown'

@app.route('/')
def index_route():
    ip_address = get_ip()

    # Check for authentication status in query parameters
    status = None
    message = None

    if request.args.get('auth_success') == 'true':
        status = 'success'
        message = 'Spotify authentication successful'
    elif request.args.get('auth_error') == 'true':
        status = 'error'
        message = 'Spotify authentication failed'

    return render_template('index.html',
                          stations=STATIONS,
                          include_sport=INCLUDE_SPORT,
                          ip_address=ip_address,
                          port=FLASK_PORT,
                          status=status,
                          message=message)

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

        station_info = STATIONS[station]
        logger.debug(f"Playing station: {station}")
        mc = cast.media_controller

        # For BBC stations, use BBC Sounds cast app directly.
        if station_info.get('cast_app') == 'bbc_sounds':
            sounds = BbcSoundsController()
            cast.register_handler(sounds)
            sounds.play_media(
                station_info['url'],
                station_info.get('media_type', 'application/dash+xml'),
                title=station_info['name'],
                stream_type='LIVE',
                metadata={
                    'metadataType': 0,
                    'title': station_info['name'],
                },
                media_info={
                    'customData': {
                        'content_id_type': 'vpid',
                        'original_pid': station_info['url'],
                        'encoding': 'aac',
                        'image_identifier': station_info['url'],
                        'is_live_rewindable': False,
                    }
                },
            )
            media_status = None
            player_state = None
            idle_reason = None
            # BBC receiver can move through IDLE/LOADING before PLAYING.
            for _ in range(20):
                cast.wait()
                media_status = cast.media_controller.status
                player_state = getattr(media_status, 'player_state', None) if media_status else None
                idle_reason = getattr(media_status, 'idle_reason', None) if media_status else None
                if player_state in ['PLAYING', 'BUFFERING']:
                    break
                time.sleep(0.2)

            if player_state not in ['PLAYING', 'BUFFERING']:
                return jsonify({
                    'error': 'BBC station failed to start playback',
                    'player_state': player_state,
                    'idle_reason': idle_reason,
                }), 502

            track_info = now_playing.to_dict()
            track_info['success'] = True
            track_info['message'] = f'Playing {station_info["name"]}'
            return jsonify(track_info)

        # Non-BBC stations use the standard media app.
        # Stop current media and disconnect current app to avoid app conflicts.
        mc.stop()
        cast.wait()
        if cast.app_id is not None:
            cast.quit_app()
            cast.wait()

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
        track_info = now_playing.to_dict()
        track_info['success'] = True
        track_info['message'] = f'Playing {station_info["name"]}'
        return jsonify(track_info)
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
        now_playing.clear_current_track()
        track_info = now_playing.to_dict()
        track_info['success'] = True
        track_info['message'] = 'Playback stopped'
        return jsonify(track_info)
    except Exception as e:
        error_msg = f'Error stopping playback: {str(e)}'
        logger.error(error_msg, exc_info=True if DEBUG else False)
        return jsonify({'error': error_msg}), 500

@app.route('/next')
def next_route():
    return update_playback('next')

@app.route('/prev')
def prev_route():
    return update_playback('prev')

@app.route('/pause')
def pause_route():
    return update_playback('pause')

@app.route('/play')
def play_route():
    return update_playback('play')

def update_playback(action_name):
    try:
        cast = get_chromecast()
        if not cast:
            error_msg = f'Chromecast {CHROMECAST_NAME} not found'
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 404

        logger.debug("Update playback")

        # Get initial state
        initial_state = cast.media_controller.status.player_is_playing if cast.media_controller.status else False
        initial_content_id = str(cast.media_controller.status.content_id or '').lower() if cast.media_controller.status else None

        media_controller = cast.media_controller
        actions = {
            'next': media_controller.queue_next,
            'prev': media_controller.queue_prev,
            'pause': media_controller.pause,
            'play': media_controller.play,
        }
        action = actions.get(action_name)
        if action is None:
            return jsonify({'error': 'Invalid playback action'}), 400

        # Perform the action
        action()
        cast.wait()

        # Wait up to 1 second for state to change
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts:
            current_state = cast.media_controller.status.player_is_playing if cast.media_controller.status else False
            current_content_id = str(cast.media_controller.status.content_id or '').lower() if cast.media_controller.status else None

            # For prev/next, wait for content_id to change
            if action_name in ['next', 'prev']:
                if current_content_id != initial_content_id:
                    # Wait a bit more for metadata to update
                    time.sleep(0.2)
                    break
            # For play/pause, wait for player state to change
            elif current_state != initial_state:
                break

            time.sleep(0.1)
            attempt += 1

        # For prev/next, force a refresh to get new track info
        skip_api_refresh = action_name not in ['next', 'prev']
        track_info = now_playing.to_dict(skip_api_refresh=skip_api_refresh)
        track_info['success'] = True
        track_info['message'] = 'Playback updated'
        return jsonify(track_info)
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
        track_info = now_playing.to_dict(skip_api_refresh=True)

        # Add spotify control availability information if Spotify is playing
        if track_info.get('source') == 'Spotify' and spotify_svc:
            track_info['spotify_control_available'] = spotify_svc.is_chromecast_available()

        logger.debug(f"Now playing: {track_info}")
        return jsonify(track_info)
    except Exception as e:
        error_msg = f'Error getting now playing info: {str(e)}'
        logger.error(error_msg, exc_info=True if DEBUG else False)
        return jsonify({'error': error_msg}), 500

@app.route('/play-random-playlist')
def play_random_content_route():
    try:
        cast = get_chromecast()
        if not cast:
            error_msg = f'Chromecast {CHROMECAST_NAME} not found'
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 404

        # Ensure Spotify service is available
        if 'SpotifyService' not in now_playing.services:
            error_msg = 'Spotify service not available'
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 500

        spotify_service = now_playing.services['SpotifyService']

        # Check if user is authenticated with Spotify
        if not spotify_service.is_authenticated():
            error_msg = 'Not authenticated with Spotify'
            logger.info(error_msg)
            return jsonify({'error': error_msg}), 401

        # Try to play random content
        play_result = spotify_service.play_random_content()

        if play_result and not play_result.get('error'):
            # Give the service a moment to update
            time.sleep(1)
            track_info = now_playing.to_dict()
            track_info['success'] = True
            selected_name = play_result.get('selected_name')
            if selected_name:
                track_info['message'] = f'Started Spotify: {selected_name}'
            else:
                track_info['message'] = 'Started random Spotify content'
            track_info['spotify_control_available'] = True
            return jsonify(track_info)
        else:
            error_msg = 'Failed to start random Spotify content'
            if play_result and play_result.get('error'):
                error_msg = play_result.get('error')
            return jsonify({'error': error_msg}), 500

    except Exception as e:
        error_msg = f'Error playing random Spotify content: {str(e)}'
        logger.error(error_msg, exc_info=True if DEBUG else False)
        return jsonify({'error': error_msg}), 500

@app.route('/spotify/auth', methods=['GET'])
def spotify_auth():
    # Get the Spotify authorization URL from the service
    get_chromecast()  # Ensure Chromecast and services are initialized

    if spotify_svc is None:
        logger.error("Spotify service not initialized")
        return jsonify({"error": "Spotify service not initialized"}), 500

    # Log that we're starting auth
    logger.info("Starting Spotify authentication process")

    auth_url = spotify_svc.get_auth_url()
    if auth_url:
        logger.info(f"Redirecting to Spotify auth URL: {auth_url}")
        return redirect(auth_url)
    else:
        logger.error("Failed to generate Spotify auth URL")
        return jsonify({"error": "Failed to generate auth URL"}), 500

@app.route('/spotify/auth/callback', methods=['GET'])
def spotify_auth_callback():
    if spotify_svc is None:
        logging.error("Spotify service not initialized")
        return jsonify({"error": "Spotify service not initialized"}), 500

    # Get the callback parameters
    code = request.args.get('code')
    if not code:
        logging.error("No authorization code received from Spotify")
        error = request.args.get('error', 'Unknown error')
        return jsonify({"error": f"Authorization failed: {error}"}), 400

    # Handle the Spotify callback
    result = spotify_svc.handle_auth_callback(code)
    if result:
        # Redirect to home page with success parameter
        return redirect('/?auth_success=true')
    else:
        # Redirect to home page with error parameter
        return redirect('/?auth_error=true')

@app.route('/spotify/auth-status', methods=['GET'])
def spotify_auth_status():
    """Check if the user is authenticated with Spotify, without requiring content to be playing"""
    get_chromecast()
    if spotify_svc is None:
        logging.error("Spotify service not initialized")
        return jsonify({"error": "Spotify service not initialized"}), 500

    # Only check authentication status
    if spotify_svc.is_authenticated():
        return jsonify({"status": "authenticated", "authenticated": True})
    else:
        return jsonify({"status": "not_authenticated", "authenticated": False}), 401

# Spotify Items Management Routes
@app.route('/spotify/items', methods=['GET'])
def get_spotify_items():
    """Get all Spotify items"""
    items = spotify_items.get_items()

    # Add index to each item
    for i, item in enumerate(items):
        item['id'] = i

    return jsonify({
        "items": items
    })

@app.route('/spotify/items', methods=['POST'])
def add_spotify_item():
    """Add a new Spotify item"""
    data = request.get_json(silent=True)
    if not data or 'name' not in data or 'uri' not in data:
        return jsonify({"error": "Name and URI are required"}), 400

    success, message = spotify_items.add_item(data['name'], data['uri'])
    if success:
        return jsonify({"message": message}), 201
    else:
        return jsonify({"error": message}), 400

@app.route('/spotify/items/<int:item_id>', methods=['PUT'])
def update_spotify_item(item_id):
    """Update an existing Spotify item"""
    data = request.get_json(silent=True)
    if not data or 'name' not in data or 'uri' not in data:
        return jsonify({"error": "Name and URI are required"}), 400

    success, message = spotify_items.update_item(item_id, data['name'], data['uri'])
    if success:
        return jsonify({"message": message})
    else:
        return jsonify({"error": message}), 400

@app.route('/spotify/items/<int:item_id>', methods=['DELETE'])
def delete_spotify_item(item_id):
    """Delete a Spotify item"""
    success, message = spotify_items.delete_item(item_id)
    if success:
        return jsonify({"message": message})
    else:
        return jsonify({"error": message}), 400

@app.route('/spotify/manager')
def spotify_manager():
    """Render the Spotify items manager page"""
    return render_template('spotify_manager.html', ip_address=get_ip(), port=FLASK_PORT)

# Run the app
if __name__ == '__main__':
    logger.info(f"Starting server on port {FLASK_PORT}")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=DEBUG)
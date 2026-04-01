from dotenv import load_dotenv
import os

load_dotenv()

INCLUDE_SPORT = os.getenv('INCLUDE_SPORT', 'true').lower() == 'true'

STATIONS = {
    'bbc6': {
        'url': 'bbc_6music',
        'name': 'BBC 6 Music',
        'image': 'https://sounds.files.bbci.co.uk/2.3.0/networks/bbc_6music/blocks-colour_600x600.png',
        'media_type': 'application/dash+xml',
        'content_matchers': ['bbc_6music', 'bbc_radio_six'],
        'now_playing_service': 'BBC6Service',
        'cast_app': 'bbc_sounds'
    },
    'fip': {
        'url': 'https://icecast.radiofrance.fr/fip-hifi.aac?id=radiofrance',
        'name': 'FIP Radio',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/1/16/FIP_logo_2021.svg',
        'media_type': 'audio/mp3',
        'content_matchers': ['fip'],
        'now_playing_service': 'FIPService'
    },
    'radioparadise': {
        'url': 'http://stream-uk1.radioparadise.com/mp3-192',
        'name': 'Radio Paradise',
        'image': 'https://www.radioparadise.com/favicon.ico',
        'media_type': 'audio/mpeg',
        'content_matchers': ['radioparadise', 'stream-uk1\\.radioparadise\\.com'],
        'now_playing_service': 'RadioParadiseService'
    }
}

if INCLUDE_SPORT:
    STATIONS['bbc5live'] = {
        'url': 'bbc_radio_five_live',
        'name': 'BBC Radio 5 Live',
        'image': 'https://sounds.files.bbci.co.uk/2.3.0/networks/bbc_radio_five_live/blocks-colour_600x600.png',
        'media_type': 'application/dash+xml',
        'content_matchers': ['bbc_radio_five_live'],
        'cast_app': 'bbc_sounds'
    }

    STATIONS['bbc5extra'] = {
        'url': 'bbc_radio_five_live_sports_extra',
        'name': 'BBC Radio 5 Sports Extra',
        'image': 'https://sounds.files.bbci.co.uk/2.3.0/networks/bbc_radio_five_live_sports_extra/blocks-colour_600x600.png',
        'media_type': 'application/dash+xml',
        'content_matchers': ['bbc_radio_five_live_sports_extra'],
        'cast_app': 'bbc_sounds'
    }
    STATIONS['bbc5extra2'] = {
        'url': 'bbc_radio_five_sports_extra_2',
        'name': 'BBC Radio 5 Sports Extra 2',
        'image': 'https://sounds.files.bbci.co.uk/2.3.0/networks/bbc_radio_five_live_sports_extra/blocks-colour_600x600.png',
        'media_type': 'application/dash+xml',
        'content_matchers': ['bbc_radio_five_sports_extra_2'],
        'cast_app': 'bbc_sounds'
    }
    STATIONS['bbc5extra3'] = {
        'url': 'bbc_radio_five_sports_extra_3',
        'name': 'BBC Radio 5 Sports Extra 3',
        'image': 'https://sounds.files.bbci.co.uk/2.3.0/networks/bbc_radio_five_live_sports_extra/blocks-colour_600x600.png',
        'media_type': 'application/dash+xml',
        'content_matchers': ['bbc_radio_five_sports_extra_3'],
        'cast_app': 'bbc_sounds'
    }
    STATIONS['talksport'] = {
        'url': 'https://radio.talksport.com/stream',
        'name': 'talkSPORT',
        'image': 'https://talksport.com/play/logos/talksport.png',
        'media_type': 'audio/mp3',
        'content_matchers': ['talksport', 'stream(?!2)']
    }
    STATIONS['talksport2'] = {
        'url': 'https://radio.talksport.com/stream2',
        'name': 'talkSPORT 2',
        'image': 'https://talksport.com/play/logos/talksport2.png',
        'media_type': 'audio/mp3',
        'content_matchers': ['talksport.*stream2']
    }

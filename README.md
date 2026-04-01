# Pi Radio Streamer

Stream radio stations to a Chromecast via a Raspberry Pi

## Features

-   Stream BBC 6 Music, BBC Radio 5 Live, BBC Radio 5 Sports Extra, talkSPORT, talkSPORT 2 and FIP Radio
-   Also identify when Spotify is playing
-   Simple responsive web interface
-   Play/stop control
-   Start random playlists when Spotify is active

## Requirements

-   Raspberry Pi
-   Chromecast
-   Python 3.7 (or higher)
-   pip

## Installation

1. Clone this repository to your Raspberry Pi:

```bash
git clone [repository-url]
cd pi-radio-streamer
```

2. Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv env

# Activate virtual environment
source env/bin/activate
```

3. Install the required Python packages:

```bash
pip install -r requirements.txt
```

4. Configure your environment:

```bash
cp .env.example .env  # Copy the example environment file
nano .env             # Edit the environment variables
```

## Configuration

The following environment variables can be configured in the `.env` file:

-   `CHROMECAST_NAME`: The name of your Chromecast (default: "Chromecast Audio")
-   `FLASK_PORT`: The port to run the server on (default: 3001)
-   `DEBUG`: Enable debug mode (default: false)
-   `INCLUDE_SPORT`: Show sport stations too? (default: false)
-   `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`: Required for Spotify authentication, release dates, and random content playback

### Spotify Integration

For full Spotify integration, including the ability to start random Spotify content, you need to:

1. Create a Spotify Developer account at https://developer.spotify.com/
2. Create a new application in the Spotify Developer Dashboard
3. Add the redirect URI to your Spotify application settings. It must exactly match what the app uses:
   - Default: `http://<your-local-ip>:<FLASK_PORT>/spotify/auth/callback`
   - Or set `SPOTIFY_REDIRECT_URI` in `.env` and add that exact value in Spotify Dashboard -> Your App -> Edit Settings -> Redirect URIs
4. Copy your Client ID and Client Secret to the `.env` file
5. Configure Spotify content items in the web manager at `/spotify/manager`

#### Configuring Spotify Content

Spotify content is stored in `config/spotify_items.json` and can be managed via the Spotify manager page.

#### First-Time Authentication

1. Open the web UI in a browser
2. Use **Connect Spotify Account** (for example from the auth prompt when starting Spotify playback)
3. Sign in to Spotify and approve access; you are redirected back to the app
4. Tokens are cached in `.spotify_cache`

When Spotify is playing on your Chromecast, a Spotify button will appear in the station grid if authentication is successful and your Chromecast is available as a Spotify Connect device.

## Usage

### Running Manually

1. Make sure your virtual environment is activated:

```bash
source env/bin/activate
```

2. Start the application:

```bash
python app.py
```

3. Open a web browser and navigate to:

```
http://[your-raspberry-pi-ip]:[port]
```

4. Click on any radio station button to start streaming
5. Use the stop playback button to stop the current stream

### Running as a System Service

You can set up the application to run automatically when your Raspberry Pi starts up:

1. Copy the service file to the systemd directory:

```bash
sudo cp pi-radio-streamer.service /lib/systemd/system/
```

2. Update the file permissions:

```bash
sudo chmod 644 /lib/systemd/system/pi-radio-streamer.service
```

3. Enable and start the service:

```bash
sudo systemctl enable pi-radio-streamer.service
sudo systemctl start pi-radio-streamer.service
```

You can manage the service using these commands:

```bash
# Check status
sudo systemctl status pi-radio-streamer.service

# Stop service
sudo systemctl stop pi-radio-streamer.service

# Restart service
sudo systemctl restart pi-radio-streamer.service

# View logs
sudo journalctl -u pi-radio-streamer.service
```

## Troubleshooting

-   Make sure your Chromecast is on the same network as your Raspberry Pi
-   Check that the Chromecast is powered on and ready
-   Ensure no other devices are currently casting to the Chromecast
-   Check the service logs for any errors:
    ```bash
    sudo journalctl -u pi-radio-streamer.service -f
    ```
-   If the service fails to start, check your environment configuration in `.env`

## Notes

-   The application runs on port 3001 by default (configurable via `FLASK_PORT`)
-   The web interface can be accessed from any device on your local network
-   Stream URLs are subject to change and may need updating if they become invalid
-   To reduce output, set `FLASK_DEBUG=False` and `DEBUG=False` in your `.env` file
-   Remember to deactivate your virtual environment when you're done:
    ```bash
    deactivate
    ```

---

## Maintenance and support

[![No Maintenance Intended](http://unmaintained.tech/badge.svg)](http://unmaintained.tech/)

---

## License

This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.

```
            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                    Version 2, December 2004

 Copyright (C) 2004 Sam Hocevar <sam@hocevar.net>

 Everyone is permitted to copy and distribute verbatim or modified
 copies of this license document, and changing it is allowed as long
 as the name is changed.

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. You just DO WHAT THE FUCK YOU WANT TO.

```

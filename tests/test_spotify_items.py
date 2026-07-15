import unittest

from services.spotify_items import normalize_spotify_uri


class TestNormalizeSpotifyUri(unittest.TestCase):
    def test_spotify_uri_passes_through(self):
        self.assertEqual(
            normalize_spotify_uri('spotify:playlist:37i9dQZF1DX4sWSpwq3LiO'),
            'spotify:playlist:37i9dQZF1DX4sWSpwq3LiO',
        )

    def test_playlist_url(self):
        self.assertEqual(
            normalize_spotify_uri('https://open.spotify.com/playlist/37i9dQZF1DX4sWSpwq3LiO'),
            'spotify:playlist:37i9dQZF1DX4sWSpwq3LiO',
        )

    def test_album_url(self):
        self.assertEqual(
            normalize_spotify_uri('https://open.spotify.com/album/3iyn2K7YlhKie8qrmUV6lS'),
            'spotify:album:3iyn2K7YlhKie8qrmUV6lS',
        )

    def test_track_url_with_query_string(self):
        self.assertEqual(
            normalize_spotify_uri('https://open.spotify.com/track/6p2ZaQL49aH9OdVS4EqFNa?si=abc123'),
            'spotify:track:6p2ZaQL49aH9OdVS4EqFNa',
        )

    def test_plain_id_assumed_playlist(self):
        self.assertEqual(
            normalize_spotify_uri('37i9dQZF1DX4sWSpwq3LiO'),
            'spotify:playlist:37i9dQZF1DX4sWSpwq3LiO',
        )

    def test_invalid_format_returns_none(self):
        self.assertIsNone(normalize_spotify_uri('https://example.com/not-spotify'))
        self.assertIsNone(normalize_spotify_uri('not a uri'))


if __name__ == '__main__':
    unittest.main()

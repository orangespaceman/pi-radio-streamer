class NowPlayingService:
    def __init__(self, cast=None):
        self.cast = cast

    def get_track(self):
        """Get the currently playing track info. Should be implemented by subclasses."""
        raise NotImplementedError
import os


class Song:
    def __init__(self, artist, title, lyrics):
        self.artist = artist
        self.title = title
        self.lyrics = lyrics


class SearchConfig:
    def __init__(self, enabled_plugins=None, result_limit=None, cache_web_dir=None, cache_web_ttl_sec=None,
                 async=False):

        if cache_web_dir is None:
            cache_web_dir = os.path.expanduser('~') + '/.cache/prismriver/'

        if cache_web_ttl_sec is None:
            cache_web_ttl_sec = 60 * 60 * 24 * 7

        self.enabled_plugins = enabled_plugins
        self.result_limit = result_limit
        self.cache_web_dir = cache_web_dir
        self.cache_web_ttl_sec = cache_web_ttl_sec

        self.async = async

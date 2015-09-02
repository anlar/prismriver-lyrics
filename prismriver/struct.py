import os


class Song:
    def __init__(self, artist, title, lyrics):
        self.artist = artist
        self.title = title
        self.lyrics = lyrics


class SearchConfig:
    def __init__(self, enabled_plugins=None, result_limit=None, cache_web_dir=None, cache_web_ttl_sec=None,
                 web_timeout_sec=None, sync=False):

        if cache_web_dir is None:
            cache_web_dir = os.path.expanduser('~') + '/.cache/prismriver/'

        if cache_web_ttl_sec is None:
            cache_web_ttl_sec = 60 * 60 * 24 * 7

        if web_timeout_sec is None:
            web_timeout_sec = 10

        self.enabled_plugins = enabled_plugins
        self.result_limit = result_limit
        self.cache_web_dir = cache_web_dir
        self.cache_web_ttl_sec = cache_web_ttl_sec
        self.web_timeout_sec = web_timeout_sec

        self.sync = sync

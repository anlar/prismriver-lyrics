import logging
import os


class Song:
    def __init__(self, artist, title, lyrics):
        self.artist = artist
        self.title = title
        self.lyrics = lyrics


class SearchConfig:
    def __init__(self, enabled_plugins=None, result_limit=None, cache_web_dir=None, cache_web_ttl_sec=None,
                 web_timeout_sec=None, sync=False, parser=None, preprocessor=None):

        if cache_web_dir is None:
            cache_web_dir = os.path.expanduser('~') + '/.cache/prismriver/'

        if cache_web_ttl_sec is None:
            cache_web_ttl_sec = 60 * 60 * 24 * 7

        if web_timeout_sec is None:
            web_timeout_sec = 10

        if parser is None:
            parser = 'lxml'

        self.enabled_plugins = enabled_plugins
        self.result_limit = result_limit
        self.cache_web_dir = cache_web_dir
        self.cache_web_ttl_sec = cache_web_ttl_sec
        self.web_timeout_sec = web_timeout_sec

        self.sync = sync

        self.parser = self.get_parser_name(parser)

        self.preprocessor_opts = []
        if preprocessor:
            opts = preprocessor.split(',')
            self.preprocessor_opts.extend(opts)
        else:
            self.preprocessor_opts.append('trim')

        # debug options
        self.debug_log_page = False

    def get_parser_name(self, selected_parser):
        if selected_parser == 'lxml':
            if self.is_lxml_available():
                return 'lxml'
            elif self.is_html5lib_avaialable():
                self.log_parser_warning(selected_parser, 'html5lib')
                return 'html5lib'
        elif selected_parser == 'html5lib':
            if self.is_html5lib_avaialable():
                return 'html5lib'
            elif self.is_lxml_available():
                self.log_parser_warning(selected_parser, 'lxml')
                return 'lxml'
        elif selected_parser == 'html.parser':
            return 'html.parser'

        self.log_parser_warning(selected_parser, 'html.parser')
        return 'html.parser'

    def is_lxml_available(self):
        try:
            import lxml
            return True
        except ImportError:
            return False

    def is_html5lib_avaialable(self):
        try:
            import html5lib
            return True
        except ImportError:
            return False

    def log_parser_warning(self, selected, actual):
        logging.debug('Selected parser "{}" not available, fallback to "{}"'.format(selected, actual))

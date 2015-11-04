from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsPlacePlugin(Plugin):
    ID = 'lyricsplace'

    def __init__(self, config):
        super(LyricsPlacePlugin, self).__init__('Lyrics Place', config)

    def search_song(self, artist, title):
        to_delete = ["'", '.', ',', '!', '?', '(', ')']
        to_replace = [' & ', ' / ', ' ']
        link = 'http://lyricsplace.com/songs/{}/{}/{}.html'.format(
            self.prepare_url_parameter(artist[0]),
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace),
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace))

        # return 404 if song not found
        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            nav_pane = soup.find('ul', {'class': 'breadcrumbs'})
            if not nav_pane:
                # song not found (not all of them return 404)
                return None

            breadcrumbs = nav_pane.findAll('li', recursive=False)

            song_artist = breadcrumbs[2].a.text[:-7]
            song_title = breadcrumbs[3].span.text[:-12]

            lyrics_pane = soup.find('div', {'class': 'twelve columns lyric'})
            lyrics = self.parse_verse_block(lyrics_pane, tags_to_skip=['h1'])

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

    def prepare_url_parameter(self, value, to_delete=None, to_replace=None, delimiter='-', quote_uri=True,
                              safe_chars=None):
        return super().prepare_url_parameter(value, to_delete, to_replace, delimiter, quote_uri, safe_chars).lower()

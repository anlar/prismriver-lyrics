from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class AliveLyricsPlugin(Plugin):
    ID = 'alivelyrics'

    def __init__(self, config):
        super(AliveLyricsPlugin, self).__init__('AliveLyrics', config)

    def search_song(self, artist, title):
        to_delete = [' ', '.', ',', '&', '?', '!', "'", '"', '/', '(', ')']
        link = 'http://www.alivelyrics.com/{}/{}/{}.html'.format(
            self.prepare_url_parameter(artist[0]),
            self.prepare_url_parameter(artist, to_delete=to_delete),
            self.prepare_url_parameter(title, to_delete=to_delete))

        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            navbar = soup.find('div', {'class', 'navbar'})
            navbar_parts = navbar.findAll('a')

            song_artist = navbar_parts[2].text
            song_title = navbar_parts[3].next_sibling[2:].strip()

            lyrics_pane = soup.find('pre', {'class': 'lyrics'})
            lyrics = self.parse_verse_block(lyrics_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

    def prepare_url_parameter(self, value, to_delete=None, to_replace=None, delimiter='-', quote_uri=True,
                              safe_chars=None):
        return super().prepare_url_parameter(value, to_delete, to_replace, delimiter, quote_uri, safe_chars).lower()

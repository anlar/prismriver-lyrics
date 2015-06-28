from bs4 import BeautifulSoup

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class ELyricsPlugin(Plugin):
    def __init__(self):
        super().__init__('elyrics', 'eLyrics')

    def search(self, artist, title):
        to_replace = [' ']
        link = 'http://www.elyrics.net/read/{}/{}-lyrics/{}-lyrics.html' \
            .format(artist[0],
                    self.prepare_url_parameter(artist, None, to_replace, quote_uri=False),
                    self.prepare_url_parameter(title, None, to_replace, quote_uri=False))

        page = self.download_webpage(link)
        if page:
            soup = BeautifulSoup(page)

            head_pane = soup.find('div', {'class': ['navcnt', 'navcnt2']})

            song_artist = head_pane.findAll('a')[2].text.replace(' Lyrics', '')
            song_title = head_pane.find('strong', recursive=False).text.replace(' Lyrics', '')

            lyric_pane = soup.find('div', {'id': 'inlyr'})
            self.remove_tags_from_block(lyric_pane, ['p', 'div', 'form'])
            lyric = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

    def prepare_url_parameter(self, value, to_delete=None, to_replace=None, delimiter='-', quote_uri=True):
        return super().prepare_url_parameter(value.replace("'", '_'), to_delete, to_replace, delimiter, quote_uri)

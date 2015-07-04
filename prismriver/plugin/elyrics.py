from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class ELyricsPlugin(Plugin):
    def __init__(self):
        super().__init__('elyrics', 'eLyrics')

    def search(self, artist, title):
        link = 'http://www.elyrics.net/read/{}/{}-lyrics/{}-lyrics.html' \
            .format(artist[0], self.prepare_parameter(artist), self.prepare_parameter(title))

        page = self.download_webpage(link)
        if page:
            soup = self.prepare_soup(page)

            head_pane = soup.find('div', {'class': ['navcnt', 'navcnt2']})

            song_artist = head_pane.findAll('a')[2].text.replace(' Lyrics', '')
            song_title = head_pane.find('strong', recursive=False).text.replace(' Lyrics', '')

            lyric_pane = soup.find('div', {'id': 'inlyr'})
            self.remove_tags_from_block(lyric_pane, ['p', 'div', 'form'])
            lyric = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

    def prepare_parameter(self, value):
        return self.prepare_url_parameter(value.replace("'", '_'), None, [' '], quote_uri=True, safe_chars='/()')

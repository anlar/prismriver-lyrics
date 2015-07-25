from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class ELyricsPlugin(Plugin):
    PLUGIN_ID = 'elyrics'

    def __init__(self, config):
        super(ELyricsPlugin, self).__init__(self.PLUGIN_ID, 'eLyrics', config)

    def search_song(self, artist, title):
        to_replace = [' ']
        safe_chars = '()'

        link = 'http://www.elyrics.net/read/{}/{}-lyrics/{}-lyrics.html'.format(
            self.prepare_url_parameter(artist[0]),
            self.prepare_url_parameter(self.prepare_parameter(artist), to_replace=to_replace, safe_chars=safe_chars),
            self.prepare_url_parameter(self.prepare_parameter(title), to_replace=to_replace, safe_chars=safe_chars))

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
        return value.replace("'", '_').replace('-', ',,')

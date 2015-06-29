from bs4 import BeautifulSoup

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class NitroLyricsPlugin(Plugin):
    def __init__(self):
        super().__init__('nitrolyrics', 'NitroLyrics')

    def search(self, artist, title):
        to_delete = ['.', '(', ')', "'", ',', '.', '?', '-']
        to_replace = [' ', ' & ']
        link = 'http://www.nitrolyrics.com/{}_{}-lyrics.html'.format(
            self.prepare_url_parameter(artist, to_delete, to_replace),
            self.prepare_url_parameter(title, to_delete, to_replace))

        page = self.download_webpage(link)

        if page:
            soup = BeautifulSoup(page)

            head_pane = soup.find('div', {'class', 'lyric'})
            song_artist = head_pane.find('a').text
            song_title = head_pane.find('h1').text.replace(' Lyrics', '')

            lyric_pane = soup.find('div', {'class': 'lyricContent'})
            lyric = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

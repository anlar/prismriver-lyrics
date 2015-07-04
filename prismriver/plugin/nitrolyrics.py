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
            soup = self.prepare_soup(page)

            head_pane = soup.find('div', {'class', 'lyric'})
            if head_pane is None:
                # empty page - song not found
                return None

            song_artist = head_pane.find('a').text
            song_title = head_pane.find('h1').text.replace(' Lyrics', '')

            lyric_pane = soup.find('div', {'class': 'lyricContent'})
            lyric = self.parse_verse_block(lyric_pane.find('p'))

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

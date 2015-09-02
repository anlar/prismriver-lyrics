""" Random comments:
- they have an API: https://docs.genius.com/ (requires key and uses OAuth2)
"""

from bs4 import Comment, NavigableString, Tag

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class GeniusPlugin(Plugin):
    ID = 'genius'

    def __init__(self, config):
        super(GeniusPlugin, self).__init__('Genius', config)

    def search_song(self, artist, title):
        to_delete = ["'", '(', ')', '.', '?']
        to_replace = [' ']

        link = 'http://genius.com/{}-{}-lyrics'.format(
            self.prepare_url_parameter(artist.lower(), to_delete=to_delete, to_replace=to_replace),
            self.prepare_url_parameter(title.lower(), to_delete=to_delete, to_replace=to_replace))

        page = self.download_webpage(link)
        if page:
            soup = self.prepare_soup(page)

            artist_pane = soup.find('span', {'class': 'text_artist'}).a
            song_artist = artist_pane.text.strip()

            title_pane = soup.find('span', {'class': 'text_title'})
            song_title = title_pane.text.strip()

            lyric_pane = soup.find('div', {'class': 'lyrics'}).p
            lyric = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

    def parse_verse_block(self, verse_block):
        lyric = ''

        for elem in verse_block.childGenerator():
            if isinstance(elem, Comment):
                pass
            elif isinstance(elem, NavigableString):
                lyric += elem.strip()
            elif isinstance(elem, Tag):
                if elem.name == 'a':
                    lyric += elem.text.strip()
                else:
                    lyric += '\n'

        return lyric.strip()

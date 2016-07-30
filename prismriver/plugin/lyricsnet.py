import re

from bs4 import Comment
from bs4 import NavigableString
from bs4 import Tag

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsNetPlugin(Plugin):
    ID = 'lyricsnet'

    def __init__(self, config):
        super(LyricsNetPlugin, self).__init__('Lyrics.net', config)

    def search_song(self, artist, title):
        link = 'http://www.lyrics.net/artist/{}'.format(
                self.prepare_url_parameter(artist))

        page = self.download_webpage(link)

        if page:
            soup = self.prepare_soup(page)

            main_pane = soup.find('div', {'id': 'content-main'})
            artist_pane = main_pane.find('p', {'class': 'artist'})

            if not artist_pane:
                # artist page not found, redirected to search page
                return None

            song_artist = artist_pane.a.text

            if not self.compare_strings(artist, song_artist):
                return None

            for lyr_item in soup.findAll('a', href=re.compile('/lyric/[0-9]+')):
                song_title = lyr_item.text

                if self.compare_strings(title, song_title):
                    link = 'http://www.lyrics.net' + lyr_item['href']
                    page = self.download_webpage_text(link)
                    if page:
                        soup = self.prepare_soup(page)

                        lyric_pane = soup.find('pre', {'id': 'lyric-body-text'})
                        if lyric_pane:
                            lyric = self.parse_verse_block(lyric_pane)
                            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

    def parse_verse_block(self, verse_block, tags_to_skip=None):
        lyric = ''

        for elem in verse_block.childGenerator():
            if isinstance(elem, Comment):
                pass
            elif isinstance(elem, NavigableString):
                lyric += elem
            elif isinstance(elem, Tag) and elem.name == 'a':
                lyric += elem.text

        return lyric.strip()

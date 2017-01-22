import re

from bs4 import NavigableString
from bs4 import Tag, Comment

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsComPlugin(Plugin):
    ID = 'lyricscom'

    def __init__(self, config):
        super(LyricsComPlugin, self).__init__('Lyrics.com', config)

    def search_song(self, artist, title):
        artist_link = 'http://www.lyrics.com/artist/{}/'.format(self.prepare_url_parameter(artist))

        artist_page = self.download_webpage(artist_link)

        if artist_page:
            soup = self.prepare_soup(artist_page)

            artist_pane = soup.find('p', {'class': 'artist'})
            if not artist_pane:
                # artist page not found, redirect to search page
                return None

            song_artist = artist_pane.a.text

            for item in soup.findAll('a', href=re.compile('lyric/[0-9]+')):
                song_title = item.text

                if self.compare_strings(title, song_title):
                    song_link = 'http://www.lyrics.com' + item['href']

                    song_page = self.download_webpage(song_link)

                    if song_page:
                        soup = self.prepare_soup(song_page)

                        lyrics_pane = soup.find('pre', {'id': 'lyric-body-text'})
                        lyrics = self.parse_verse_block_custom(lyrics_pane)

                        return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

    def parse_verse_block_custom(self, verse_block):
        lyric = ''

        for elem in verse_block.childGenerator():
            if isinstance(elem, Comment):
                pass
            elif isinstance(elem, NavigableString):
                lyric += elem
            elif isinstance(elem, Tag):
                lyric += elem.text

        return lyric.strip()

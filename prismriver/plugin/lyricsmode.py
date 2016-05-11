from bs4 import Comment, NavigableString, Tag

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsModePlugin(Plugin):
    ID = 'lyricsmode'

    def __init__(self, config):
        super(LyricsModePlugin, self).__init__('LyricsMode', config)

    def search_song(self, artist, title):
        link = 'http://www.lyricsmode.com/lyrics/{}/{}/{}.html'.format(
            self.prepare_url_parameter(artist[0]),
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            nav_pane = soup.find('ul', {'class': 'breadcrumb'})
            breadcrumbs = nav_pane.findAll('li', recursive=False)

            song_artist = breadcrumbs[1].a.span.text
            song_title = breadcrumbs[2].contents[1][:-7]

            lyrics_pane = soup.find('p', {'id': 'lyrics_text'})
            lyrics = self.parse_verse_block_lm(lyrics_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

    def parse_verse_block_lm(self, verse_block):
        lyric = ''

        for elem in verse_block.childGenerator():
            if isinstance(elem, Comment):
                pass
            elif isinstance(elem, NavigableString):
                lyric += elem.strip('\n')
            elif isinstance(elem, Tag):
                if elem.name == 'span':
                    if lyric.endswith('\n'):
                        lyric += super().parse_verse_block(elem)
                    else:
                        lyric += super().parse_verse_block(elem)
                else:
                    lyric += '\n'

        return lyric.strip()

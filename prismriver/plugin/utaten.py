from bs4 import Comment, NavigableString, Tag

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class UtaTenPlugin(Plugin):
    ID = 'utaten'
    RANK = 9

    def __init__(self, config):
        super(UtaTenPlugin, self).__init__('UtaTen', config)

    def search_song(self, artist, title):
        link = 'http://utaten.com/lyric/{}/{}/'.format(
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            main_pane = soup.find('main')

            title_pane = main_pane.find('div', {'class': 'contentBox__title contentBox__title--lyricTitle'})
            if not title_pane:
                # song not found, redirected to main page
                return None

            title_pane_parts = title_pane.h1.contents

            song_title = title_pane_parts[0].strip()[1:-1]
            song_artist = title_pane_parts[3].text.strip()

            lyric_pane = main_pane.find('div', {'class': 'lyricBody'})
            lyric_pane = lyric_pane.find('div', {'class': 'medium'})

            lyric = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

    # todo: handle furigana
    def parse_verse_block(self, verse_block, tags_to_skip=None):
        lyric = ''

        for elem in verse_block.childGenerator():
            if isinstance(elem, Comment):
                pass
            elif isinstance(elem, NavigableString):
                lyric += elem.strip()
            elif isinstance(elem, Tag):
                if elem.name == 'span':
                    lyric += elem.find('span', {'class': 'rb'}, recursive=False).text
                else:
                    lyric += '\n'

        return lyric.strip()

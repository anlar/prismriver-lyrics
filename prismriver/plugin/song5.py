from bs4 import NavigableString, Comment, Tag

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class SongFivePlugin(Plugin):
    ID = 'song5'
    RANK = 2

    def __init__(self, config):
        super(SongFivePlugin, self).__init__('Song5', config)

    def search_song(self, artist, title):
        # no need to replace/delete symbols -- site will handle anything
        link = 'http://song5.ru/text/{}-{}'.format(
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        # returns 404 if song not found
        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            nav_pane = soup.find('ul', {'class': 'breadcrumb'})
            breadcrumbs = nav_pane.findAll('li', recursive=False)

            song_artist = breadcrumbs[1].a.text
            song_title = breadcrumbs[2].text

            lyrics_pane = soup.find('div', {'class': 'songtext'})
            lyric = self.parse_verse_block(lyrics_pane, tags_to_skip=['ul', 'script', 'ins', 'a', 'div'])

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

    def parse_verse_block(self, verse_block, tags_to_skip=None):
        lyric = ''

        for elem in verse_block.childGenerator():
            if isinstance(elem, Comment):
                pass
            elif isinstance(elem, NavigableString):
                if elem.strip() == 'Исполнитель:':
                    break
                else:
                    lyric += elem.strip()
            elif isinstance(elem, Tag):
                if not (tags_to_skip and elem.name in tags_to_skip):
                    lyric += '\n'

        return lyric.strip()

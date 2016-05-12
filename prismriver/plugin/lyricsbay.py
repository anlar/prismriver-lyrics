from bs4 import Tag

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsBayPlugin(Plugin):
    ID = 'lyricsbay'
    RANK = 4

    def __init__(self, config):
        super(LyricsBayPlugin, self).__init__('Lyrics Bay', config)

    def search_song(self, artist, title):
        to_delete = ['(', ')']
        to_replace = [' ']

        link = 'http://www.lyricsbay.com/{}-{}-lyrics'.format(
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace),
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace)).lower()

        # return 404 if song not found
        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            full_title = soup.head.title.text
            title_parts = full_title.split(' – ', 2)

            song_artist = title_parts[0]
            song_title = title_parts[1][:-7]

            lyrics_pane = soup.find('div', {'class': 'entry-content'})

            lyric = ''
            for elem in lyrics_pane.childGenerator():
                if isinstance(elem, Tag) and elem.name == 'p':
                    verse = self.parse_verse_block(elem, ['a'])
                    lyric += (verse + '\n\n')

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

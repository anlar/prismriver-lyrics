import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


# todo: load all translation versions

class LyrsensePlugin(Plugin):
    ID = 'lyrsense'

    def __init__(self, config):
        super(LyrsensePlugin, self).__init__('Lyrsense', config)

    def search_song(self, artist, title):
        link = 'http://lyrsense.com/search?s={}'.format(
            self.prepare_url_parameter(title))

        page = self.download_webpage(link)

        if page:
            soup = self.prepare_soup(page)

            song_info = self.parse_search_page(soup, artist, title)
            if not song_info:
                return None

            song_page = self.download_webpage_text(song_info[0])
            if song_page:
                soup = self.prepare_soup(song_page)

                lyrics = []
                lyric_blocks = soup.findAll('p', id=re.compile('.{2}_text'))

                for block in lyric_blocks:
                    lyric = self.parse_verse_block(block, tags_to_skip=['sup', 'div'])  # excluding footnotes
                    lyrics.append(lyric)

                return Song(song_info[1], song_info[2], self.sanitize_lyrics(lyrics))

    def parse_search_page(self, soup, artist, title):
        blocks = soup.findAll('ul', id=re.compile('song_.*List'))

        for block in blocks:
            for elem in block.findAll('li', {'class': 'element'}, recursive=False):
                song_title = elem.a.text
                song_artist = elem.contents[1][3:]
                song_link = elem.a['href']

                if self.compare_strings(artist, song_artist) and self.compare_strings(title, song_title):
                    return [song_link, song_artist, song_title]

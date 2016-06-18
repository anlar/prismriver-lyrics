import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class KashiNaviPlugin(Plugin):
    ID = 'kashinavi'
    RANK = 8

    def __init__(self, config):
        super(KashiNaviPlugin, self).__init__('KashiNavi', config)

    def search_song(self, artist, title):
        link = 'http://kashinavi.com/search.php?r=kyoku&search={}'.format(
            self.prepare_url_parameter(title, delimiter='+', quote_encoding='cp932'))

        page = self.download_webpage_text(link, 'shift_jis')

        if page:
            soup = self.prepare_soup(page)

            links = soup.findAll('a', href=re.compile('song_view.html\?\d?'), text=True)
            for link in links:
                song_artist = link.parent.find_next_sibling('td').text
                song_title = link.text
                song_link = link['href']

                if self.compare_strings(artist, song_artist) and self.compare_strings(title, song_title):
                    song_id = song_link.split('?', 2)[1]
                    lyric_link = 'http://kashinavi.com/s/kashi.php?no={}'.format(song_id)

                    page = self.download_webpage_text(lyric_link, 'shift_jis')
                    if page:
                        lyrics = page[page.index('>') + 1:page.rfind('<')].replace('<br>', '\n')
                        return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

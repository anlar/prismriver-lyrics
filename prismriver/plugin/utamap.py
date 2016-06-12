import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class UtaMapPlugin(Plugin):
    ID = 'utamap'
    RANK = 9

    def __init__(self, config):
        super(UtaMapPlugin, self).__init__('UtaMap', config)

    def search_song(self, artist, title):
        link = 'http://www.utamap.com/searchkasi.php?searchname=title&word={}'.format(
                self.prepare_url_parameter(title, delimiter='+'))

        page = self.download_webpage_text(link, encoding='shift_jis')

        if page:
            soup = self.prepare_soup(page)

            links = soup.findAll('a', href=re.compile('\./showkasi.php\?surl=.*'))
            for link in links:
                song_artist = link.parent.find_next_sibling('td').text
                song_title = link.text
                song_link = link['href']

                if self.compare_strings(artist, song_artist) and self.compare_strings(title, song_title):
                    song_id = song_link.split('=', 2)[1]
                    lyric_link = 'http://www.utamap.com/phpflash/flashfalsephp.php?unum={}'.format(song_id)

                    page = self.download_webpage_text(lyric_link)
                    if page:
                        lyric = page[15:]
                        return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class EvestaPlugin(Plugin):
    ID = 'evesta'

    def __init__(self, config):
        super(EvestaPlugin, self).__init__('Evesta', config)

    def search_song(self, artist, title):
        link = 'http://www.evesta.jp/lyric/search2.php?t={}&ct=2&a={}&ca=2'.format(
            self.prepare_url_parameter(title),
            self.prepare_url_parameter(artist))

        page = self.download_webpage(link)
        if page:
            soup = self.prepare_soup(page)

            search_result_pane = soup.find('div', {'id': 'lyricList'})
            if search_result_pane is None:
                return None

            first_result = search_result_pane.table.findAll('tr')[1]
            result_parts = first_result.findAll('a')

            song_title = result_parts[0].text
            song_artist = result_parts[1].text
            song_link = result_parts[0]['href']

            lyric_page = self.download_webpage(song_link)
            soup = self.prepare_soup(lyric_page)

            main_lyric_pane = soup.find('div', {'id': 'lyricview'})
            inner_lyric_pane = main_lyric_pane.find('div', {'class': 'body'}).p
            lyric = self.parse_verse_block(inner_lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

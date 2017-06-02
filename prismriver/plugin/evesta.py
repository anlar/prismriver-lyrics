from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class EvestaPlugin(Plugin):
    ID = 'evesta'

    def __init__(self, config):
        super(EvestaPlugin, self).__init__('Evesta', config)

    def search_song(self, artist, title):
        link = 'http://lyric.evesta.jp/search.php?kind=title&keyword={}&how=2&do={}'.format(
            self.prepare_url_parameter(title),
            self.prepare_url_parameter('検索'))

        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            search_result_pane = soup.find('div', {'id': 'searchresult'})
            if search_result_pane is None:
                return None

            song_id = None
            song_artist = None
            song_title = None

            for item in search_result_pane.findAll('div', {'class': 'result'}):
                song_id = item.find('a', {'class': 'title'})['href']
                song_title = item.find('a', {'class': 'title'}).text
                song_artist = item.find('p', {'class': 'artist'}).a.text

                if self.compare_strings(title, song_title) and self.compare_strings(artist, song_artist):
                    break

            if not song_id:
                return

            lyric_page = self.download_webpage('http://lyric.evesta.jp' + song_id)
            soup = self.prepare_soup(lyric_page)

            lyric_pane = soup.find('div', {'id': 'lyricbody'})
            lyric = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class KGetPlugin(Plugin):
    def __init__(self):
        super(KGetPlugin, self).__init__('kget', 'KGet')

    def search(self, artist, title):
        link = 'http://www.kget.jp/search/index.php?r={}&t={}'.format(
            self.prepare_url_parameter(artist, delimiter='+'),
            self.prepare_url_parameter(title, delimiter='+'))

        page = self.download_webpage(link)

        if page:
            soup = self.prepare_soup(page)

            lyric_list_pane = soup.find('div', {'class': 'title-wrap cf'})
            if lyric_list_pane is None:
                # empty search result list
                return None

            artist_pane = lyric_list_pane.find('p', {'class': 'artist'}).find('a')
            song_artist = artist_pane.text

            title_pane = lyric_list_pane.find('a', {'class': 'lyric-anchor'})
            song_title = title_pane.find('h2', {'class': 'title'}).text
            song_link = 'http://www.kget.jp' + title_pane['href']

            lyric_page = self.download_webpage(song_link)
            soup = self.prepare_soup(lyric_page)

            lyric_pane = soup.find('div', {'id': 'lyric-trunk'})
            lyric = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

""" Random comments:
- if song wasn't found it will return 404
- link should be lower-cased
- all spaces and punctuation characters should be deleted
"""

from prismriver.plugin.common import Plugin

from prismriver.struct import Song


class AZLyricsPlugin(Plugin):
    PLUGIN_ID = 'azlyrics'

    def __init__(self, config):
        super(AZLyricsPlugin, self).__init__(self.PLUGIN_ID, 'AZLyrics', config)

    def search_song(self, artist, title):
        to_delete = [' ', ',', '.', '-', '?', '!', '/', '&', "'", '(', ')']

        link = 'http://www.azlyrics.com/lyrics/{}/{}.html'.format(
            self.prepare_url_parameter(artist, to_delete),
            self.prepare_url_parameter(title, to_delete)).lower()

        page = self.download_webpage(link)

        if page:
            soup = self.prepare_soup(page)

            head_pane = soup.find('div', {'class': 'lyricsh'})
            song_artist = head_pane.find('b').text.replace(' LYRICS', '')

            main_pane = soup.find('div', {'class': 'col-xs-12 col-lg-8 text-center'})
            song_title = main_pane.find('b', recursive=False).text[1:-1]

            lyric_pane = main_pane.find('div', {'class': None}, recursive=False)
            lyric = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

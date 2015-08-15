import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class BopFmPlugin(Plugin):
    PLUGIN_ID = 'bopfm'

    def __init__(self, config):
        super(BopFmPlugin, self).__init__(self.PLUGIN_ID, 'bop.fm', config)

    def search_song(self, artist, title):
        to_delete = [',', '-', '!', '/', "'", '(', ')', '[', ']']
        to_replace = [' ']

        link = 'https://bop.fm/s/{}/{}'.format(
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace),
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace)).lower()

        page = self.download_webpage(link)

        if page:
            soup = self.prepare_soup(page)

            lyric_pane = soup.find('div', {'data-render': 'song-lyrics'})
            if not lyric_pane:
                # lyrics not available for that song
                return

            inner_lyric_pane = lyric_pane.find('div', class_=re.compile('text'), recursive=False)

            lyric = ''
            for verse_block in inner_lyric_pane.findAll('p'):
                lyric += self.parse_verse_block(verse_block)
                lyric += '\n\n'

            info_pane = soup.find('div', {'class': 'info-details'})
            song_artist = info_pane.find('div', {'title': not None}, recursive=False)['title']
            song_title = info_pane.find('h1', {'title': not None}, recursive=False).text

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

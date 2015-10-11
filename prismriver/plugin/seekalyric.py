import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class SeekaLyricPlugin(Plugin):
    ID = 'seekalyric'

    def __init__(self, config):
        super(SeekaLyricPlugin, self).__init__('SeekaLyric', config)

    def search_song(self, artist, title):
        to_replace = [' ', '(', ')', '[', ']', '.', ',', '"', "'", '-', '!', '?']
        link = 'http://www.seekalyric.com/song/{}/{}'.format(
            self.prepare_url_parameter(artist, to_replace=to_replace, delimiter='_'),
            self.prepare_url_parameter(title, to_replace=to_replace, delimiter='_'))

        page = self.download_webpage(link)

        if page:
            soup = self.prepare_soup(page)

            profile_pane = soup.find('ul', {'id': 'FP_HR_Song2'})
            if not profile_pane:
                # song not found, we're redirected to main page
                return None
            profile_parts = profile_pane.findAll('li', {'class': 'line0S'})

            song_artist = profile_parts[0].a.text
            song_title = profile_parts[1].text

            lyrics_pane = soup.find('div', {'id': 'contentt'})
            lyrics = self.parse_verse_block(lyrics_pane)
            lyrics = re.sub(' +', ' ', lyrics)  # replace multiple spaces with one

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

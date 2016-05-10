import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsManiaPlugin(Plugin):
    ID = 'lyricsmania'

    def __init__(self, config):
        super(LyricsManiaPlugin, self).__init__('LyricsMania', config)

    def search_song(self, artist, title):
        to_delete = ['.', "'", '?', '(', ')']
        to_replace = [' ', ' & ']

        link = 'http://www.lyricsmania.com/{}_lyrics_{}.html'.format(
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace, delimiter='_'),
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace, delimiter='_'))

        page = self.download_webpage(link)

        if page:
            soup = self.prepare_soup(page)
            main_pane = soup.find('div', {'class': 'lyrics-body'})
            if main_pane is None:
                # song wasn't found on site and we're redirected on main page where we can't find lyric pane
                return None
            else:
                main_pane = main_pane.find('div', {'class': 'fb-quotable'})

            # search for artist and title
            header_pane = soup.find('div', {'class': 'lyrics-nav'})
            song_title = header_pane.find('h2').text
            song_title = re.sub(' lyrics$', '', song_title)
            song_artist = header_pane.find('h3').text

            # first part of lyrics to the left of video block
            lyric1 = self.parse_verse_block(main_pane)

            lyric_pane = main_pane.find('div', {'class': 'p402_premium'})

            # second part of lyrics below of video block
            lyric2 = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric1 + '\n\n' + lyric2]))

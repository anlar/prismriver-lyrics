import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class SongLyricsPlugin(Plugin):
    ID = 'songlyrics'

    def __init__(self, config):
        super(SongLyricsPlugin, self).__init__('SongLyrics.com', config)

    def search_song(self, artist, title):
        to_delete = [',', '(', ')', '&', '"', '?']
        to_replace = [' ', "'", '.']

        link = 'http://www.songlyrics.com/{}/{}-lyrics/'.format(
            self.prepare_url_parameter(artist.lower(), to_delete=to_delete, to_replace=to_replace, delimiter='-'),
            self.prepare_url_parameter(title.lower(), to_delete=to_delete, to_replace=to_replace, delimiter='-'))

        page = self.download_webpage(link)
        if page:
            soup = self.prepare_soup(page)

            title_pane = soup.find('div', {'class': 'pagetitle'})
            song_artist = title_pane.find('p', recursive=False).a.text
            title_header = title_pane.find('h1', recursive=False).text
            song_title = re.findall('.*? - (.*?) Lyrics', title_header)[0]

            lyric_pane = soup.find('p', {'id': 'songLyricsDiv'})
            lyric = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

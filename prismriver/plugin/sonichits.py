""" Random comments:
- api access requires some parts of UA to be set, otherwise return 404
"""

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class SonicHitsPlugin(Plugin):
    ID = 'sonichits'
    RANK = 7

    def __init__(self, config):
        super(SonicHitsPlugin, self).__init__('SonicHits', config)

    def search_song(self, artist, title):
        link = 'http://sonichits.com/api/lyrics?artist={}&track={}'.format(
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        page = self.download_webpage_json(link)
        if page:
            song_artist = page['artist']
            song_title = page['track']
            lyrics = page['lyrics'].replace('\r', '').replace('<br>', '\n')

            if lyrics.startswith('<span class="lyrics-text">No lyrics found for this song.'):
                return None
            else:
                return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

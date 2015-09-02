import json

from prismriver.plugin.common import Plugin
from prismriver.struct import Song

# API doc: http://api.vagalume.com.br/docs/

class VagalumePlugin(Plugin):
    ID = 'vagalume'

    def __init__(self, config):
        super(VagalumePlugin, self).__init__('Vagalume', config)

    def search_song(self, artist, title):
        link = 'http://api.vagalume.com.br/search.php?art={}&mus={}'.format(
            self.prepare_url_parameter(artist), self.prepare_url_parameter(title)
        )

        page = self.download_webpage_text(link)
        if page:
            resp = json.loads(page)
            if resp['type'] != 'exact':
                return None

            song_artist = resp['art']['name']
            song_title = resp['mus'][0]['name']
            lyric = resp['mus'][0]['text']

            if lyric.startswith('Shortcut to '):
                # lyric is empty, just list of other songs
                return None
            else:
                return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

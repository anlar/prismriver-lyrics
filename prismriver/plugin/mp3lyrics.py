from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class Mp3LyricsPlugin(Plugin):
    ID = 'mp3lyrics'

    def __init__(self, config):
        super(Mp3LyricsPlugin, self).__init__('Mp3Lyrics', config)

    def search_song(self, artist, title):
        link = 'http://mp3lyrics.com/?_return_json_=/Search/Advanced/?Artist={}&Track={}'.format(
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        page = self.download_webpage_json(link)
        if page:
            total_hits = page['SearchResult']['TotalHits']
            if total_hits == 0:
                return None

            song_id = page['SearchResult']['Tracks'][0]['Id']
            song_link = 'http://mp3lyrics.com/?_return_json_=/Lyric/{}/'.format(song_id)

            song_page = self.download_webpage_json(song_link)
            if song_page:
                song_artist = song_page['LyricModel']['ArtistName']
                song_title = song_page['LyricModel']['TrackTitle']
                lyric = song_page['LyricModel']['LyricsText']

                return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

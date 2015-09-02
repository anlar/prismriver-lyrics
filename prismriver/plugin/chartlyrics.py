from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class ChartlyricsPlugin(Plugin):
    ID = 'chartlyrics'
    RANK = 3

    def __init__(self, config):
        super(ChartlyricsPlugin, self).__init__('Chartlyrics', config)

    def search_song(self, artist, title):
        link = "http://api.chartlyrics.com/apiv1.asmx/SearchLyricDirect?artist={}&song={}".format(
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        xml_root = self.download_xml(link)
        if xml_root:
            song_artist = xml_root.find("LyricArtist").text
            song_title = xml_root.find("LyricSong").text
            song_lyric = xml_root.find("Lyric").text

            if not self.compare_strings(artist, song_artist):
                # search engine usually may return songs that has at least one matching word in title and artist,
                # so we should check at least one of them
                return

            if song_lyric:
                return Song(song_artist, song_title, self.sanitize_lyrics([song_lyric]))

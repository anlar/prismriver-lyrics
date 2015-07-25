from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LololyricsPlugin(Plugin):
    PLUGIN_ID = 'lololyrics'

    def __init__(self, config):
        super(LololyricsPlugin, self).__init__(self.PLUGIN_ID, 'Lololyrics', config)

    def search_song(self, artist, title):
        link = 'http://api.lololyrics.com/0.5/getLyric?artist={}&track={}'.format(
            self.prepare_url_parameter(artist), self.prepare_url_parameter(title)
        )

        xml_root = self.download_xml(link)
        if xml_root:
            lyric = xml_root.find("response").text
            return Song(artist, title, self.sanitize_lyrics([lyric]))

from bs4 import BeautifulSoup

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsManiaPlugin(Plugin):
    def __init__(self):
        super().__init__('lyricsmania', "LyricsMania")

    def search(self, artist, title):
        link = "http://www.lyricsmania.com/{}_lyrics_{}.html".format(self.simplify_url_parameter(title),
                                                                     self.simplify_url_parameter(artist))
        page = self.download_webpage(link)

        if page:
            soup = BeautifulSoup(page)
            main_pane = soup.find("div", {"class": "lyrics-body"})
            lyric_pane = main_pane.find("div", {"class": "p402_premium"})

            lyric = self.parse_verse_block(lyric_pane)

            return Song(artist, title, self.sanitize_lyrics([lyric]))

    def simplify_url_parameter(self, value):
        simplified = value.translate({ord("("): None, ord(")"): None, ord("'"): None, ord(" "): "_"})
        return self.quote_uri(simplified)

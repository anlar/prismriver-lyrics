from bs4 import BeautifulSoup, NavigableString, Tag

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyrsterPlugin(Plugin):
    def __init__(self):
        super().__init__('lyrster', "Lyrster")

    def search(self, artist, title):
        link = "http://www.lyrster.com/lyrics/{}-lyrics-{}.html".format(self.prepare_url_parameter(title),
                                                                        self.prepare_url_parameter(artist))

        page = self.download_webpage(link)
        if page:
            soup = BeautifulSoup(page)

            head_pane = soup.find("div", {"id": "lyrics-info"})
            song_title = head_pane.find("h1").text.replace(" Lyrics", "")
            song_artist = head_pane.find("a").text

            lyric_pane = soup.find("div", {"id": "lyrics"})
            lyric = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

    def parse_verse_block(self, verse_block):
        lyric = ''
        for elem in verse_block.recursiveChildGenerator():
            if isinstance(elem, NavigableString):
                lyric += elem.strip()
            elif isinstance(elem, Tag):
                lyric += '\n'
        return lyric.strip()

    def prepare_url_parameter(self, value):
        simplified = value.translate({ord("'"): None,
                                      ord("!"): None,
                                      ord("("): None,
                                      ord(")"): None,
                                      ord("["): None,
                                      ord("]"): None,
                                      ord(" "): "-"}
                                     )
        return self.quote_uri(simplified.casefold())

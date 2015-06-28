from bs4 import BeautifulSoup, NavigableString, Tag

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LeosLyricsPlugin(Plugin):
    def __init__(self):
        super().__init__('leoslyrics', "Leo's Lyrics")

    def search(self, artist, title):
        link = "http://www.leoslyrics.com/{}/{}-lyrics/".format(self.prepare_url_parameter(artist),
                                                                self.prepare_url_parameter(title))

        page = self.download_webpage(link)
        if page:
            soup = BeautifulSoup(page)

            head_pane = soup.find("ul", {"class": "breadcrumbs"})
            head_pane_parts = head_pane.findAll("li")

            song_artist = head_pane_parts[2].text
            song_title = head_pane_parts[3].text

            main_pane = soup.find("div", {"class": "song text-center"})
            lyric_pane = main_pane.find("div")
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
        simplified = value.translate({ord(":"): None,
                                      ord("'"): None,
                                      ord(","): None,
                                      ord("&"): None,
                                      ord("["): None,
                                      ord("]"): None,
                                      ord("'"): "-",
                                      ord("."): "-",
                                      ord(" "): "-"}
                                     )
        return self.quote_uri(simplified)

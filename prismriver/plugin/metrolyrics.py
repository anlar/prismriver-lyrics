from bs4 import BeautifulSoup, NavigableString, Tag

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class MetroLyricsPlugin(Plugin):
    def __init__(self):
        super().__init__('metrolyrics', 'MetroLyrics')

    def search(self, artist, title):
        link = "http://www.metrolyrics.com/{}-lyrics-{}.html".format(self.simplify_url_parameter(title),
                                                                     self.simplify_url_parameter(artist))

        page = self.download_webpage(link)

        if page:
            soup = BeautifulSoup(page)

            lyric_pane = soup.find("div", {"id": "lyrics-body-text"})

            lyric = ''
            for verse_pane in lyric_pane.findAll("p", {"class": "verse"}):
                for elem in verse_pane.recursiveChildGenerator():
                    if isinstance(elem, NavigableString):
                        lyric += elem.strip()
                    elif isinstance(elem, Tag):
                        lyric += '\n'

                lyric += '\n\n'

            return Song(artist, title, self.sanitize_lyrics([lyric]))

    def simplify_url_parameter(self, value):
        simplified = value.translate({ord("("): None, ord(")"): None, ord("'"): None, ord(" "): "-"})
        return self.quote_uri(simplified)

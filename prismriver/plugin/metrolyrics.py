from bs4 import BeautifulSoup

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
                verse = self.parse_verse_block(verse_pane)
                lyric += (verse + '\n\n')

            return Song(artist, title, self.sanitize_lyrics([lyric]))

    def simplify_url_parameter(self, value):
        simplified = value.translate({ord("("): None, ord(")"): None, ord("'"): None, ord(" "): "-"})
        return self.quote_uri(simplified)

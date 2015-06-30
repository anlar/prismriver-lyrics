from bs4 import BeautifulSoup

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
            if head_pane is None:
                # song wasn't found and we're redirected to main page
                return None

            song_title = head_pane.find("h1").text.replace(" Lyrics", "")
            song_artist = head_pane.find("a").text

            lyric_pane = soup.find("div", {"id": "lyrics"})
            lyric = self.parse_verse_block(lyric_pane)

            if lyric != "We do not have the complete song's lyrics just yet.":
                return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

    def prepare_url_parameter(self, value):
        simplified = value.translate({ord("'"): None,
                                      ord("!"): None,
                                      ord("("): None,
                                      ord(")"): None,
                                      ord("["): None,
                                      ord("]"): None,
                                      ord(" "): "-"}
                                     )
        return self.quote_uri(simplified.lower())

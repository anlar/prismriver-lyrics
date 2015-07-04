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
            soup = self.prepare_soup(page)
            main_pane = soup.find("div", {"class": "lyrics-body"})
            if main_pane is None:
                # song wasn't found on site and we're redirected on main page where we can't find lyric pane
                return None

            # first part of lyrics to the left of video block
            lyric1 = self.parse_verse_block(main_pane)

            lyric_pane = main_pane.find("div", {"class": "p402_premium"})

            # second part of lyrics below of video block
            lyric2 = self.parse_verse_block(lyric_pane)

            return Song(artist, title, self.sanitize_lyrics([lyric1 + '\n' + lyric2]))

    def simplify_url_parameter(self, value):
        simplified = value.translate({ord("("): None, ord(")"): None, ord("'"): None, ord(" "): "_"})
        return self.quote_uri(simplified)

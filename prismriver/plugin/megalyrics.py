from bs4 import BeautifulSoup

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class MegalyricsPlugin(Plugin):
    def __init__(self):
        super().__init__('megalyrics', 'Megalyrics')

    def search(self, artist, title):
        link = "http://megalyrics.ru/lyric/{}/{}.htm".format(self.simplify_url_parameter(artist),
                                                             self.simplify_url_parameter(title))
        page = self.download_webpage(link)

        if page:
            soup = BeautifulSoup(page)
            main_pane = soup.find("div", {"id": "txt"})

            if main_pane:
                lyrics = []

                if main_pane.find("div", {"class": "switch-block"}):
                    # first page type: original and translated bound together as a string by string translation
                    lyric_pane = main_pane.find("div", {"id": "song_text"})
                    lyrics = self.parse_dual_text_pane(lyric_pane)
                else:
                    # second page type: original text and then it's translation
                    for lyric_pane in main_pane.findAll("div", {"class": "text separate"}):
                        html_text = lyric_pane.find("div", {"class": "text_inner"})

                        if html_text:
                            lyric = self.parse_verse_block(html_text)
                        else:
                            lyric = self.parse_verse_block(lyric_pane)

                        lyrics.append(lyric)

                    if len(lyrics) == 0:  # song wasn't found - empty page
                        return None

                title_pane = soup.find("div", {"class": "title_w"})
                title_values = title_pane.get_text().split(" - ")

                song_artist = title_values[0]
                song_title = title_values[1]

                return Song(song_artist, song_title, self.sanitize_lyrics(lyrics))

    def simplify_url_parameter(self, value):
        simplified = value.translate({ord(" "): "-"})
        return self.quote_uri(simplified)

    def parse_dual_text_pane(self, lyric_pane):
        lyric_original = ''
        for item in lyric_pane.findAll("div", {"class": "text"}):
            lyric_original += item.get_text()
            lyric_original += '\n'

        lyric_translate = ''
        for item in lyric_pane.findAll("div", {"class": "transl"}):
            lyric_translate += item.get_text()
            lyric_translate += '\n'

        return [lyric_original, lyric_translate]

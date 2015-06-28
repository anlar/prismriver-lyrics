from bs4 import BeautifulSoup, NavigableString, Tag

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class MegalyricsPlugin(Plugin):
    def __init__(self):
        super().__init__('megalyrics', 'Megalyrics')

    def search(self, artist, title):
        link = "http://megalyrics.ru/lyric/{}/{}.htm".format(self.quote_uri(artist), self.quote_uri(title))
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
                            lyric = self.parse_text_pane(html_text)
                        else:
                            lyric = self.parse_text_pane(lyric_pane)

                        lyrics.append(lyric)

                title_pane = soup.find("div", {"class": "title_w"})
                title_values = title_pane.get_text().split(" - ")

                song_artist = title_values[0]
                song_title = title_values[1]

                return Song(song_artist, song_title, self.sanitize_lyrics(lyrics))

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

    def parse_text_pane(self, html_text):
        lyric = ''

        for elem in html_text.recursiveChildGenerator():
            if isinstance(elem, NavigableString):
                lyric += elem.strip()
            elif isinstance(elem, Tag):
                lyric += '\n'

        return lyric

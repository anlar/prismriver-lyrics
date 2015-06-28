from bs4 import BeautifulSoup

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsHuddlePlugin(Plugin):
    def __init__(self):
        super().__init__('lyricshuddle', 'LyricsHuddle')

    def search(self, artist, title):
        to_delete = ['!', '?', '(', ')', "'", '"', ',']
        to_replace = [' ', ' & ', ' / ', '/', ':']
        link = "http://www.lyricshuddle.com/{}/{}/{}.html".format(artist[0],
                                                                  self.prepare_url_parameter(artist, to_delete,
                                                                                             to_replace),
                                                                  self.prepare_url_parameter(title, to_delete,
                                                                                             to_replace))

        page = self.download_webpage(link)
        if page:
            soup = BeautifulSoup(page)

            head_pane = soup.find("div", {"class": "location"})
            head_pane_parts = head_pane.findAll("a")

            song_artist = head_pane_parts[2].text
            song_title = head_pane_parts[3].text

            main_pane = soup.find("div", {"class": "lyricstext"})
            [x.extract() for x in main_pane.findAll('div')]
            [x.extract() for x in main_pane.findAll('style')]
            lyric = self.parse_verse_block(main_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

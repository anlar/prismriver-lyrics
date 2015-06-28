from bs4 import BeautifulSoup

from prismriver.plugin.common import Plugin
from prismriver.struct import Song

# TouhouWiki lyric pages guidelines:
# 1) http://en.touhouwiki.net/wiki/Touhou_Wiki:Guidelines#Lyrics_article_guidelines
# 2) http://en.touhouwiki.net/wiki/Template:Lyrics

# todo:
# - check artist name
# - songs with different lyrics but same name

class TouhouWikiPlugin(Plugin):
    def __init__(self):
        super().__init__('touhouwiki', 'TouhouWiki')

    def search(self, artist, title):
        link = "http://en.touhouwiki.net/wiki/Lyrics:_" + self.quote_uri(title)
        page = self.download_webpage(link)

        if page:
            soup = BeautifulSoup(page)

            # artist
            title_bar = soup.find("th", {"class": "incell_top"})
            song_artist = title_bar.find('a').get_text()

            # if artist.casefold() != song_artist.casefold():
            #     return None

            # title
            title_bar = soup.find("h1", {"id": "firstHeading"})
            song_title = title_bar.get_text().replace("Lyrics: ", "", 1)

            # lyrics
            lyrics = []
            main_table = soup.find("table", {"class": "template_lyrics outcell"})

            for cell_title in main_table.findAll("th", {"class": "incell"}):
                cell_title_text = cell_title.get_text()
                if cell_title_text in ('Original', 'Romanized', 'Translation'):
                    lyrics.append('')

            if len(lyrics) == 0:
                lyrics.append('')

            for row in main_table.findAll("tr", {"class": "lyrics_row"}):
                verse_num = 0
                for verse in row.findAll("p"):
                    lyrics[verse_num] += (verse.get_text() + '\n')
                    verse_num += 1

            return Song(song_artist, song_title, self.sanitize_lyrics(lyrics))

        else:
            return None

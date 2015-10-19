from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsActionPlugin(Plugin):
    ID = 'lyricsaction'

    def __init__(self, config):
        super(LyricsActionPlugin, self).__init__('Lyrics Action', config)

    def search_song(self, artist, title):
        # it seems that they can handle any symbol in link and redirect it correct page so there is no need replace and
        # delete anything
        link = 'http://www.lyricsaction.com/{}/{}/{}-lyrics.htm'.format(
            self.prepare_url_parameter(artist[0]),
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            main_pane = soup.find('div', {'class', 'node'})

            title_pane = main_pane.find('h2', recursive=False)
            title_parts = title_pane.text.split(' lyrics - ', 2)

            song_artist = title_parts[0]
            song_title = title_parts[1]

            lyrics_pane = main_pane.find('div', {'class': 'entry'}, recursive=False).p
            lyrics = self.parse_verse_block(lyrics_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

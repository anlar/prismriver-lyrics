from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class MetroLyricsPlugin(Plugin):
    PLUGIN_ID = 'metrolyrics'

    def __init__(self, config):
        super(MetroLyricsPlugin, self).__init__(self.PLUGIN_ID, 'MetroLyrics', config)

    def search_song(self, artist, title):
        to_delete = ["'", '(', ')']
        to_replace = [' ']

        link = "http://www.metrolyrics.com/{}-lyrics-{}.html".format(
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace),
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace))

        page = self.download_webpage(link)

        if page:
            soup = self.prepare_soup(page)

            lyric_pane = soup.find("div", {"id": "lyrics-body-text"})
            if lyric_pane is None:  # song not found
                return None

            lyric = ''
            for verse_pane in lyric_pane.findAll("p", {"class": "verse"}):
                verse = self.parse_verse_block(verse_pane)
                lyric += (verse + '\n\n')

            if lyric.strip():
                # if lyric is empty that mean that they've only empty stub page for that song
                return Song(artist, title, self.sanitize_lyrics([lyric]))

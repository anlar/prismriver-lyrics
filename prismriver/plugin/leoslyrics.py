from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LeosLyricsPlugin(Plugin):
    PLUGIN_ID = 'leoslyrics'

    def __init__(self, config):
        super(LeosLyricsPlugin, self).__init__(self.PLUGIN_ID, "Leo's Lyrics", config)

    def search_song(self, artist, title):
        to_delete = [',', '"', '?', '!', '(', ')', '[', ']']
        to_replace = [' ', '.', "'", ' & ']

        link = "http://www.leoslyrics.com/{}/{}-lyrics/".format(
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace),
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace))

        page = self.download_webpage(link)
        if page:
            soup = self.prepare_soup(page)

            head_pane = soup.find("ul", {"class": "breadcrumbs"})
            head_pane_parts = head_pane.findAll("li")

            song_artist = head_pane_parts[2].text
            song_title = head_pane_parts[3].text

            main_pane = soup.find("div", {"class": "song text-center"})
            lyric_pane = main_pane.find("div")
            lyric = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

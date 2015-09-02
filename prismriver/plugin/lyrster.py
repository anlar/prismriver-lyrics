from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyrsterPlugin(Plugin):
    ID = 'lyrster'

    def __init__(self, config):
        super(LyrsterPlugin, self).__init__('Lyrster', config)

    def search_song(self, artist, title):
        to_delete = ["'", '!', '(', ')', '[', ']']

        link = "http://www.lyrster.com/lyrics/{}-lyrics-{}.html".format(
            self.prepare_url_parameter(title, to_delete=to_delete),
            self.prepare_url_parameter(artist, to_delete=to_delete))

        page = self.download_webpage(link)
        if page:
            soup = self.prepare_soup(page)

            head_pane = soup.find("div", {"id": "lyrics-info"})
            if head_pane is None:
                # song wasn't found and we're redirected to main page
                return None

            song_title = head_pane.find("h1").text.replace(" Lyrics", "")
            song_artist = head_pane.find("a").text

            lyric_pane = soup.find("div", {"id": "lyrics"})
            lyric = self.parse_verse_block(lyric_pane)

            if lyric == "We do not have the complete song's lyrics just yet." or lyric.startswith('Shortcut to '):
                # empty song page without lyric
                return None
            else:
                return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

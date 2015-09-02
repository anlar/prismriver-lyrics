from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsRegPlugin(Plugin):
    ID = 'lyricsreg'

    def __init__(self, config):
        super(LyricsRegPlugin, self).__init__('LyricsReg.com', config)

    def search_song(self, artist, title):
        to_delete = ['(', ')', "'", ',']

        link = 'http://www.lyricsreg.com/lyrics/{}/{}/'.format(
            self.prepare_url_parameter(artist.replace(' & ', ' and '), to_delete=to_delete),
            self.prepare_url_parameter(title.replace(' & ', ' and '), to_delete=to_delete))

        page = self.download_webpage(link)
        if page:
            soup = self.prepare_soup(page)

            main_pane = soup.find('section', {'id': 'maincontent'})

            header = main_pane.find('h2', {'class': 'content-subhead'})
            artist_title = header.text.split(' lyrics : ')
            song_artist = artist_title[0]
            song_title = artist_title[1][1:-1]

            lyric_pane = main_pane.find('div', recursive=False)
            lyric = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

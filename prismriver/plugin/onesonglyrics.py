from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class OneSongLyricsPlugin(Plugin):
    ID = '1songlyrics'

    def __init__(self, config):
        super(OneSongLyricsPlugin, self).__init__('1 Song Lyrics', config)

    def search_song(self, artist, title):
        # no need to delete/replace chars - site will handle redirects
        link = 'http://www.1songlyrics.com/{}/{}/{}.html'.format(
            self.prepare_url_parameter(artist[0]),
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            main_pane = soup.find('div', {'id': 'wrapper'})
            headers = main_pane.findAll('h2', recursive=False)

            song_artist = headers[1].text
            song_title = headers[0].text[:-12]

            lyrics_pane = soup.findAll('p', {'class': False})[1]
            lyrics = self.parse_verse_block(lyrics_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

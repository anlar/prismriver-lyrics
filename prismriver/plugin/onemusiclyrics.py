from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class OneMusicLyricsPlugin(Plugin):
    ID = '1musiclyrics'

    def __init__(self, config):
        super(OneMusicLyricsPlugin, self).__init__('1 Music Lyrics', config)

    def search_song(self, artist, title):
        to_replace = ['.', ',', "'", '!', '?', '&', '(', ')', '-', '>', '/', ' ']
        link = 'http://www.1musiclyrics.net/{}/{}/{}.html'.format(
            self.prepare_url_parameter(artist[0]),
            self.prepare_url_parameter(artist, to_replace=to_replace, delimiter='_'),
            self.prepare_url_parameter(title, to_replace=to_replace, delimiter='_'))

        # return 404 if song not found
        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            if soup.html.title.text == '1 Music Lyrics':
                # song not found, redirected to main page
                return None

            main_pane = soup.find('div', {'id': 'welcomeBox'})

            title_parts = main_pane.findAll('h1', {'id': 'welcomeText'}, recursive=False)
            song_artist = title_parts[1].text
            song_title = title_parts[0].text[:-13]

            lyrics_pane = main_pane.find('p', {'class': False}, recursive=False)
            lyrics = self.parse_verse_block(lyrics_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

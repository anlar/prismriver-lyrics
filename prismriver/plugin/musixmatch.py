from prismriver.plugin.common import Plugin
from prismriver.struct import Song


# todo: load lyrics translations

class MusixmatchPlugin(Plugin):
    ID = 'musixmatch'
    RANK = 6

    def __init__(self, config):
        super(MusixmatchPlugin, self).__init__('Musixmatch', config)

    def search_song(self, artist, title):
        to_delete = ['!', '"', '(', ')']
        to_replace = [' ', '.', "'", ' + ']

        link = 'https://www.musixmatch.com/lyrics/{}/{}'.format(
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace),
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace))

        # return 404 if song not found
        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            title_pane = soup.find('div', {'class': 'mxm-track-title'})

            song_artist = title_pane.find('a').text
            song_title = title_pane.find('h1', recursive=False).text

            base_lyrics_pane = soup.find('div', {'class': 'mxm-lyrics'})

            lyrics = ''
            for lyrics_pane in base_lyrics_pane.findAll('p', {'class': 'mxm-lyrics__content'}):
                lyrics += (lyrics_pane.text + '\n')

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

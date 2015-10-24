from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class AlphabetLyricsPlugin(Plugin):
    ID = 'alphabetlyrics'

    def __init__(self, config):
        super(AlphabetLyricsPlugin, self).__init__('Alphabet Lyrics', config)

    def search_song(self, artist, title):
        to_delete = ['.', ',', "'", '?', '/', '(', ')', '!']
        to_replace = [' ']
        link = 'http://alphabetlyrics.com/lyrics/{}/{}.html'.format(
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace, delimiter='_'),
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace, delimiter='_'))

        page = self.download_webpage_text(link)
        # return 404 if song not found
        if page:
            soup = self.prepare_soup(page)

            nav_bar = soup.find('div', {'class': 'songlist bglyric2'})
            song_artist = nav_bar.findAll('a', recursive=False)[1].text
            song_title = nav_bar.find('b', recursive=False).text

            lyrics_pane = soup.findAll('div', {'class': 'lyrics'})[1]

            lyrics = ''
            for elem in lyrics_pane.findAll(['div', 'br'], recursive=False):
                lyrics += (elem.text.strip() + '\n')

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

    def prepare_url_parameter(self, value, to_delete=None, to_replace=None, delimiter='-', quote_uri=True,
                              safe_chars=None):
        return super().prepare_url_parameter(value, to_delete, to_replace, delimiter, quote_uri, safe_chars).lower()

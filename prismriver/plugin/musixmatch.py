from prismriver.plugin.common import Plugin
from prismriver.struct import Song


# todo: load lyrics translations, eg:
# https://www.musixmatch.com/lyrics/%E6%9E%97%E5%8E%9F%E3%82%81%E3%81%90%E3%81%BF/Over-Soul

class MusixmatchPlugin(Plugin):
    ID = 'musixmatch'
    RANK = 6

    def __init__(self, config):
        super(MusixmatchPlugin, self).__init__('Musixmatch', config)

    def search_song(self, artist, title):
        # no need to delete/replace chars - site will handle redirects
        link = 'https://www.musixmatch.com/lyrics/{}/{}'.format(
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        # return 404 if song not found
        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            title_pane = soup.find('div', {'class': 'media-card-text'})

            song_artist = title_pane.find('a').text
            song_title = title_pane.find('h1').span.text

            lyrics_pane = soup.find('span', {'id': 'lyrics-html'})
            lyrics = self.parse_verse_block(lyrics_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

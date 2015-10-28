from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsBayPlugin(Plugin):
    ID = 'lyricsbay'
    RANK = 3

    def __init__(self, config):
        super(LyricsBayPlugin, self).__init__('Lyrics Bay', config)

    def search_song(self, artist, title):
        to_replace = ["'", ' ']
        link = 'http://www.lyricsbay.com/{}_lyrics-{}.html'.format(
            self.prepare_url_parameter(title, to_replace=to_replace, delimiter='_'),
            self.prepare_url_parameter(artist, to_replace=to_replace, delimiter='_'))

        # return 404 if song not found
        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            full_title = soup.head.title.text
            title_parts = full_title.split(' Song Lyrics by ', 2)

            song_artist = title_parts[1]
            song_title = title_parts[0]

            lyrics_pane = soup.find('div', {'class': 'lyrics_text'})
            lyrics = self.parse_verse_block(lyrics_pane, tags_to_skip=['div'])

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

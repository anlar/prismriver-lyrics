import json

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


# API doc: http://www.lyricsnmusic.com/api
# It says that you need key to access it but it works fine without it (you still can generate it without registration).

class LyricsNMusicPlugin(Plugin):
    PLUGIN_ID = 'lyricsnmusic'

    def __init__(self, config):
        super(LyricsNMusicPlugin, self).__init__(self.PLUGIN_ID, 'Lyrics N Music', config)

    def search_song(self, artist, title):
        link = 'http://api.lyricsnmusic.com/songs?artist={}&track={}'.format(
            self.prepare_url_parameter(artist), self.prepare_url_parameter(title)
        )

        page = self.download_webpage_text(link)
        if page:
            resp = json.loads(page)

            song_artist = None
            song_title = None
            song_link = None

            for elem in resp:
                song_artist = elem['artist']['name']
                song_title = elem['title']
                viewable = elem['viewable']  # may be unavailable due to licensing issue

                if viewable and self.compare_strings(artist, song_artist) and self.compare_strings(title, song_title):
                    song_link = elem['url']
                    break

            if song_link:
                page = self.download_webpage(song_link)
                if page:
                    soup = self.prepare_soup(page)

                    lyric_block = soup.find('pre', {'itemprop': 'description'})
                    lyric = self.parse_verse_block(lyric_block)

                    return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

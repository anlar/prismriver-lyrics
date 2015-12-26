import time

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class SongsLyricsPlugin(Plugin):
    ID = 'songslyrics'

    def __init__(self, config):
        super(SongsLyricsPlugin, self).__init__('Songs Lyrics', config)

    def search_song(self, artist, title):
        link = 'http://www.songs-lyrics.net/lyrics-search.php?ar={}&so={}&submit=Search'.format(
                self.prepare_url_parameter(artist),
                self.prepare_url_parameter(title))

        page = self.download_webpage(link)

        if page:
            soup = self.prepare_soup(page)

            results_pane = soup.find('table', {'class': 'table2'})
            for item in results_pane.findAll('td', {'class': 'text'}):
                tags = item.findAll('a', recursive=False)

                song_artist = tags[0].text
                song_title = tags[2].text[:-7]
                song_link = 'http://www.songs-lyrics.net' + tags[2]['href']

                if self.compare_strings(artist, song_artist) and self.compare_strings(title, song_title):
                    # can't send 2 consecutive requests - it will throw too many requests from your ip error
                    time.sleep(2)
                    page = self.download_webpage_text(song_link)
                    if page:
                        soup = self.prepare_soup(page)

                        main_pane = soup.find('div', {'class': 'row panels'})
                        lyric_pane = main_pane.findAll('div', recursive=False)[1]
                        lyric = self.parse_verse_block(lyric_pane, tags_to_skip=['div', 'table', 'h5'])

                        return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

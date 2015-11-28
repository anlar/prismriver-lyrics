import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class JetLyricsPlugin(Plugin):
    ID = 'jetlyrics'

    def __init__(self, config):
        super(JetLyricsPlugin, self).__init__('JetLyrics', config)

    def search_song(self, artist, title):
        link = 'http://lyrics.jetmute.com/search.php?q={}+{}&search=Search'.format(
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        page = self.download_webpage(link, headers={'Referer': 'http://lyrics.jetmute.com/index.php'})
        if page:
            results = self.get_search_results(page, artist, title)

            if results:
                song_artist = results[0][0]
                song_title = results[0][1]

                lyrics = []
                for result in results:
                    lyric = self.get_lyric(result[2])
                    lyrics.append(lyric)

                return Song(song_artist, song_title, self.sanitize_lyrics(lyrics))

            return None

    def get_search_results(self, page, artist, title):
        soup = self.prepare_soup(page)
        center_pane = soup.find('center')
        links = center_pane.findAll('a', href=re.compile('http://lyrics.jetmute.com/viewlyrics.*'), recursive=False)

        full_title = '{} - {} Lyrics'.format(title, artist)
        results = []
        for link in links:
            if self.compare_strings(link.text, full_title):
                [song_title, song_artist] = link.text[:-7].split(' - ', 2)
                results.append([song_artist, song_title, link['href']])

        return results

    def get_lyric(self, link):
        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)
            lyric_pane = soup.find('div', {'id': 'lyricsText'})
            lyric = self.parse_verse_block(lyric_pane, tags_to_skip=['noscript'])
            return lyric

import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class BandcampPlugin(Plugin):
    ID = 'bandcamp'
    RANK = 8

    def __init__(self, config):
        super(BandcampPlugin, self).__init__('Bandcamp', config)

    def search_song(self, artist, title):
        # search terms should begin with title, otherwise engine do not return track entries
        link = 'https://bandcamp.com/search?q={}+{}'.format(
                self.prepare_url_parameter(title),
                self.prepare_url_parameter(artist))

        page = self.download_webpage_text(link)

        if page:
            soup = self.prepare_soup(page)

            results_pane = soup.find('ul', {'class': 'result-items'})
            for item in results_pane.findAll('li', {'class': 'searchresult track'}):
                info_pane = item.find('div', {'class': 'result-info'}, recursive=False)
                head_pane = info_pane.find('div', {'class': 'heading'}).a

                song_link = head_pane['href']
                song_title = head_pane.text.strip()

                subhead_pane = info_pane.find('div', {'class': 'subhead'})
                subhead = subhead_pane.text.strip()
                mobj = re.match('.*by (?P<id>.*)', subhead, re.DOTALL)
                song_artist = mobj.group('id')

                if self.compare_strings(song_artist, artist) and self.compare_strings(song_title, title):
                    page = self.download_webpage_text(song_link)
                    if page:
                        soup = self.prepare_soup(page)

                        lyric_pane = soup.find('div', {'class': 'tralbumData lyricsText'})
                        if lyric_pane:
                            lyric = self.parse_verse_block(lyric_pane)
                            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

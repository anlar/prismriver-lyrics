import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LetsSingItPlugin(Plugin):
    ID = 'letssingit'

    def __init__(self, config):
        super(LetsSingItPlugin, self).__init__('LetsSingIt', config)

    def search_song(self, artist, title):
        link = 'https://search.letssingit.com/?s={}+{}&a=search&l=archive'.format(
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        page = self.download_webpage(link, headers={'Referer': 'https://www.letssingit.com/'})

        if page:
            soup = self.prepare_soup(page)
            search_result = self.parse_search_page(soup, artist, title)

            if search_result:
                page = self.download_webpage(search_result[2])
                soup = self.prepare_soup(page)

                lyric_pane = soup.find('div', {'id': 'lyrics'})

                if lyric_pane.find('span', {'id': 'container_lyrics_request'}, recursive=False):
                    # song without lyric, contains "request these lyrics" button
                    return None

                lyric = self.parse_verse_block(lyric_pane, tags_to_skip=['div'])

                return Song(search_result[0], search_result[1], self.sanitize_lyrics([lyric]))

    def parse_search_page(self, soup, artist, title):
        search_table = soup.find('table', {'class': re.compile('table_as_list.?')}).find('tbody', recursive=False)
        if not search_table:
            return []

        for item in search_table.findAll('tr', recursive=False):
            info_pane = item.findAll('td')[1]
            info_items = info_pane.findAll('a', {'href': not None})

            song_title = info_items[0].text[:-7]  # remove ' lyrics' from the end
            song_artist = info_items[1].text

            if self.compare_strings(artist, song_artist) and self.compare_strings(title, song_title):
                return [song_artist, song_title, info_items[0]['href']]

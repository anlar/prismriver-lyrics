from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsFreakPlugin(Plugin):
    ID = 'lyricsfreak'

    def __init__(self, config):
        super(LyricsFreakPlugin, self).__init__('LyricsFreak', config)

    def search_song(self, artist, title):
        link = 'http://www.lyricsfreak.com/search.php?a=search&type=song&q={}'.format(
                self.prepare_url_parameter(title))

        page = self.download_webpage(link)

        if page:
            soup = self.prepare_soup(page)

            search_result = self.parse_search_page(soup, artist, title)

            if search_result:
                page = self.download_webpage_text(search_result[2])

                if page:
                    soup = self.prepare_soup(page)

                    lyric_pane = soup.find('div', {'id': 'content_h'})
                    lyric = self.parse_verse_block(lyric_pane)

                    return Song(search_result[0], search_result[1],
                                self.sanitize_lyrics([lyric], remove_duplicate_spaces=True))

    def parse_search_page(self, soup, artist, title):
        pane = soup.find('div', {'class': 'colortable green'})
        if pane:
            pane = pane.table.tbody

            for elem in pane.findAll('tr', recursive=False):
                item_artist = elem.find('td', {'class': 'colfirst'}, recursive=False).a.text[1:].strip()

                title_pane = elem.find('a', {'class': 'song'})
                item_title = title_pane.text[:-7]
                item_link = title_pane['href']

                if self.compare_strings(artist, item_artist) and self.compare_strings(title, item_title):
                    return [item_artist, item_title, 'http://www.lyricsfreak.com' + item_link]

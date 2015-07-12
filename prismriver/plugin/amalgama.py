""" Random comments:
- if song wasn't found it will return 404
- link should be lower-cased
- some song links may use custom patterns so can't create one universal
"""

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class AmalgamaPlugin(Plugin):
    def __init__(self):
        super(AmalgamaPlugin, self).__init__('amalgama', 'Amalgama')

    def search(self, artist, title):
        to_delete = ['.', ',', '!', '?', '(', ')', '*']
        to_replace = [' ', "'", '-']

        link = 'http://www.amalgama-lab.com/songs/{}/{}/{}.html'.format(
            self.prepare_url_parameter(artist[0]),
            self.prepare_url_parameter(artist, to_delete, to_replace, delimiter='_'),
            self.prepare_url_parameter(title, to_delete, to_replace, delimiter='_')).lower()

        page = self.download_webpage(link)

        if page:
            soup = self.prepare_soup(page)

            head_pane = soup.find('div', {'id': 'breadcrumbs_nav'})
            head_pane_parts = head_pane.findAll('a', recursive=False)

            song_artist = head_pane_parts[3].text
            song_title = head_pane.findAll(text=True, recursive=False)[-1].strip()

            lyric_pane = soup.find('div', {'id': 'click_area'})
            lyrics = self.parse_verse_block(lyric_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics(lyrics))

    def parse_verse_block(self, verse_block):
        original = ''
        translation = ['']
        translation_no = 0

        for elem in verse_block.findAll('div', {'class': ['string_container', 'empty_container']}):
            if elem.find('strong'):
                # translation delimiter
                translation_no += 1
                translation.append('')
            else:
                lyric1 = elem.find('div', {'class': 'original'}).text.strip()
                lyric2 = elem.find('div', {'class': 'translate'}).text.strip()

                if translation_no == 0:
                    original += (lyric1 + '\n')
                    translation[0] += (lyric2 + '\n')
                else:
                    translation[translation_no] += (lyric2 + '\n')

        return [original] + translation

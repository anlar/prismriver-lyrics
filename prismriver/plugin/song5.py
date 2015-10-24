import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class SongFivePlugin(Plugin):
    ID = 'song5'

    def __init__(self, config):
        super(SongFivePlugin, self).__init__('Song5', config)

    def search_song(self, artist, title):
        # no need to replace/delete symbols -- site will handle anything
        link = 'http://song5.ru/text/{}-{}'.format(
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        # returns 404 if song not found
        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            nav_pane = soup.find('ul', {'class': 'breadcrumb'})
            breadcrumbs = nav_pane.findAll('li', recursive=False)

            song_artist = breadcrumbs[1].a.text
            song_title = breadcrumbs[2].text

            lyrics_pane = soup.find('div', {'class': 'col-md-7'})

            lyrics = []
            if lyrics_pane.find('ul', {'class': 'nav nav-tabs'}, recursive=False):
                original = ''
                translation = ''

                for elem in lyrics_pane.findAll('span', {'class': True}, recursive=False):
                    if elem['class'][0] == 'orig_str':
                        original += (elem.text.strip() + '\n')
                    elif elem['class'][0] == 'translate_str':
                        translation += (elem.text.strip() + '\n')

                lyrics.append(original)
                lyrics.append(translation)
            else:
                lyric = self.parse_verse_block(lyrics_pane, tags_to_skip=['ul', 'script', 'ins', 'a', 'div'])
                lyric = re.sub('Исполнитель:$', '', lyric)
                lyrics.append(lyric)

            return Song(song_artist, song_title, self.sanitize_lyrics(lyrics))

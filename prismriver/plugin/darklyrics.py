import re

from bs4 import Comment, NavigableString, Tag

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class DarkLyricsPlugin(Plugin):
    ID = 'darklyrics'
    RANK = 7

    def __init__(self, config):
        super(DarkLyricsPlugin, self).__init__('Dark Lyrics', config)

    def search_song(self, artist, title):
        link = 'http://www.darklyrics.com/search?q={}%20{}'.format(
                self.prepare_url_parameter(artist),
                self.prepare_url_parameter(title))

        page = self.download_webpage(link)

        if page:
            soup = self.prepare_soup(page)

            main_pane = soup.find('div', {'class': 'cont'})
            full_title = '{} - {}'.format(artist, title)

            for item in main_pane.findAll('a', {'target': '_blank'}, href=re.compile('lyrics/.*/.*html#[0-9]+')):

                if self.compare_strings(item.text, full_title):
                    mobj = re.match('lyrics/.*/.*html#(?P<id>.*)', item['href'])
                    song_id = mobj.group('id')

                    song_link = 'http://www.darklyrics.com/' + item['href']
                    [song_artist, song_title] = item.text.split(' - ', 2)

                    page = self.download_webpage_text(song_link)
                    if page:
                        soup = self.prepare_soup(page)

                        lyrics_pane = soup.find('div', {'class': 'lyrics'})
                        lyric = self.find_verse_block(lyrics_pane, song_id)

                        return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

    def find_verse_block(self, verse_block, song_id):
        lyric = ''

        enabled = False
        for elem in verse_block.childGenerator():
            if isinstance(elem, Comment):
                pass
            elif isinstance(elem, NavigableString):
                if enabled:
                    lyric += elem.strip()
            elif isinstance(elem, Tag):
                if elem.name == 'h3':
                    tag_id = elem.find('a')['name']
                    if song_id == tag_id:
                        enabled = True
                    else:
                        enabled = False
                elif elem.name == 'i':
                    if enabled:
                        lyric += elem.text.strip()
                elif elem.name == 'div':
                    # end of page
                    enabled = False
                else:
                    if enabled:
                        lyric += '\n'

        return lyric.strip()

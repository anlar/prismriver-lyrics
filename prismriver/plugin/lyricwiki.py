import json
import re

from bs4 import Tag, NavigableString, Comment

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricWikiPlugin(Plugin):
    ID = 'lyricwiki'
    RANK = 7

    def __init__(self, config):
        super(LyricWikiPlugin, self).__init__('LyricWiki', config)

    def search_song(self, artist, title):
        # they don't understand quoted '&' as a delimiter between artists
        url = 'http://lyrics.wikia.com/api.php?action=lyrics&artist={}&song={}&fmt=realjson&func=getSong'.format(
            self.prepare_url_parameter(artist, safe_chars='&'), self.prepare_url_parameter(title))

        page = self.download_webpage_text(url)

        if page:
            resp = json.loads(page)
            if resp['lyrics'] == 'Not found':
                return None

            song_artist = resp['artist']
            song_title = resp['song']

            lyric_url = resp['url']
            lyric_page = self.download_webpage(lyric_url)

            soup = self.prepare_soup(lyric_page)

            lyrics = self.get_page_lyrics(soup)

            # load lyric translations from separate pages
            # eg: This song has been translated into these languages: Romanized, English.
            page_name = re.split('(?<!/)/(?!/)', lyric_url, 2)[1]
            for link in soup.findAll('a', {'title': True}, href=re.compile('/wiki/' + page_name + '/.*')):
                page = self.download_webpage_text('http://lyrics.wikia.com' + link['href'])
                lyrics.extend(self.get_page_lyrics(self.prepare_soup(page)))

            return Song(song_artist, song_title, self.sanitize_lyrics(lyrics))

    def get_page_lyrics(self, page_soup):
        lyrics = []
        for lyric_pane in page_soup.findAll("div", {"class": "lyricbox"}):
            lyric = self.parse_verse_block(lyric_pane)
            # skip empty invisible block with licensing warning
            if lyric.strip():
                lyrics.append(lyric)

        return lyrics

    def parse_verse_block(self, verse_block, tags_to_skip=None):
        lyric = ''

        for elem in verse_block.childGenerator():
            if isinstance(elem, Comment):
                pass
            elif isinstance(elem, NavigableString):
                if not elem.strip().startswith('(function()'):
                    lyric += elem.strip()
            elif isinstance(elem, Tag):
                if elem.name == 'b':
                    # bold elements, usually just 'Instrumental' tag
                    lyric += elem.text.strip()
                else:
                    lyric += '\n'

        return lyric

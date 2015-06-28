import json

from bs4 import BeautifulSoup, Tag, NavigableString, Comment

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricWikiPlugin(Plugin):
    def __init__(self):
        super().__init__('lyricwiki', 'LyricWiki')

    def search(self, artist, title):
        url = 'http://lyrics.wikia.com/api.php?action=lyrics&artist={}&song={}&fmt=realjson&func=getSong'.format(
            self.quote_uri(artist), self.quote_uri(title))

        webpage = self.download_webpage(url)
        resp = json.loads(webpage.decode("utf-8"))
        if resp['lyrics'] == 'Not found':
            return None

        song_artist = resp['artist']
        song_title = resp['song']

        second_url = resp['url']
        web_page = self.download_webpage(second_url)

        soup = BeautifulSoup(web_page)
        main_table = soup.find("div", {"class": "lyricbox"})

        lyric = self.parse_verse_block(main_table)

        return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

    def parse_verse_block(self, verse_block):
        lyric = ''

        for elem in verse_block.recursiveChildGenerator():
            if isinstance(elem, Comment):
                pass
            elif isinstance(elem, NavigableString):
                if not elem.strip().startswith('(function()'):
                    lyric += elem.strip()
            elif isinstance(elem, Tag):
                lyric += '\n'

        return lyric

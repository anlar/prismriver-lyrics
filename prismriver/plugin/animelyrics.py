import re

from bs4 import Tag, NavigableString

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class AnimeLyricsPlugin(Plugin):
    def __init__(self):
        super(AnimeLyricsPlugin, self).__init__('animelyrics', 'Anime Lyrics')

    def search(self, artist, title):
        link = 'http://www.animelyrics.com/search.php?q={}&t=title&searchcat=anime'.format(
            self.prepare_url_parameter(title)
        )

        page = self.download_webpage(link)
        if page:
            soup = self.prepare_soup(page)

            search_results = self.parse_search_page(soup)
            search_results = self.limit_search_results(search_results, artist, title)

            for result in search_results:
                song = self.get_song(result, artist, title)
                if song:
                    return song

    def parse_search_page(self, soup):
        search_head = soup.find('div', {'class': 'searchhead'})
        if not search_head:
            return []

        results = []
        current = []

        elem = search_head.nextSibling

        while elem is not None:
            if isinstance(elem, Tag):
                if elem.name == 'a':
                    current.append(elem.get_text())
                    if len(current) == 3:
                        song_link = 'http://www.animelyrics.com' + elem['href']
                        current.append(song_link)
                        results.append(current)

                        current = []

            elem = elem.nextSibling

        return results

    def limit_search_results(self, results, artist, title):
        hits = []
        for result in results:
            if self.compare_strings(result[2], title):
                hits.append(result)

        return hits

    def get_song(self, result, artist, title):
        # check song title
        song_title = result[2]
        if not self.compare_strings(song_title, title):
            return None

        # download song page
        song_link = result[3]
        page = self.download_webpage(song_link)
        soup = self.prepare_soup(page)

        # check song artist
        song_artist = self.get_artist(soup)
        if not self.compare_strings(song_artist, artist):
            return None

        lyrics = []

        lyric_table = soup.find('table')
        if lyric_table:
            lyric_parts = lyric_table.findAll('tr')

            if len(lyric_parts) == 2:
                # that means that whole lyric resides in first block
                lyric = self.parse_lyric_block(lyric_parts[0])
                lyrics.append(lyric)
            else:
                # otherwise parse and combine each block
                lyrics.extend(['', ''])
                for elem in lyric_parts[1:]:
                    blocks = elem.findAll('td', {'class': ['romaji', 'translation']})
                    if blocks:
                        lyric_romaji = self.parse_lyric_block(blocks[0])
                        lyrics[0] += (lyric_romaji + '\n')

                        lyric_trans = self.parse_lyric_block(blocks[1])
                        lyrics[1] += (lyric_trans + '\n')

                    lyrics[0] += '\n'
                    lyrics[1] += '\n'

        else:
            lyric = self.parse_lyric_block(soup)
            lyrics.append(lyric)

        kanji_ver_block = soup.find('a', {'href': song_link
                                    .replace('http://www.animelyrics.com/', '')
                                    .replace('.htm', '.jis')})

        if kanji_ver_block:
            page = self.download_webpage(song_link.replace('.htm', '.jis'))
            soup = self.prepare_soup(page)

            song_block = soup.find('div', {'id': 'kanji'})
            lyric = self.parse_kanji_block(song_block)
            lyrics.insert(0, lyric)

        return Song(artist, song_title, self.sanitize_lyrics(lyrics))

    def get_artist(self, page_soup):
        top_block = page_soup.find('td', {'valign': 'top'})

        values = []

        for elem in top_block.childGenerator():
            if isinstance(elem, NavigableString):
                text = elem.strip()
                if text:
                    values.append(text)

        for value in values:
            if value.startswith('Performed'):
                mobj = re.match('Performed by([:]*) (?P<id>.*)', value)
                return mobj.group('id')

        for value in values:
            if value.startswith('Performer'):
                mobj = re.match('Performer([:]*) (?P<id>.*)', value)
                return mobj.group('id')

        for value in values:
            if value.startswith('by'):
                mobj = re.match('by([:]*) (?P<id>.*)', value)
                return mobj.group('id')

        for value in values:
            if value.startswith('Sung by'):
                mobj = re.match('Sung by([:]*) (?P<id>.*)', value)
                return mobj.group('id')

        for value in values:
            if value.startswith('Singers'):
                mobj = re.match('Singers([:]*) (?P<id>.*)', value)
                return mobj.group('id')

    def parse_lyric_block(self, block):
        song_block = block.find('span', {'class': 'lyrics'})
        return self.parse_verse_block(song_block)

    def parse_kanji_block(self, block):
        lyric = ''

        for elem in block.childGenerator():
            if isinstance(elem, NavigableString):
                lyric += elem.strip()
            elif isinstance(elem, Tag):
                if elem.name == 'a':
                    lyric += elem.text
                else:
                    lyric += '\n'

        return lyric

    def compare_strings(self, s1, s2):
        return s1 and s2 and s1.lower() == s2.lower()

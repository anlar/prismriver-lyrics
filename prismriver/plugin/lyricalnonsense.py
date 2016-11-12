import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricalNonsensePlugin(Plugin):
    ID = 'lyricalnonsense'

    def __init__(self, config):
        super(LyricalNonsensePlugin, self).__init__('Lyrical Nonsense', config)

    def search_song(self, artist, title):
        artist_page = self.get_artist_page(artist)
        if artist_page:
            song_page = self.get_song_page(artist_page, title)
            if song_page:
                return self.get_song(song_page)

    def get_artist_page(self, artist):
        main_page = self.download_webpage('http://www.lyrical-nonsense.com/lyrics/')
        if main_page:
            soup = self.prepare_soup(main_page)

            artist_infos = []

            artists_pane = soup.find('div', {'class': 'lyricinfoblock'})

            for elem in artists_pane.findAll('a', href=re.compile('http://www.lyrical-nonsense.com/lyrics/.*/')):
                artist_infos.append([elem['href'], elem.text.split(' | )')])

            artist_link = None
            for info in artist_infos:
                if artist.lower() in map(lambda x: x.lower(), info[1]):
                    artist_link = info[0]

            if artist_link:
                return self.download_webpage(artist_link)

    def get_song_page(self, page, title):
        soup = self.prepare_soup(page)

        for elem in soup.findAll('table', {'class': 'imagetablelyrics'}):
            original_title_block = elem.find('div', {'class': 'titletextartist'})
            song_link = original_title_block.a['href']

            song_titles = [original_title_block.text]

            translated_title_block = elem.find('div', {'class': 'subtitletextartist'})
            if translated_title_block:
                for translated_title in translated_title_block.strings:
                    song_titles.extend(translated_title.strip().split('\r\n'))

            if title.lower() in map(lambda x: x.lower(), song_titles):
                return self.download_webpage(song_link)

    def get_song(self, page):
        soup = self.prepare_soup(page)

        artist_block = soup.find('table', {'class': 'imagetabletitle'})
        if artist_block:
            artist_block = artist_block.find('div', {'class': 'titletextpage'})
            song_artist = artist_block.get_text()
        else:
            artist_block = soup.find('div', {'class': 'artistlyricblocknew'})
            artist_block = artist_block.find('div', {'class': 'artisttext1new'})
            song_artist = artist_block.get_text().strip()

        title_block = soup.find('table', {'class': 'songtitle'})
        if title_block:
            title_block = title_block.find('div', {'class': 'titletextpage'})
            song_title = title_block.get_text()
        else:
            title_block = soup.find('div', {'class': 'titlelyricblocknew'})
            title_block = title_block.find('div', {'class': 'titletext1new'})
            song_title = title_block.get_text().strip()

        lyrics = []

        main_lyric_block = soup.find('div', {'id': 'langtabs'})
        # we should reverse list order to move original japanese lyric to the top
        for lyric_block in main_lyric_block.findAll('div', id=True)[::-1]:
            block_id = lyric_block['id']
            # skip 'Details' (song info) and all '*-tv' (tv-size versions) blocks
            if (not block_id.startswith('Details')) and (not block_id.endswith('-tv')):
                lyric = self.parse_verse_block(lyric_block)
                lyrics.append(lyric)

        return Song(song_artist, song_title, self.sanitize_lyrics(lyrics))

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LetrasPlugin(Plugin):
    def __init__(self):
        super(LetrasPlugin, self).__init__('letras', 'Letras')

    def search(self, artist, title):
        link = 'http://letras.mus.br/winamp.php?t={}{}{}'.format(
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(' - '),
            self.prepare_url_parameter(title)
        )

        page = self.download_webpage(link)
        if page:
            soup = self.prepare_soup(page)

            header = soup.find('div', {'id': 'cabecalho'})
            song_title = header.h1.a.text
            song_artist = header.h2.a.text

            lyric_block = soup.find('div', {'id': 'letra'})

            lyric = ''
            for elem in lyric_block.findAll('p', recursive=False):
                lyric += (self.parse_verse_block(elem) + '\n\n')

            return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))
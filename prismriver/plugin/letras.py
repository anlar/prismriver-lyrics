from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LetrasPlugin(Plugin):
    PLUGIN_ID = 'letras'

    def __init__(self, config):
        super(LetrasPlugin, self).__init__(self.PLUGIN_ID, 'Letras', config)

    def search_song(self, artist, title):
        link = 'http://letras.mus.br/winamp.php?t={}{}{}'.format(
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(' - '),
            self.prepare_url_parameter(title)
        )

        page = self.download_webpage(link)
        if page:
            soup = self.prepare_soup(page)

            header = soup.find('div', {'id': 'cabecalho'})

            # if header wasn't found - it's an empty page
            if header:
                song_title = header.h1.a.text
                song_artist = header.h2.a.text

                lyric_block = soup.find('div', {'id': 'letra'})

                lyric = ''
                for elem in lyric_block.findAll('p', recursive=False):
                    lyric += (self.parse_verse_block(elem) + '\n\n')

                return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LetrasPlugin(Plugin):
    ID = 'letras'

    def __init__(self, config):
        super(LetrasPlugin, self).__init__('Letras', config)

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

                if not self.compare_strings(artist, song_artist):
                    # sometimes it may search song only by it's title and return things from another artist
                    return

                lyric_block = soup.find('div', {'id': 'letra'})

                lyric = ''
                for elem in lyric_block.findAll('p', recursive=False):
                    lyric += (self.parse_verse_block(elem) + '\n\n')

                if lyric.startswith('\n\nShortcut to '):
                    # lyric is empty, just list of other songs
                    return None
                else:
                    return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

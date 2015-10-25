from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class NautiljonPlugin(Plugin):
    ID = 'nautiljon'

    def __init__(self, config):
        super(NautiljonPlugin, self).__init__('Nautiljon', config)

    def search_song(self, artist, title):
        # no need to delete/replace chars - site will handle redirects
        link = 'http://www.nautiljon.com/paroles/{}/{}.html'.format(
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            title = soup.find('head').title
            title_parts = title.text.split(' : ', 3)

            song_artist = title_parts[1]
            song_title = title_parts[2]

            lyrics_panes = soup.findAll('td', {'class': 'a50 vtop'})

            lyrics = []

            if len(lyrics_panes) > 0:
                # 2 lyrics: original and translated
                for pane in lyrics_panes:
                    lyrics.append(self.parse_verse_block(pane))
            else:
                # only original lyrics
                lyrics_pane = soup.find('div', {'id': 'onglets_2_histoire'})
                lyric = self.parse_verse_block(lyrics_pane, tags_to_skip=['div', 'p'])

                if lyric.endswith('Aucune parole disponible.'):
                    # there are no lyrics for that song - instrumental
                    return None
                else:
                    lyrics.append(lyric)

            return Song(song_artist, song_title, self.sanitize_lyrics(lyrics))

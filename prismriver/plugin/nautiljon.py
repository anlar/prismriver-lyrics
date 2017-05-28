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

            orig_pane = soup.find('span', {'itemprop': 'text'})
            tran_panes = soup.findAll('td', {'class': 'a50 vtop'})

            lyrics = [self.parse_verse_block(orig_pane)]

            if len(tran_panes) > 1:
                # skip first block as it's wrapping original lyrics pane
                for pane in tran_panes[1:]:
                    lyrics.append(self.parse_verse_block(pane))

            return Song(song_artist, song_title, self.sanitize_lyrics(lyrics))

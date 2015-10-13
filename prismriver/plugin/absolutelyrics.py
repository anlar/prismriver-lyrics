from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class AbsoluteLyricsPlugin(Plugin):
    ID = 'absolutelyrics'

    def __init__(self, config):
        super(AbsoluteLyricsPlugin, self).__init__('AbsoluteLyrics', config)

    def search_song(self, artist, title):
        to_delete = ['?']
        link = 'http://www.absolutelyrics.com/lyrics/view/{}/{}'.format(
            self.prepare_url_parameter(artist, to_delete=to_delete, delimiter='_'),
            self.prepare_url_parameter(title, to_delete=to_delete, delimiter='_'))

        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            nav_pane = soup.find('div', {'id': 'nav'})
            nav_a_panes = nav_pane.findAll('a', recursive=False)

            if len(nav_pane) == 1:
                # song not found, we're redirected to search page
                # todo: process search suggestions
                return None

            song_artist = nav_a_panes[1].text.replace(' Lyrics', '')
            song_title = nav_a_panes[1].next_sibling.strip().replace(' Lyrics', '')

            lyrics_pane = soup.find('p', {'id': 'view_lyrics'})
            lyrics = self.parse_verse_block(lyrics_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

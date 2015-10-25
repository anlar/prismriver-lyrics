from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsDepotPlugin(Plugin):
    ID = 'lyricsdepot'

    def __init__(self, config):
        super(LyricsDepotPlugin, self).__init__('Lyrics Depot', config)

    def search_song(self, artist, title):
        to_delete = ['.', ',', "'", '"', '!', '?' '(', ')']
        to_replace = [' / ', '/', ' ']
        link = 'http://www.lyricsdepot.com/{}/{}.html'.format(
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace),
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace))

        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            nav_pane = soup.find('ul', {'class': 'pull-left'})
            nav_pane_parts = nav_pane.findAll('li', recursive=False)

            song_artist = nav_pane_parts[1].a.text[:-7]
            song_title = nav_pane_parts[2].text[:-7]

            lyrics_pane = soup.find('p', {'class': 'lyrics'})
            lyrics = self.parse_verse_block(lyrics_pane)

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

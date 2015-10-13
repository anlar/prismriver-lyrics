from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class AlLyricsPlugin(Plugin):
    ID = 'allyrics'

    def __init__(self, config):
        super(AlLyricsPlugin, self).__init__('AlLyrics.net', config)

    def search_song(self, artist, title):
        to_delete = ['!', '?', '.', ',', '(', ')']
        to_replace = [' ', "'", ' & ']
        link = 'http://www.allyrics.net/{}/lyrics/{}/'.format(
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace),
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace))

        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            nav_bar = soup.find('div', {'class', 'top_cont'}).h2
            artist_tag = nav_bar.find('b')

            song_artist = artist_tag.text[:-2]
            song_title = artist_tag.next_sibling.strip()[:-7]

            if not song_title:
                # song not found
                return None

            lyrics_pane = soup.find('div', {'class': 'c_tl'})
            lyrics = self.parse_verse_block(lyrics_pane, tags_to_skip=['script'])

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

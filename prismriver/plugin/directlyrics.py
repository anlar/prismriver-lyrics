from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class DirectLyricsPlugin(Plugin):
    ID = 'directlyrics'

    def __init__(self, config):
        super(DirectLyricsPlugin, self).__init__('Directlyrics', config)

    def search_song(self, artist, title):
        to_delete = ['.', ',', "'", '?', '/', '(', ')', '!']
        to_replace = [' ']
        link = 'http://www.directlyrics.com/{}-{}-lyrics.html'.format(
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace),
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace))

        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            main_pane = soup.find('div', {'class': 'column content'})
            if not main_pane:
                return None

            title_parts = main_pane.find('h2').findAll('span', {'itemprop': 'name'})
            song_artist = title_parts[0].text
            song_title = title_parts[1].text

            lyrics_pane = main_pane.find('div', {'class': 'lyrics lyricsselect'}, recursive=False).p
            lyrics = self.parse_verse_block(lyrics_pane, tags_to_skip=['ins', 'script'])

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

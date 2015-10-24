from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class ShowMeLyricsPlugin(Plugin):
    ID = 'showmelyrics'
    RANK = 6

    def __init__(self, config):
        super(ShowMeLyricsPlugin, self).__init__('ShowMeLyrics', config)

    def search_song(self, artist, title):
        to_delete = ["'", '’', '.', ',', '!', '?', '[', ']', '(', ')', '*']
        to_replace = [' ', ' & ']
        link = 'http://showmelyrics.com/lyrics/{}-{}'.format(
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace),
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace))

        page = self.download_webpage_text(link)
        # return 404 if song not found
        if page:
            soup = self.prepare_soup(page)

            title_pane = soup.find('div', {'class': 'box-title-current'})
            full_title = title_pane.span.text.strip()
            title_parts = full_title.split(' – ', 2)

            song_artist = title_parts[0]
            song_title = title_parts[1]

            lyrics_pane = soup.find('div', {'id': 'lyrics'})
            inner_lyrics_pane = lyrics_pane.find('div', {'class': 'editable editable-content'}, recursive=False)

            lyrics = ''
            for elem in inner_lyrics_pane.findAll('p', recursive=False):
                lyrics += (self.parse_verse_block(elem) + '\n\n')

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

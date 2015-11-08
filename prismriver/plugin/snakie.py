from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class SnakiePlugin(Plugin):
    ID = 'snakie'

    def __init__(self, config):
        super(SnakiePlugin, self).__init__('Snakie\'s Obsession', config)

    def search_song(self, artist, title):
        to_delete = ['.', ',', '!', '?', '(', ')', '~', '/', "'", '"']
        to_replace = [' ']
        link = 'http://lyrics.snakeroot.ru/{}/{}/{}_{}.html'.format(
            self.prepare_url_parameter(artist[0].upper()),
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace, delimiter='_'),
            self.prepare_url_parameter(artist, to_delete=to_delete, to_replace=to_replace, delimiter='_').lower(),
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace, delimiter='_').lower())

        # return 404 if song not found
        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            main_pane = soup.find('div', {'id': 'content'})

            title_pane = main_pane.find('h2', recursive=False)
            song_artist = title_pane.a.text
            song_title = title_pane.a.next_sibling[3:]

            # searching for first non-empty paragraph
            for lyrics_pane in reversed(main_pane.findAll('p')):
                if lyrics_pane.text.strip() != '':
                    lyrics = self.parse_verse_block(lyrics_pane)
                    return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

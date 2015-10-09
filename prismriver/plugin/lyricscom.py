from bs4 import Tag, Comment
from bs4 import NavigableString

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class LyricsComPlugin(Plugin):
    ID = 'lyricscom'

    def __init__(self, config):
        super(LyricsComPlugin, self).__init__('Lyrics.com', config)

    def search_song(self, artist, title):
        to_replace = [' ', ' & ']
        to_delete = ['?', '(', ')', '[', ']', '.', ',', "'", '/', ':']
        link = 'http://www.lyrics.com/{}-lyrics-{}.html'.format(
            self.prepare_url_parameter(title, to_replace=to_replace, to_delete=to_delete),
            self.prepare_url_parameter(artist, to_replace=to_replace, to_delete=to_delete))

        page = self.download_webpage(link)

        if page:
            soup = self.prepare_soup(page)

            lyrics_pane = soup.find('div', {'id': 'lyrics'})
            if not lyrics_pane:
                # song not found or lyrics is empty
                return
            lyrics = self.parse_verse_block(lyrics_pane)

            profile_pane = soup.find('h1', {'id': 'profile_name'})
            song_title = profile_pane.contents[0].strip()

            artist_pane = profile_pane.find('a', {'href': True})
            song_artist = artist_pane.text

            return Song(song_artist, song_title, self.sanitize_lyrics([lyrics]))

    def parse_verse_block(self, verse_block):
        lyric = ''

        for elem in verse_block.childGenerator():
            if isinstance(elem, Comment):
                pass
            elif isinstance(elem, NavigableString):
                line = elem.strip()
                # after that line goes lyrics submitter name
                if line == '---':
                    break
                else:
                    lyric += elem.strip()
            elif isinstance(elem, Tag):
                lyric += '\n'

        return lyric.strip()

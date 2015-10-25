import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class JLyricsRuPlugin(Plugin):
    ID = 'jlyricsru'
    RANK = 7

    def __init__(self, config):
        super(JLyricsRuPlugin, self).__init__('J-Lyrics.ru', config)

    def search_song(self, artist, title):
        to_delete = ['.', ',', '!', '?', '~']
        to_replace = [' & ', ' × ', "'", '"' ':', ' ']
        link = 'http://j-lyrics.ru/songs/{}/'.format(
            self.prepare_url_parameter(title, to_delete=to_delete, to_replace=to_replace))

        page = self.download_webpage_text(link)
        if page:
            soup = self.prepare_soup(page)

            title_pane = soup.find('section', {'class': 'textTranslateMain'})
            if not title_pane:
                # song not found
                return None

            song_artists = [pane.text for pane in
                            title_pane.findAll('a', {'title': True}, href=re.compile(r'/artists/.*'))]
            if not self.is_correct_artist(artist, song_artists):
                return None

            song_artist = ', '.join(song_artists)
            song_title = title_pane.h1.text

            lyrics = []

            lyrics_panes = soup.findAll('div', {'class': ['box__translate', 'rusVariant__translate']})
            for pane in lyrics_panes:
                lyrics.append(self.parse_verse_block(pane))

            # reorder lyrics: from "jp, ru, en" to "jp, en, ru"
            if len(lyrics) >= 3:
                lyrics.insert(1, lyrics.pop())

            return Song(song_artist, song_title, self.sanitize_lyrics(lyrics))

    def is_correct_artist(self, artist, song_artists):
        for song_artist in song_artists:
            if self.compare_strings(artist, song_artist):
                return True

        return False

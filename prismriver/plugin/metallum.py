from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class MetallumPlugin(Plugin):
    ID = 'metallum'
    RANK = 8

    def __init__(self, config):
        super(MetallumPlugin, self).__init__('Encyclopaedia Metallum', config)

    def search_song(self, artist, title):
        link = 'http://www.metal-archives.com/search/ajax-advanced/searching/songs/?songTitle={}&exactSongMatch=1&bandName={}&exactBandMatch=1'.format(
                self.prepare_url_parameter(title),
                self.prepare_url_parameter(artist))

        page = self.download_webpage_json(link)

        if page and len(page['aaData']) > 0:
            item = page['aaData'][0]
            song_info = self.get_song_info(item)

            lyric_link = 'http://www.metal-archives.com/release/ajax-view-lyrics/id/{}'.format(song_info[2])
            lyric_page = self.download_webpage_text(lyric_link)

            if lyric_page:
                soup = self.prepare_soup(lyric_page)
                lyric = self.parse_verse_block(soup.find('p'))
                return Song(song_info[0], song_info[1], self.sanitize_lyrics([lyric]))

    def get_song_info(self, item):
        song_artist = self.prepare_soup(item[0]).a.text
        song_title = item[3]
        lyric_id = self.prepare_soup(item[4]).a['id'].split('_', 2)[1]

        return [song_artist, song_title, lyric_id]

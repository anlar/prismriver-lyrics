from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class Sing365Plugin(Plugin):
    ID = 'sing365'
    RANK = 6

    def __init__(self, config):
        super(Sing365Plugin, self).__init__('Sing365', config)

    def search_song(self, artist, title):
        link = 'https://www.googleapis.com/customsearch/v1element?key={}&rsz=filtered_cse&num=1&hl=en&prettyPrint=true&source=gcsc&gss=.com&sig={}&cx={}&q={}%20{}'.format(
                'AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY',
                '432dd570d1a386253361f581254f9ca1',
                'partner-pub-0919305250342516:9855113007',
                self.prepare_url_parameter(artist),
                self.prepare_url_parameter(title))

        page = self.download_webpage_json(link)
        if page:
            results = page['results']

            if not results or len(results) < 0:
                return None
            elif not self.compare_strings(results[0]['titleNoFormatting'], '{} LYRICS - {}'.format(title, artist)):
                return None

            [song_title, song_artist] = results[0]['titleNoFormatting'].split(' LYRICS - ', 2)

            lyric_link = results[0]['unescapedUrl']
            lyric_id = lyric_link.split('/')[-1]
            print_link = 'http://www.sing365.com/music/lyric.nsf/PrintLyrics?openForm&ParentUnid={}'.format(lyric_id)

            lyric_page = self.download_webpage_text(print_link)
            if lyric_page:
                soup = self.prepare_soup(lyric_page)

                lyric_pane = soup.find('tr', {'valign': 'top'}).findAll('td', recursive=False)[1]
                lyric = self.parse_verse_block(lyric_pane, tags_to_skip=['font', 'input', 'i'])

                return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

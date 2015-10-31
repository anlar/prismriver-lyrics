import html
import re

from prismriver.plugin.common import Plugin
from prismriver.struct import Song


class KasiTimePlugin(Plugin):
    ID = 'kasitime'
    RANK = 8

    def __init__(self, config):
        super(KasiTimePlugin, self).__init__('Kasi-Time', config)

    def search_song(self, artist, title):
        link = 'https://www.googleapis.com/customsearch/v1element?key={}&rsz=filtered_cse&num=1&hl=ja&prettyPrint=true&source=gcsc&gss=.com&sig={}&cx={}&q={}%20{}'.format(
            'AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY',
            '432dd570d1a386253361f581254f9ca1',
            'partner-pub-4761826397918753:6745924343',
            self.prepare_url_parameter(artist),
            self.prepare_url_parameter(title))

        page = self.download_webpage_json(link)
        if page:
            results = page['results']

            if not results or len(results) < 0:
                return None
            elif not self.compare_strings(results[0]['titleNoFormatting'], '{} {} - 歌詞タイム'.format(title, artist)):
                return None

            lyric_link = results[0]['unescapedUrl']

            lyric_page = self.download_webpage_text(lyric_link)
            if lyric_page:
                soup = self.prepare_soup(lyric_page)

                title_pane = soup.find('div', {'class': 'person_list_and_other_contents'})
                song_title = title_pane.h1.text.strip()

                person_pane = title_pane.find('div', {'class': 'person_list'})
                song_artist = person_pane.find('a').text.strip()

                lyric = self.get_lyrics(lyric_page)

                return Song(song_artist, song_title, self.sanitize_lyrics([lyric]))

    def get_lyrics(self, lyric_page):
        raw_lyric = re.findall('var lyrics = \'(.*?)\';', lyric_page, re.DOTALL)
        html_lyric = html.unescape(raw_lyric[0])
        return html_lyric.replace('<br>', '\n')

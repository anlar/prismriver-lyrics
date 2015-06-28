import logging
import re
import urllib.parse
import urllib.request
import urllib.error
import sys
import time
import xml.etree.ElementTree

from prismriver import util


class Plugin:
    def __init__(self, plugin_id, plugin_name):
        self.plugin_id = plugin_id
        self.plugin_name = plugin_name

    def search(self, artist, title):
        pass

    def is_valid_request(self, artist, title):
        return artist and title

    def quote_uri(self, value):
        return urllib.parse.quote(value)

    def download_webpage(self, url):
        start = time.time()

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20150101 Firefox/20.0 (Chrome)'})
        try:
            with urllib.request.urlopen(req) as response:
                the_page = response.read()
                page_size = sys.getsizeof(the_page)
                logging.debug('Download web-page from "{}", {}, {}'.format(url, util.format_file_size(page_size),
                                                                           util.format_time_ms(time.time() - start)))

                return the_page
        except urllib.error.HTTPError as err:
            logging.debug('Failed to download web-page from "{}", error: {}, {}'.format(url, err.code, err.reason))
            return None
        except ConnectionResetError as err:
            logging.debug('Failed to download web-page from "{}", error: {}, {}'.format(url, err.errno, err.strerror))
            return None

    def download_xml(self, url):
        page = self.download_webpage(url)
        if page:
            xml_string = page.decode("utf-8")
            xml_string = re.sub(' xmlns="[^"]+"', '', xml_string, count=1)
            root = xml.etree.ElementTree.fromstring(xml_string)
            return root

    def sanitize_lyrics(self, lyrics):
        if lyrics:
            sanitized = []
            for lyric in lyrics:
                if lyric:
                    sanitized.append(lyric.strip())

            return sanitized
        else:
            return None

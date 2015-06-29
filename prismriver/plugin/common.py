import logging
import re
import urllib.parse
import urllib.request
import urllib.error
import sys
import time
import xml.etree.ElementTree

from bs4 import NavigableString, Tag

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

    def prepare_url_parameter(self, value, to_delete=None, to_replace=None, delimiter='-', quote_uri=True):
        if not to_delete:
            to_delete = []
        if not to_replace:
            to_replace = []

        new_value = value

        for elem in to_delete:
            new_value = new_value.replace(elem, '')

        for elem in to_replace:
            new_value = new_value.replace(elem, delimiter)

        if quote_uri:
            return self.quote_uri(new_value)
        else:
            return new_value

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

    def download_webpage_text(self, url):
        page = self.download_webpage(url)
        if page:
            return page.decode("utf-8")

    def download_xml(self, url):
        page = self.download_webpage_text(url)
        if page:
            xml_string = re.sub(' xmlns="[^"]+"', '', page, count=1)
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

    def remove_tags_from_block(self, pane, tags):
        for tag in tags:
            [x.extract() for x in pane.findAll(tag)]

    def parse_verse_block(self, verse_block):
        lyric = ''

        for elem in verse_block.recursiveChildGenerator():
            if isinstance(elem, NavigableString):
                lyric += elem.strip()
            elif isinstance(elem, Tag):
                lyric += '\n'

        return lyric.strip()

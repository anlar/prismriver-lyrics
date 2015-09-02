import hashlib
import json
import logging
import re
import urllib.parse
import urllib.request
import urllib.error
import sys
import time
import xml.etree.ElementTree
import socket
import os
from os import path

from bs4 import NavigableString, Tag, Comment, BeautifulSoup

from prismriver import util


class Plugin:
    def __init__(self, plugin_name, config):
        self.plugin_name = plugin_name
        self.config = config

    def search_song(self, artist, title):
        pass

    #
    # URI quote helpers
    #

    def quote_uri(self, value, safe_chars=None):
        if safe_chars:
            return urllib.parse.quote(value, safe=(safe_chars + '/'))
        else:
            return urllib.parse.quote(value)

    def prepare_url_parameter(self, value, to_delete=None, to_replace=None, delimiter='-',
                              quote_uri=True, safe_chars=None):
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
            return self.quote_uri(new_value, safe_chars)
        else:
            return new_value

    #
    # Page download helpers
    #

    def download_webpage(self, url):
        start = time.time()

        cache_file_name = self.get_cache_file_name(url)
        cached_page = self.get_page_from_cache(cache_file_name)
        if cached_page:
            logging.debug(
                'Get web-page from cache "{}": "{}", {}, {}'.format(url, cache_file_name,
                                                                    util.format_file_size(self.get_psize(cached_page)),
                                                                    util.format_time_ms(time.time() - start)))
            return cached_page

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20150101 Firefox/20.0 (Chrome)'})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                page = response.read()

                self.put_page_to_cache(cache_file_name, page, url)

                logging.debug(
                    'Download web-page from "{}", {}, {}'.format(url,
                                                                 util.format_file_size(self.get_psize(page)),
                                                                 util.format_time_ms(time.time() - start)))

                return page
        except urllib.error.HTTPError as err:
            logging.debug('Failed to download web-page from "{}", error: {}, {}'.format(url, err.code, err.reason))
            return None
        except ConnectionResetError as err:
            logging.debug('Failed to download web-page from "{}", error: {}, {}'.format(url, err.errno, err.strerror))
            return None
        except socket.timeout:
            logging.debug('Failed to download web-page from "{}", timed out'.format(url))

    def download_webpage_text(self, url):
        page = self.download_webpage(url)
        if page:
            return page.decode("utf-8")

    def download_webpage_json(self, url):
        page = self.download_webpage_text(url)
        if page:
            return json.loads(page)

    def download_xml(self, url):
        page = self.download_webpage_text(url)
        if page:
            xml_string = re.sub(' xmlns="[^"]+"', '', page, count=1)
            root = xml.etree.ElementTree.fromstring(xml_string)
            return root

    def get_page_from_cache(self, cache_file_name):
        try:
            with open(cache_file_name, 'rb') as cache_file:
                now = time.time()
                mtime = path.getmtime(cache_file_name)

                if now - mtime < self.config.cache_web_ttl_sec:
                    return cache_file.read()
        except IOError:
            pass

    def put_page_to_cache(self, cache_file_name, page, link):
        if not path.exists(path.dirname(cache_file_name)):
            os.makedirs(path.dirname(cache_file_name))

        with open(cache_file_name, 'wb') as cache_file:
            cache_file.write(page)
            logging.debug(
                'Put web-page to cache "{}": "", {}, {}'.format(link, cache_file_name,
                                                                util.format_file_size(self.get_psize(page))))

    def get_cache_file_name(self, link):
        return self.config.cache_web_dir + hashlib.md5(link.encode('utf-8')).hexdigest() + '.cache'

    def get_psize(self, page):
        return sys.getsizeof(page)

    #
    # Page parsing helpers
    #

    def sanitize_lyrics(self, lyrics):
        if lyrics:
            sanitized = []
            for lyric in lyrics:
                if lyric:
                    sanitized.append(lyric.strip())

            return sanitized
        else:
            return None

    def prepare_soup(self, page):
        return BeautifulSoup(page, 'lxml')

    def remove_tags_from_block(self, pane, tags):
        for tag in tags:
            [x.extract() for x in pane.findAll(tag)]

    def parse_verse_block(self, verse_block):
        lyric = ''

        for elem in verse_block.childGenerator():
            if isinstance(elem, Comment):
                pass
            elif isinstance(elem, NavigableString):
                lyric += elem.strip()
            elif isinstance(elem, Tag):
                lyric += '\n'

        return lyric.strip()

    #
    # Other
    #

    def compare_strings(self, s1, s2):
        return s1 and s2 and s1.lower() == s2.lower()

import argparse
import logging

from prismriver.struct import SearchConfig


def init_logging(quiet, verbose, log_file):
    log_format = '%(asctime)s %(levelname)s [%(module)s] %(message)s'

    if quiet:
        log_level = logging.WARNING
    elif verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    if log_file:
        log_handlers = [logging.FileHandler(log_file), logging.StreamHandler()]
    else:
        log_handlers = [logging.StreamHandler()]

    logging.basicConfig(format=log_format, level=log_level, handlers=log_handlers)


def init_args_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument("-a", "--artist", help="song artist")
    parser.add_argument("-t", "--title", help="song title")

    parser.add_argument("-l", "--limit", type=int, help="maximum results count")
    parser.add_argument('-p', '--plugins', help='comma separated listed of enabled plugins '
                                                '(empty list means that everything is enabled - by default)')

    parser.add_argument("--web_timeout", type=int, help="timeout for web-page downloading in seconds (default: 10 sec)")

    parser.add_argument('--sync', action='store_true',
                        help='search info from all plugins consecutively')

    parser.add_argument('--parser', type=str, choices=['lxml', 'html5lib', 'html.parser'],
                        help='html parser (default: lxml)')

    parser.add_argument('--cache_dir', type=str,
                        help='cache directory for downloaded web pages (default: ~/.cache/prismriver)')
    parser.add_argument('--cache_ttl', type=str,
                        help='cache ttl for downloaded web pages in seconds (default: one week)')

    parser.add_argument("-q", "--quiet", help="disable logging info (show only errors)", action="store_true")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument('--log', type=str, help='if set will redirect log info to that file')

    return parser


def init_search_config(params):
    config = SearchConfig(
        params.plugins.split(',') if params.plugins else None,
        params.limit,
        params.cache_dir,
        params.cache_ttl,
        params.web_timeout,
        params.sync,
        params.parser)

    return config


def format_file_size(size_bytes):
    multiple = 1024
    for suffix in ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']:
        size = size_bytes / multiple
        if size < multiple:
            return '{0:.1f} {1}'.format(size, suffix)


def format_time_ms(time_sec):
    return "{:.1f} ms".format(time_sec * 1000)

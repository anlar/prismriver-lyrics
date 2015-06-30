import argparse
from json import JSONEncoder
import json
import logging

from prismriver.main import search


class SongJsonEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def format_output(songs, output_format):
    if output_format == 'txt':
        lyrics = []
        for song in songs:
            if song.lyrics:
                for lyric in song.lyrics:
                    lyrics.append(lyric)

        result = ''
        index = 0
        for lyric in lyrics:
            result += lyric
            if index < len(lyrics) - 1:
                result += '\n\n<<< --- --- --- --- --- >>>\n\n'
            index += 1

        return result

    elif output_format == 'json':
        return json.dumps(songs, cls=SongJsonEncoder, sort_keys=True, indent=4, ensure_ascii=False)

    elif output_format == 'json_ascii':
        return json.dumps(songs, cls=SongJsonEncoder, sort_keys=True, indent=4)

    else:
        pass


def init_logging(quiet, verbose):
    log_format = '%(asctime)s %(levelname)s [%(module)s] %(message)s'
    if quiet:
        logging.basicConfig(format=log_format, level=logging.WARNING)
    elif verbose:
        logging.basicConfig(format=log_format, level=logging.DEBUG)
    else:
        logging.basicConfig(format=log_format, level=logging.INFO)


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artist", help="song artist")
    parser.add_argument("-t", "--title", help="song title")

    parser.add_argument("-l", "--limit", type=int, help="lyrics limit")
    parser.add_argument('-p', '--plugins', help='comma separated listed of enabled plugins '
                                                '(empty list means that everything is enabled - by default)')

    parser.add_argument("-f", "--format", type=str, default='txt',
                        help="lyrics output format (txt (default), json, json_ascii)")
    parser.add_argument("-q", "--quiet", help="disable logging info (show only errors)", action="store_true")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")

    params = parser.parse_args()

    init_logging(params.quiet, params.verbose)

    logging.debug('Search lyrics with following parameters: {}'.format(params.__dict__))

    enabled_plugins = params.plugins.split(',') if params.plugins else None
    result = search(params.artist, params.title, params.limit, enabled_plugins)

    if result:
        print(format_output(result, params.format))

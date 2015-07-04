import argparse
from json import JSONEncoder
import json
import logging

from prismriver.main import search


class SongJsonEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def format_output(songs, output_format, txt_template=None):
    if output_format == 'txt':
        formatted_songs = []

        for song in songs:
            lyrics_txt = ''
            if song.lyrics:
                index = 0
                for lyric in song.lyrics:
                    lyrics_txt += lyric
                    if index < len(song.lyrics) - 1:
                        lyrics_txt += '\n\n<<< --- --- --- >>>\n\n'
                    index += 1

            result = txt_template
            result = result.replace('%TITLE%', song.title)
            result = result.replace('%ARTIST%', song.artist)
            result = result.replace('%PLUGIN_ID%', song.plugin_name)
            result = result.replace('%PLUGIN_NAME%', song.plugin_name)
            result = result.replace('%LYRICS%', lyrics_txt)

            formatted_songs.append(result)

        result = ''
        index = 0
        for formatted_song in formatted_songs:
            result += formatted_song
            if index < len(formatted_songs) - 1:
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

    parser.add_argument("-l", "--limit", type=int, help="maximum results count")
    parser.add_argument('-p', '--plugins', help='comma separated listed of enabled plugins '
                                                '(empty list means that everything is enabled - by default)')

    parser.add_argument("-f", "--format", type=str, default='txt',
                        help="lyrics output format (txt (default), json, json_ascii)")

    parser.add_argument("-o", "--output", type=str, default='%ARTIST% - %TITLE%\nSource: %PLUGIN_NAME%\n\n%LYRICS%',
                        help="output template for txt format. Available parameters: "
                             "%%TITLE%% - song title, "
                             "%%ARTIST%% - song artist, "
                             "%%LYRICS%% - song lyrics, "
                             "%%PLUGIN_ID%% - plugin id, "
                             "%%PLUGIN_NAME%% - plugin name "
                             "(default value: %%ARTIST%% - %%TITLE%%\\nSource: %%PLUGIN_NAME%%\\n\\n%%LYRICS%%)"
                        )

    parser.add_argument("-q", "--quiet", help="disable logging info (show only errors)", action="store_true")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")

    params = parser.parse_args()

    init_logging(params.quiet, params.verbose)

    logging.debug('Search lyrics with following parameters: {}'.format(params.__dict__))

    enabled_plugins = params.plugins.split(',') if params.plugins else None
    result = search(params.artist, params.title, params.limit, enabled_plugins)

    if result:
        print(format_output(result, params.format, params.output))

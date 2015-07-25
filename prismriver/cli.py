import argparse
import json
import logging

from prismriver.main import search_sync, search_async, get_plugins
from prismriver.struct import SearchConfig


class SongJsonEncoder(json.JSONEncoder):
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


def list_plugins():
    plugins = get_plugins()
    plugins.sort(key=lambda x: x.plugin_name.lower())
    for plugin in plugins:
        print('{:<20} [id: {}]'.format(plugin.plugin_name, plugin.plugin_id))


def run():
    parser = argparse.ArgumentParser()

    parser.add_argument('--list', action='store_true', help='list available search plugins')
    parser.add_argument('--song', action='store_true',
                        help='search for song information by artist and title (default action)')

    parser.add_argument("-a", "--artist", help="song artist")
    parser.add_argument("-t", "--title", help="song title")

    parser.add_argument("-l", "--limit", type=int, help="maximum results count")
    parser.add_argument('-p', '--plugins', help='comma separated listed of enabled plugins '
                                                '(empty list means that everything is enabled - by default)')

    parser.add_argument("-f", "--format", type=str, default='txt',
                        help="lyrics output format (txt (default), json, json_ascii)")

    parser.add_argument('--async', action='store_true',
                        help='search info from all plugins simultaneously')

    parser.add_argument('--cache_dir', type=str,
                        help='cache directory for downloaded web pages (default: ~/.cache/prismriver)')
    parser.add_argument('--cache_ttl', type=str,
                        help='cache ttl for downloaded web pages in seconds (default: one week)')

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
    parser.add_argument('--log', type=str, help='if set will redirect log info to that file')

    params = parser.parse_args()

    init_logging(params.quiet, params.verbose, params.log)

    if params.list:
        list_plugins()
    else:
        logging.debug('Search lyrics with following parameters: {}'.format(params.__dict__))

        search_config = SearchConfig(
            params.plugins.split(',') if params.plugins else None,
            params.limit,
            params.cache_dir,
            params.cache_ttl)

        if params.async:
            result = search_async(params.artist, params.title, search_config)
        else:
            result = search_sync(params.artist, params.title, search_config)

        if result:
            print(format_output(result, params.format, params.output))

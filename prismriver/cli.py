import json

from prismriver import util
from prismriver.main import get_plugins, search


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


def list_plugins():
    plugins = get_plugins()
    plugins.sort(key=lambda x: x.plugin_name.lower())
    for plugin in plugins:
        print('{:<20} [id: {}]'.format(plugin.plugin_name, plugin.ID))


def run():
    parser = util.init_args_parser()

    parser.add_argument('--list', action='store_true', help='list available search plugins')
    parser.add_argument('--song', action='store_true',
                        help='search for song information by artist and title (default action)')

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

    params = parser.parse_args()

    util.init_logging(params.quiet, params.verbose, params.log)
    util.log_debug_info(params)

    config = util.init_search_config(params)
    util.log_config_info(config)

    if params.list:
        list_plugins()
    else:
        result = search(params.artist, params.title, config)

        if result:
            print(format_output(result, params.format, params.output))

from prismriver import util
from prismriver.qt.controller import MainController


def run():
    parser = create_args_parser()
    # skip unknown args, some of them may be handled as common qt options
    # see: http://doc.qt.io/qt-5/qguiapplication.html
    params, unknown = parser.parse_known_args()

    util.init_logging(params.quiet, params.verbose, params.log)
    util.log_debug_info()

    search_config = util.init_search_config(params)

    MainController(search_config, params.artist, params.title, params.mpris, params.connect, params.tray)


def create_args_parser():
    parser = util.init_args_parser()

    parser.add_argument('-m', '--mpris', help='default MPRIS-player name')
    parser.add_argument('--connect', action='store_true', help='connect to player and listen for song details')

    parser.add_argument('--tray', default='show', choices=('show', 'minimize', 'hide'), help='tray help')

    return parser

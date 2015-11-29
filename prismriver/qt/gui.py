from prismriver import util

parser = util.init_args_parser()
parser.add_argument('-m', '--mpris', help='default MPRIS-player name')
parser.add_argument('--connect', action='store_true', help='connect to player and listen for song details')
parser.add_argument('--tray', default='show', choices=('show', 'minimize', 'hide'), help='tray help')
parser.add_argument('--qt4', action='store_true', help='force using PyQt4 frontend')

# skip unknown args, some of them may be handled as common qt options
# see: http://doc.qt.io/qt-5/qguiapplication.html
params, unknown = parser.parse_known_args()

util.init_logging(params.quiet, params.verbose, params.log)
util.log_debug_info(params)

config = util.init_search_config(params)
util.log_config_info(config)

force_qt4 = params.qt4

# that import should be placed here to ensure that 'force_qt4' variable will be initialized before initialization of
# compat.py module, so it can access it before starting to import Qt classes
from prismriver.qt.controller import MainController

MainController(config, params.artist, params.title, params.mpris, params.connect, params.tray)

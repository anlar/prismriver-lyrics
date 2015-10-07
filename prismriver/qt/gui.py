import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from prismriver.qt.tray import TrayIcon
from prismriver.qt.window import MainWindow
from prismriver import util


def run():
    parser = create_args_parser()
    # skip unknown args, some of them may be handled as common qt options
    # see: http://doc.qt.io/qt-5/qguiapplication.html
    params, unknown = parser.parse_known_args()

    util.init_logging(params.quiet, params.verbose, params.log)

    search_config = util.init_search_config(params)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('prismriver/pixmaps/prismriver-lunasa.png'))
    app.setApplicationName('Lunasa Prismriver')

    main = MainWindow(params.artist, params.title, params.mpris, params.connect, search_config)
    main.setGeometry(0, 0, 1024, 1000)
    main.setWindowTitle('Lunasa Prismriver')

    show_tray = (params.tray != 'hide')
    show_main = (params.tray != 'minimize')

    if show_main:
        main.show()

    if show_tray:
        tray = TrayIcon(main)
        tray.setIcon(QIcon('prismriver/pixmaps/prismriver-lunasa.png'))

        main.search_results_updated.connect(tray.show_notification)

        tray.show()

    sys.exit(app.exec_())


def create_args_parser():
    parser = util.init_args_parser()

    parser.add_argument('-m', '--mpris', help='default MPRIS-player name')
    parser.add_argument('--connect', action='store_true', help='connect to player and listen for song details')

    parser.add_argument('--tray', default='show', choices=('show', 'minimize', 'hide'), help='tray help')

    return parser

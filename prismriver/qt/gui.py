import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from prismriver.qt.window import MainWindow
from prismriver import util


def run():
    parser = util.init_args_parser()
    params = parser.parse_args()

    util.init_logging(params.quiet, params.verbose, params.log)

    search_config = util.init_search_config(params)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('prismriver/pixmaps/prismriver-lunasa.png'))
    app.setApplicationName('Lunasa Prismriver')

    main = MainWindow(params.artist, params.title, search_config)
    main.setGeometry(0, 0, 1024, 1000)
    main.setWindowTitle('Lunasa Prismriver')
    main.show()

    sys.exit(app.exec_())

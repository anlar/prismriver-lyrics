import sys

from PyQt5.QtGui import QIcon

from PyQt5.QtWidgets import QApplication

from prismriver.qt.window import MainWindow
from prismriver import util


def run():
    util.init_logging(False, True, None)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('prismriver/pixmaps/prismriver-lunasa.png'))

    main = MainWindow()

    sys.exit(app.exec_())

import sys

from PyQt5.QtWidgets import QApplication

from prismriver.qt.window import MainWindow
from prismriver import util


def run():
    util.init_logging(False, True, None)

    app = QApplication(sys.argv)
    main = MainWindow()
    sys.exit(app.exec_())

import sys

from PyQt5.QtGui import QIcon

from PyQt5.QtWidgets import QApplication

from prismriver.qt.window import MainWindow
from prismriver import util


def run():
    util.init_logging(False, True, None)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('prismriver/pixmaps/prismriver-lunasa.png'))
    app.setApplicationName('Lunasa Prismriver')

    main = MainWindow()
    main.setGeometry(0, 0, 1024, 1000)
    main.setWindowTitle('Lunasa Prismriver')
    main.show()

    sys.exit(app.exec_())

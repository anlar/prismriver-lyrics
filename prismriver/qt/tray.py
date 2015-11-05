from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu


class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        self.setIcon(QIcon('prismriver/pixmaps/prismriver-lunasa.png'))

        self.right_menu = QMenu()
        self.setContextMenu(self.right_menu)

import os

from prismriver.qt.compat import QSystemTrayIcon, QIcon, QMenu


class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        path = os.path.dirname(os.path.abspath(__file__))
        self.setIcon(QIcon(os.path.join(path, 'pixmaps', 'prismriver.png')))

        self.right_menu = QMenu()
        self.setContextMenu(self.right_menu)

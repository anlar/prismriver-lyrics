from prismriver.qt.compat import QSystemTrayIcon, QIcon, QMenu


class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        self.setIcon(QIcon('prismriver/pixmaps/prismriver.png'))

        self.right_menu = QMenu()
        self.setContextMenu(self.right_menu)

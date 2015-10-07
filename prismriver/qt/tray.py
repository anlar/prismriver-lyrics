from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication


class TrayIcon(QSystemTrayIcon):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.activated.connect(self.toggle_main_window)

        self.right_menu = RightClickMenu(self.main_window)
        self.setContextMenu(self.right_menu)

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def toggle_main_window(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.main_window.isHidden():
                self.main_window.show()
            else:
                self.main_window.hide()

    def show_notification(self, artist, title, songs):
        if songs:
            self.showMessage(title + '\n' + artist,
                             'Found {} results'.format(len(songs)),
                             QSystemTrayIcon.NoIcon, 7000)


class RightClickMenu(QMenu):
    def __init__(self, main_window):
        super().__init__()

        show_action = QAction('Show &Main Window', self)
        show_action.triggered.connect(main_window.show)
        self.addAction(show_action)

        self.addSeparator()

        quit_action = QAction('&Quit', self)
        quit_action.triggered.connect(QApplication.quit)
        self.addAction(quit_action)

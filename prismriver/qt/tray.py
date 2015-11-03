from functools import partial

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication

from prismriver import mpris


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
        self.main_window = main_window

        self.aboutToShow.connect(self.update_actions)

    def update_actions(self):
        self.clear()

        show_action = QAction('Show &Main Window', self)
        show_action.triggered.connect(self.main_window.show)
        self.addAction(show_action)

        self.addSeparator()

        players = self.get_players()
        if players:
            for player in players:
                player_action = QAction(player.identity, self)
                player_action.setIcon(QIcon(mpris.get_player_icon_path(player.name)))
                player_action.triggered.connect(partial(self.main_window.toggle_mpris_listener, selected_player=player))
                self.addAction(player_action)

        self.addSeparator()

        quit_action = QAction('&Quit', self)
        quit_action.triggered.connect(QApplication.quit)
        self.addAction(quit_action)

    def get_players(self):
        return self.main_window.edit_player_model.players

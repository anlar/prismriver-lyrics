import random
import sys
import time

from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QStyle

from prismriver import main, util
from prismriver.mpris import MprisConnector, MprisConnectionException
from prismriver.qt.window import MainWindow, PlayerListModel


class MainController(object):
    def __init__(self, search_config, default_artist, default_title, default_player, connect_to_player):
        super().__init__()

        self.search_config = search_config
        self.state = State.default

        self.mpris_connect = MprisConnector()
        self.worker_search = None
        self.worker_mpris = None

        self.start_app(default_artist, default_title, default_player, connect_to_player)

    def start_app(self, default_artist, default_title, default_player, connect_to_player):
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon('prismriver/pixmaps/prismriver-lunasa.png'))
        app.setApplicationName('Lunasa Prismriver')

        self.main_window = MainWindow()

        self.main_window.edit_artist.setText(default_artist)
        self.main_window.edit_title.setText(default_title)

        self.main_window.btn_refresh.clicked.connect(self.refresh_players)

        self.init_layout(State.waiting)
        self.refresh_players(default_player)

        if connect_to_player:
            player = self.get_current_player()
            if player and (default_player is None or default_player == player.name):
                self.start_mpris()
        elif default_artist and default_title:
            self.start_search()

        self.main_window.show()

        sys.exit(app.exec_())

    def init_layout(self, state):
        try:
            self.main_window.btn_search.clicked.disconnect()
        except TypeError:
            pass

        try:
            self.main_window.btn_connect.clicked.disconnect()
        except TypeError:
            pass

        if state == State.waiting:
            self.main_window.btn_search.setIcon(
                QIcon.fromTheme('edit-find', self.main_window.style().standardIcon(QStyle.SP_BrowserReload)))
            self.main_window.btn_search.setText('Search...')
            self.main_window.btn_search.clicked.connect(self.start_search)

            self.main_window.btn_connect.setText('Connect...')
            self.main_window.btn_connect.clicked.connect(self.start_mpris)

            self.main_window.btn_search.setEnabled(True)
            self.main_window.btn_connect.setEnabled(True)
            self.main_window.btn_refresh.setEnabled(True)

            self.main_window.edit_artist.setReadOnly(False)
            self.main_window.edit_title.setReadOnly(False)
            self.main_window.edit_player.setEnabled(True)

        elif state == State.searching:
            self.main_window.btn_search.setIcon(
                QIcon.fromTheme('process-stop', self.main_window.style().standardIcon(QStyle.SP_BrowserStop)))
            self.main_window.btn_search.setText('Stop')
            self.main_window.btn_search.clicked.connect(self.interrupt_search)

            self.main_window.btn_connect.setText('Connect...')
            self.main_window.btn_connect.clicked.connect(self.start_mpris)

            self.main_window.btn_search.setEnabled(True)
            self.main_window.btn_connect.setEnabled(False)
            self.main_window.btn_refresh.setEnabled(False)

            self.main_window.edit_artist.setReadOnly(True)
            self.main_window.edit_title.setReadOnly(True)
            self.main_window.edit_player.setEnabled(False)

        elif state == State.listening:
            self.main_window.btn_search.setIcon(
                QIcon.fromTheme('edit-find', self.main_window.style().standardIcon(QStyle.SP_BrowserReload)))
            self.main_window.btn_search.setText('Search...')
            self.main_window.btn_search.clicked.connect(self.start_search)

            self.main_window.btn_connect.setText('Disconnect')
            self.main_window.btn_connect.clicked.connect(self.stop_mpris)

            self.main_window.btn_search.setEnabled(False)
            self.main_window.btn_connect.setEnabled(True)
            self.main_window.btn_refresh.setEnabled(False)

            self.main_window.edit_artist.setReadOnly(True)
            self.main_window.edit_title.setReadOnly(True)
            self.main_window.edit_player.setEnabled(False)

        else:
            return

        self.state = state

    def get_current_player(self):
        return self.main_window.edit_player.currentData(PlayerListModel.DataRole)

    def set_status_message(self, message):
        self.main_window.statusBar().showMessage(message)

    @pyqtSlot()
    def start_search(self, background=False):
        if not background:
            self.init_layout(State.searching)

        self.set_status_message('Searching...')

        self.worker_search = SearchThread(self.main_window.edit_artist.text(), self.main_window.edit_title.text(),
                                          self.search_config, background)
        self.worker_search.resultReady.connect(self.finish_search)
        self.worker_search.start()

    @pyqtSlot()
    def finish_search(self, worker_id, songs, total_time, background):
        if background:
            self.set_status_message('Listening to the player...')
            self.main_window.lyrics_table_model.update_data(songs)
        else:
            if not self.worker_search or (self.worker_search.worker_id != worker_id):
                return

            self.init_layout(State.waiting)
            self.set_status_message('Search completed in {}'.format(util.format_time_ms(total_time)))
            self.main_window.lyrics_table_model.update_data(songs)

    @pyqtSlot()
    def interrupt_search(self):
        self.init_layout(State.waiting)

        if self.worker_search:
            self.set_status_message('Search stopped')

            self.worker_search.quit()
            self.worker_search = None

    @pyqtSlot()
    def refresh_players(self, default_player):
        players = self.mpris_connect.get_players()
        self.main_window.edit_player.clear()
        self.main_window.edit_player_model.update_data(players)

        if players:
            if default_player:
                for pl in players:
                    if pl.name == default_player:
                        self.main_window.edit_player.setCurrentIndex(players.index(pl))
                        break
                else:
                    self.main_window.edit_player.setCurrentIndex(0)
            else:
                self.main_window.edit_player.setCurrentIndex(0)

    @pyqtSlot()
    def start_mpris(self):
        player = self.get_current_player()
        if player:
            self.init_layout(State.listening)
            self.set_status_message('Listening to the player...')

            self.worker_mpris = MprisThread(self.mpris_connect, player)

            self.worker_mpris.meta_ready.connect(self.update_mpris_results)
            self.worker_mpris.connection_closed.connect(self.stop_mpris)
            self.worker_mpris.start()

    @pyqtSlot()
    def stop_mpris(self):
        self.init_layout(State.waiting)
        self.set_status_message('Player listener stopped')
        self.worker_mpris.active = False

    @pyqtSlot()
    def update_mpris_results(self, meta):
        current_artist = self.main_window.edit_artist.text()
        current_title = self.main_window.edit_title.text()

        if (current_artist != meta[0] or current_title != meta[1]) and (meta[0] and meta[1]):
            self.main_window.edit_artist.setText(meta[0])
            self.main_window.edit_title.setText(meta[1])
            self.start_search(True)


class SearchThread(QThread):
    resultReady = pyqtSignal(int, list, float, bool)

    def __init__(self, artist, title, search_config, background):
        super().__init__()

        self.worker_id = random.randint(1, 999999999)

        self.artist = artist
        self.title = title
        self.search_config = search_config
        self.background = background

    def run(self):
        start_time = time.time()
        songs = main.search(self.artist, self.title, self.search_config)
        total_time = time.time() - start_time

        self.resultReady.emit(self.worker_id, songs, total_time, self.background)


class MprisThread(QThread):
    meta_ready = pyqtSignal(list)
    connection_closed = pyqtSignal(bool)

    def __init__(self, connector, player):
        super().__init__()

        self.connector = connector
        self.player = player
        self.active = True

    def run(self):
        try:
            if self.connector.connect(self.player):
                while self.active:
                    meta = self.connector.get_meta()
                    self.meta_ready.emit(meta)
                    time.sleep(2)
        except MprisConnectionException:
            self.connection_closed.emit(True)


class State(object):
    default = -1
    waiting = 1
    searching = 2
    listening = 3

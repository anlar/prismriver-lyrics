import time

from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant, pyqtSignal, QThread
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QLineEdit, QGridLayout, \
    QGroupBox, QVBoxLayout, QTextEdit, QPushButton, QStyle, QSplitter, QTableView, QHeaderView, QAbstractItemView, \
    QComboBox

from prismriver import util
from prismriver.main import search_async
from prismriver.mpris import MprisConnector, MprisConnectionException
from prismriver.struct import SearchConfig


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.worker_search = None
        self.worker_mpris = None

        self.mpris_connect = MprisConnector()

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.create_search_pane())
        main_layout.addWidget(self.create_result_pane(), 2)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.init_ui()

    def create_search_pane(self):
        group_box = QGroupBox('Search')

        self.btn_search = QPushButton()
        self.btn_search.setAutoDefault(True)
        self.btn_search.setDefault(True)

        self.btn_connect = QPushButton(
            QIcon.fromTheme('multimedia-player', self.style().standardIcon(QStyle.SP_BrowserStop)),
            'Connect...')
        self.btn_connect.clicked.connect(self.toggle_mpris_listener)

        self.btn_refresh = QPushButton(
            QIcon.fromTheme('view-refresh', self.style().standardIcon(QStyle.SP_BrowserReload)),
            'Refresh'
        )
        self.btn_refresh.clicked.connect(self.refresh_players)

        label_artist = QLabel('Artist')
        label_title = QLabel('Title')
        label_player = QLabel('Player')

        self.edit_artist = QLineEdit()
        self.edit_title = QLineEdit()
        self.edit_artist.returnPressed.connect(self.btn_search.click)
        self.edit_title.returnPressed.connect(self.btn_search.click)

        self.edit_player = QComboBox()
        players = self.mpris_connect.get_active_players()
        self.edit_player.addItems(players)

        grid = QGridLayout()

        grid.addWidget(label_artist, 0, 0)
        grid.addWidget(self.edit_artist, 0, 1)
        grid.addWidget(self.btn_search, 0, 2)

        grid.addWidget(label_title, 1, 0)
        grid.addWidget(self.edit_title, 1, 1)
        grid.addWidget(self.btn_connect, 1, 2)

        grid.addWidget(label_player, 2, 0)
        grid.addWidget(self.edit_player, 2, 1)
        grid.addWidget(self.btn_refresh, 2, 2)

        group_box.setLayout(grid)

        group_box.setTabOrder(self.edit_artist, self.edit_title)
        group_box.setTabOrder(self.edit_title, self.btn_search)

        return group_box

    def create_result_pane(self):
        main_group = QGroupBox('Results')
        main_layout = QVBoxLayout()

        split = QSplitter()
        split.setOrientation(Qt.Horizontal)

        self.lyric_table = LyricTableModel()
        self.lyric_table_view = QTableView()
        self.lyric_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lyric_table_view.setModel(self.lyric_table)
        self.lyric_table_view.setColumnWidth(3, 50)
        self.lyric_table_view.verticalHeader().setVisible(False)
        self.lyric_table_view.horizontalHeader().setHighlightSections(False)
        self.lyric_table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.lyric_table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        self.lyric_table_view.selectionModel().selectionChanged.connect(self.update_lyric_pane)

        self.lyric_text = QTextEdit()
        self.lyric_text.setReadOnly(True)

        split.addWidget(self.lyric_table_view)
        split.addWidget(self.lyric_text)

        main_layout.addWidget(split)
        main_group.setLayout(main_layout)

        return main_group

    def init_ui(self):
        self.setGeometry(0, 0, 1024, 1000)
        self.setWindowTitle('Lunasa Prismriver')
        self.toggle_buttons_on_search(False)
        self.set_status_message(None)
        self.show()

    def set_status_message(self, message):
        self.statusBar().showMessage(message)

    def start_search(self, is_manual):
        if is_manual:
            self.toggle_buttons_on_search(True)

        self.set_status_message('Searching...')

        self.worker_search = SearchThread(self.edit_artist.text(), self.edit_title.text(), is_manual)
        self.worker_search.resultReady.connect(self.update_search_results)
        self.worker_search.start()

    def stop_search(self):
        if self.worker_search and self.worker_search.isRunning():
            self.worker_search.terminate()
            self.toggle_buttons_on_search(False)
            self.set_status_message('Search stopped')

    def refresh_players(self):
        players = self.mpris_connect.get_active_players()
        self.edit_player.clear()
        self.edit_player.addItems(players)

    def toggle_mpris_listener(self, sudden_stop=False):
        if not sudden_stop and (self.worker_mpris is None or not self.worker_mpris.isRunning()):
            self.worker_mpris = MprisThread(self.mpris_connect, self.edit_player.currentText())
            self.worker_mpris.meta_ready.connect(self.update_search_results_mpris)
            self.worker_mpris.connection_closed.connect(self.toggle_mpris_listener)
            self.worker_mpris.start()
            self.toggle_buttons_on_connect(True)
            self.set_status_message('Listening to the player...')
        else:
            self.worker_mpris.terminate()
            self.toggle_buttons_on_connect(False)
            if sudden_stop:
                self.set_status_message('Player listener stopped (connection closed)')
            else:
                self.set_status_message('Player listener stopped')

    def toggle_buttons_on_search(self, is_started):
        try:
            self.btn_search.clicked.disconnect()
        except TypeError:
            pass

        if is_started:
            self.btn_search.setIcon(QIcon.fromTheme('process-stop', self.style().standardIcon(QStyle.SP_BrowserStop)))
            self.btn_search.setText('Stop')
            self.btn_search.clicked.connect(self.stop_search)
        else:
            self.btn_search.setIcon(QIcon.fromTheme('edit-find', self.style().standardIcon(QStyle.SP_BrowserReload)))
            self.btn_search.setText('Search...')
            self.btn_search.clicked.connect(lambda: self.start_search(True))

        self.edit_artist.setReadOnly(is_started)
        self.edit_title.setReadOnly(is_started)
        self.edit_player.setEnabled(not is_started)

        self.btn_connect.setEnabled(not is_started)
        self.btn_refresh.setEnabled(not is_started)

    def toggle_buttons_on_connect(self, is_connected):
        self.btn_search.setEnabled(not is_connected)
        self.btn_refresh.setEnabled(not is_connected)

        self.edit_artist.setReadOnly(is_connected)
        self.edit_title.setReadOnly(is_connected)
        self.edit_player.setEnabled(not is_connected)

        if is_connected:
            self.btn_connect.setText('Disconnect')
        else:
            self.btn_connect.setText('Connect...')

    def update_search_results(self, songs, process_time_sec, is_manual):
        self.lyric_table.update_data(songs)
        self.update_lyric_pane()

        if is_manual:
            self.toggle_buttons_on_search(False)
            self.set_status_message('Search completed in {}'.format(util.format_time_ms(process_time_sec)))
        else:
            self.set_status_message('Listening to the player...')

    def update_search_results_mpris(self, meta):
        current_artist = self.edit_artist.text()
        current_title = self.edit_title.text()

        if (current_artist != meta[0] or current_title != meta[1]) and (meta[0] and meta[1]):
            self.edit_artist.setText(meta[0])
            self.edit_title.setText(meta[1])
            self.start_search(False)

    def update_lyric_pane(self):
        selected = self.lyric_table_view.selectionModel().selectedRows()
        songs = []
        for sel in selected:
            songs.append(sel.data(LyricTableModel.DataRole))

        self.lyric_text.setText(format_lyrics(songs))


class LyricTableModel(QAbstractTableModel):
    DataRole = -101010

    def __init__(self, parent=None):
        super().__init__(parent)
        self.songs = []

    def rowCount(self, parent=None, *args, **kwargs):
        if self.songs:
            return len(self.songs)
        else:
            return 0

    def columnCount(self, parent=None, *args, **kwargs):
        return 4

    def data(self, index, role=None):
        row, col = index.row(), index.column()
        if role == Qt.DisplayRole:
            if self.songs[row]:
                if col == 0:
                    return QVariant(self.songs[row].plugin_name)
                elif col == 1:
                    return QVariant(self.songs[row].artist)
                elif col == 2:
                    return QVariant(self.songs[row].title)
                elif col == 3:
                    return QVariant(len(self.songs[row].lyrics))
        elif role == self.DataRole:
            return self.songs[row]

        return QVariant()

    def headerData(self, section, orientation, role=None):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == 0:
                    return QVariant('Plugin')
                elif section == 1:
                    return QVariant('Artist')
                elif section == 2:
                    return QVariant('Title')
                elif section == 3:
                    return QVariant('#')

        return QVariant()

    def update_data(self, songs):
        self.songs = songs
        self.layoutChanged.emit()


class SearchThread(QThread):
    resultReady = pyqtSignal(list, float, bool)

    def __init__(self, artist, title, is_manual):
        super().__init__()

        self.artist = artist
        self.title = title
        self.is_manual = is_manual

    def run(self):
        start_time = time.time()
        songs = search_async(self.artist, self.title, SearchConfig())
        total_time = time.time() - start_time

        self.resultReady.emit(songs, total_time, self.is_manual)


class MprisThread(QThread):
    meta_ready = pyqtSignal(list)
    connection_closed = pyqtSignal(bool)

    def __init__(self, connector, player):
        super().__init__()

        self.connector = connector
        self.player = player

    def run(self):
        try:
            if self.connector.connect(self.player):
                while True:
                    meta = self.connector.get_meta()
                    self.meta_ready.emit(meta)
                    time.sleep(2)
        except MprisConnectionException:
            self.connection_closed.emit(True)


def format_lyrics(songs):
    formatted_songs = []

    for song in songs:
        lyrics_txt = ''
        if song.lyrics:
            index = 0
            for lyric in song.lyrics:
                lyrics_txt += lyric
                if index < len(song.lyrics) - 1:
                    lyrics_txt += '\n\n<<< --- --- --- >>>\n\n'
                index += 1

        formatted_songs.append(lyrics_txt)

    result = ''
    index = 0
    for formatted_song in formatted_songs:
        result += formatted_song
        if index < len(formatted_songs) - 1:
            result += '\n\n<<< --- --- --- --- --- >>>\n\n'
        index += 1

    return result

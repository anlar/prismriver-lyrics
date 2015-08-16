import time

from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant, pyqtSignal, QThread
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QLineEdit, QGridLayout, \
    QGroupBox, QVBoxLayout, QTextEdit, QPushButton, QStyle, QSplitter, QTableView, QHeaderView, QAbstractItemView

from prismriver import util
from prismriver.main import search_async
from prismriver.struct import SearchConfig


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.create_search_pane())
        main_layout.addWidget(self.create_result_pane(), 2)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.init_ui()

    def create_search_pane(self):
        group_box = QGroupBox('Search')

        self.btn_search = QPushButton(QIcon.fromTheme('edit-find', self.style().standardIcon(QStyle.SP_BrowserReload)),
                                      'Search')
        self.btn_search.setAutoDefault(True)
        self.btn_search.setDefault(True)
        self.btn_search.clicked.connect(self.start_search)

        self.btn_stop = QPushButton(QIcon.fromTheme('process-stop', self.style().standardIcon(QStyle.SP_BrowserStop)),
                                    'Stop')
        self.btn_stop.clicked.connect(self.stop_search)

        label_artist = QLabel('Artist')
        label_title = QLabel('Title')

        self.edit_artist = QLineEdit()
        self.edit_title = QLineEdit()
        self.edit_artist.returnPressed.connect(self.btn_search.click)
        self.edit_title.returnPressed.connect(self.btn_search.click)

        grid = QGridLayout()

        grid.addWidget(label_artist, 0, 0)
        grid.addWidget(self.edit_artist, 0, 1)
        grid.addWidget(self.btn_search, 0, 2)

        grid.addWidget(label_title, 1, 0)
        grid.addWidget(self.edit_title, 1, 1)
        grid.addWidget(self.btn_stop, 1, 2)

        group_box.setLayout(grid)

        group_box.setTabOrder(self.edit_artist, self.edit_title)
        group_box.setTabOrder(self.edit_title, self.btn_search)
        group_box.setTabOrder(self.btn_search, self.btn_stop)

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
        self.setWindowTitle('Prismriver')
        self.toggle_search_buttons(False)
        self.set_status_message(None)
        self.show()

    def set_status_message(self, message):
        self.statusBar().showMessage(message)

    def start_search(self):
        self.toggle_search_buttons(True)
        self.set_status_message('Searching...')
        self.worker = SearchThread(self.edit_artist.text(), self.edit_title.text())
        self.worker.resultReady.connect(self.update_search_results)
        self.worker.start()

    def stop_search(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.toggle_search_buttons(False)
            self.set_status_message('Search process terminated')

    def update_search_results(self, songs, process_time_sec):
        self.lyric_table.update_data(songs)
        self.update_lyric_pane()
        self.toggle_search_buttons(False)
        self.set_status_message('Search completed in {}'.format(util.format_time_ms(process_time_sec)))

    def update_lyric_pane(self):
        selected = self.lyric_table_view.selectionModel().selectedRows()
        songs = []
        for sel in selected:
            songs.append(sel.data(LyricTableModel.DataRole))

        self.lyric_text.setText(self.format_lyrics(songs))

    def toggle_search_buttons(self, searching):
        self.btn_search.setEnabled(not searching)
        self.btn_stop.setEnabled(searching)

    def format_lyrics(self, songs):
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
    resultReady = pyqtSignal(list, float)

    def __init__(self, artist, title):
        super().__init__()
        self.artist = artist
        self.title = title

    def run(self):
        start_time = time.time()
        songs = search_async(self.artist, self.title, SearchConfig())
        total_time = time.time() - start_time

        self.resultReady.emit(songs, total_time)

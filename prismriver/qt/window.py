from prismriver import mpris
from prismriver.qt.compat import uic, QAbstractTableModel, Qt, pyqtSlot, QItemSelection, QStringListModel, QIcon, \
    QMainWindow, QAbstractItemView, QHeaderView, QStyle, use_pyqt5


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        uic.loadUi('prismriver/qt/window.ui', self)

        self.init_search_pane()
        self.init_table()

    def init_search_pane(self):
        self.btn_refresh.setIcon(
            QIcon.fromTheme('view-refresh', self.style().standardIcon(QStyle.SP_BrowserReload)))

        self.btn_connect.setIcon(
            QIcon.fromTheme('multimedia-player', self.style().standardIcon(QStyle.SP_ComputerIcon)))

        self.edit_artist.returnPressed.connect(self.btn_search.click)
        self.edit_title.returnPressed.connect(self.btn_search.click)

        self.edit_player_model = (PlayerListModel())
        self.edit_player.setModel(self.edit_player_model)

    def init_table(self):
        self.lyrics_table_model = LyricTableModel()
        self.lyrics_table_view.setModel(self.lyrics_table_model)
        self.lyrics_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lyrics_table_view.setColumnWidth(3, 50)
        self.lyrics_table_view.verticalHeader().setVisible(False)
        self.lyrics_table_view.horizontalHeader().setHighlightSections(False)

        if use_pyqt5:
            self.lyrics_table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.lyrics_table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        else:
            self.lyrics_table_view.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
            self.lyrics_table_view.horizontalHeader().setResizeMode(2, QHeaderView.Stretch)

        # there are 2 cases when we need to update lyric text pane:
        # 1) when lyric table has some values and selection were changed;
        # 2) when lyric table get update with empty info list - here selectionChanged signal won't be emitted
        self.lyrics_table_view.selectionModel().selectionChanged.connect(self.update_lyric_pane)
        self.lyrics_table_model.layoutChanged.connect(self.update_lyric_pane)

    @pyqtSlot(QItemSelection, QItemSelection)
    def update_lyric_pane(self):
        selected_songs = self.lyrics_table_view.selectionModel().selectedRows()
        songs = []
        for sel in selected_songs:
            songs.append(sel.data(LyricTableModel.DataRole))

        self.edit_lyrics.setText(format_lyrics(songs))


class PlayerListModel(QStringListModel):
    DataRole = -101010

    def __init__(self, *__args):
        super().__init__(*__args)
        self.players = []

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.players) if self.players else 0

    def data(self, index, role=None):
        row = index.row()

        if role == Qt.DisplayRole:
            if self.players[row]:
                return '{} [{}]'.format(self.players[row].identity, self.players[row].name)

        elif role == Qt.DecorationRole:
            if self.players[row]:
                return QIcon(mpris.get_player_icon_path(self.players[row].name))

        elif role == self.DataRole:
            return self.players[row]

    def update_data(self, players):
        self.players = players
        self.layoutChanged.emit()


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
                    return self.songs[row].plugin_name
                elif col == 1:
                    return self.songs[row].artist
                elif col == 2:
                    return self.songs[row].title
                elif col == 3:
                    return len(self.songs[row].lyrics)
        elif role == self.DataRole:
            return self.songs[row]

    def headerData(self, section, orientation, role=None):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == 0:
                    return 'Plugin'
                elif section == 1:
                    return 'Artist'
                elif section == 2:
                    return 'Title'
                elif section == 3:
                    return '#'

    @pyqtSlot(list)
    def update_data(self, songs):
        self.songs = songs
        self.layoutChanged.emit()


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

from prismriver.qt.gui import force_qt4

if force_qt4:
    use_pyqt5 = False
else:
    try:
        __import__('PyQt5')
        use_pyqt5 = True
    except ImportError:
        use_pyqt5 = False

if use_pyqt5:
    from PyQt5 import uic as uic
    from PyQt5.QtCore import pyqtSlot as pyqtSlot
    from PyQt5.QtCore import QThread as QThread
    from PyQt5.QtCore import pyqtSignal as pyqtSignal
    from PyQt5.QtCore import QAbstractTableModel as QAbstractTableModel
    from PyQt5.QtCore import Qt as Qt
    from PyQt5.QtCore import QStringListModel as QStringListModel
    from PyQt5.QtGui import QIcon as QIcon
    from PyQt5.QtWidgets import QSystemTrayIcon as QSystemTrayIcon
    from PyQt5.QtWidgets import QMenu as QMenu
    from PyQt5.QtWidgets import QApplication as QApplication
    from PyQt5.QtWidgets import QStyle as QStyle
    from PyQt5.QtWidgets import QAction as QAction
    from PyQt5.QtWidgets import QMainWindow as QMainWindow
    from PyQt5.QtWidgets import QAbstractItemView as QAbstractItemView
    from PyQt5.QtWidgets import QHeaderView as QHeaderView
else:
    from PyQt4 import uic as uic
    from PyQt4.QtCore import pyqtSlot as pyqtSlot
    from PyQt4.QtCore import QThread as QThread
    from PyQt4.QtCore import pyqtSignal as pyqtSignal
    from PyQt4.QtCore import QAbstractTableModel as QAbstractTableModel
    from PyQt4.QtCore import Qt as Qt
    from PyQt4.QtGui import QStringListModel as QStringListModel
    from PyQt4.QtGui import QIcon as QIcon
    from PyQt4.QtGui import QSystemTrayIcon as QSystemTrayIcon
    from PyQt4.QtGui import QMenu as QMenu
    from PyQt4.QtGui import QApplication as QApplication
    from PyQt4.QtGui import QStyle as QStyle
    from PyQt4.QtGui import QAction as QAction
    from PyQt4.QtGui import QMainWindow as QMainWindow
    from PyQt4.QtGui import QAbstractItemView as QAbstractItemView
    from PyQt4.QtGui import QHeaderView as QHeaderView

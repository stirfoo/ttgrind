# mainwin.py
# S. Edward Dolan
# Saturday, December 21 2024

import sys

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt as qt

from ttwidget import TTWidget

class MainWin(QMainWindow):
    def __init__(self, parent=None):
        super(MainWin, self).__init__(parent)
        self.createActions()
        self.createMenu()
        self.ttView = TTWidget(self)
        self.setCentralWidget(self.ttView)
        self.statusBar().showMessage("D:0.0000 Z:0.0000")
        self.setWindowTitle("TTGrind")
    def createActions(self):
        self.exitAct = QAction("E&xit", self, triggered=self.close)
    def createMenu(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.exitAct)
    def closeEvent(self, e):
        e.accept()
    def sizeHint(self):
        return QSize(800, 600)

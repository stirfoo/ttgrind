#!/usr/bin/python3

# ttgrind.py
# S. Edward Dolan
# Saturday, December 21 2024

import sys

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt as qt

from mainwin import MainWin

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # print(QStyleFactory.keys()) # print available styles
    
    app.setStyle(QStyleFactory.create("Windows"))
    win = MainWin()
    win.show()
    sys.exit(app.exec())


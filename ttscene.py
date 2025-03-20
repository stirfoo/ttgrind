# ttscene.py
# S. Edward Dolan
# Saturday, December 21 2024

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt as qt
        
class TTScene(QGraphicsScene):
    def __init__(self, parent=None):
        super(TTScene, self).__init__(QRectF(-5000, -5000, 10000, 10000),
                                      parent)
        self.pixelSize = 0.0
    def pixelsToScene(self, n):
        view = self.views()[0]
        return view.mapToScene(QRect(0, 0, n, n)).boundingRect().width()

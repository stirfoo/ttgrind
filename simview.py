# simview.py
# S. Edward Dolan
# Friday, January 17 2024

from pprint import pprint

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt as qt

from wheel import Wheel
from stock import Stock
from grindanim import GrindAnim

class SimView(QGraphicsView):
    """View a tool grinding simulation.
    """
    def __init__(self, scene, parent):
        super(SimView, self).__init__(parent)
        self.setStyleSheet("QGraphicsView { background-color: #2d3561; }")
        self.setRenderHints(QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(qt.ScrollBarAlwaysOff)
        self.setScene(scene)
        src = self.sceneRect().center()
        # move the scene origin to the center of the view and invert Y
        self.setTransform(QTransform().scale(1, -1)
                          .translate(src.x(), src.y()))
        self.fitInView(QRectF(-.5, -.5, 1.0, 1.0), qt.KeepAspectRatio)
        self.stock = None
        self.wheel = None
        self.program = None
        self.anim = GrindAnim(self)
    def onSpeedChanged(self, val):
        self.anim.setSpeed(val)
    def setStock(self, length, dia):
        if self.stock:
            self.scene().removeItem(self.stock)
        self.stock = Stock(length, dia)
        self.scene().addItem(self.stock)
        self.fitAll()
    def setWheel(self, width, dia):
        if self.wheel:
            self.scene().removeItem(self.wheel)
        self.wheel = Wheel(width, dia)
        self.wheel.hide()
        self.scene().addItem(self.wheel)
    def setProgram(self, program):
        self.program = program
    def show(self):
        self.anim.start(self.stock, self.wheel, self.program)
        super(SimView, self).show()
    def hide(self):
        # stop the simulation
        if self.anim is not None and self.anim.isRunning():
            self.anim.reset()
        super(SimView, self).hide()
    def updatePixelSize(self):
        sz = self.mapToScene(QRect(0, 0, 1, 1)).boundingRect().width()
        self.scene().pixelSize = sz
        return sz
    def fitAll(self):
        if self.stock:
            r = self.stock.sceneBoundingRect()
            x = r.width() * .01
            self.fitInView(r.adjusted(-x, -x, x, x), qt.KeepAspectRatio)
            ps = self.updatePixelSize()
    def resizeEvent(self, e):
        super(SimView, self).resizeEvent(e)
        self.fitAll()
    def mousePressEvent(self, e):
        # eat it
        pass
    def keyPressEvent(self, e):
        # eat it
        pass
    def wheelEvent(self, e):
        # eat it
        pass
    

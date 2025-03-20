# ttview.py
# S. Edward Dolan
# Saturday, December 21 2024

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt as qt

from dim.dimension import LinearDim, DimLabel
from tttooldef import TTToolDef, TTPointDef
from floatedit import DimEdit

class TTToolView(QGraphicsView):
    """View and edit a tool profile to be ground on the Tru-Tech grinder.
    """
    def __init__(self, scene, parent):
        super(TTToolView, self).__init__(parent)
        self.setStyleSheet("QGraphicsView { background-color: #2d3561; }")
        self.setRenderHints(QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.setScene(scene)
        src = self.sceneRect().center()
        # move the scene origin to the center of the view and invert Y
        self.setTransform(QTransform().scale(1, -1)
                          .translate(src.x(), src.y()))
        self.ttDef = None
        self.dimBox = DimEdit(self)
        self.dimBox.hide()
        # 
        # TODO: possibly configure a tooldef with check boxen
        # 
        # self.chkbox = QCheckBox("Point?", self)
        # self.chkbox.setStyleSheet("QCheckBox { color: #00ff00; }"
        #                           "QCheckBox:checked {"
        #                           "color: red;}")
        self.fitInView(QRectF(-.5, -.5, 1.0, 1.0), qt.KeepAspectRatio)
    def setToolDef(self, ttDef):
        if self.ttDef:
            if self.ttDef == ttDef:
                return
            self.scene().removeItem(self.ttDef)
        self.ttDef = ttDef
        self.scene().addItem(self.ttDef)
        self.fitAll()
    def getStockDims(self):
        return self.ttDef.specs['blankLength'], self.ttDef.specs['blankDia']
    def getToolSpecs(self):
        return self.ttDef.specs
    def getToolProfile(self):
        return self.ttDef.getPathElements()
    def updatePixelSize(self):
        sz = self.mapToScene(QRect(0, 0, 1, 1)).boundingRect().width()
        self.scene().pixelSize = sz
        return sz
    def fitAll(self):
        ps = 0
        iters = 1
        items = self.scene().items()
        while True:
            r = QRectF()
            for item in items:
                if not item.parentItem():
                    r = r.united(item.sceneBoundingRect())
            x = r.width() * .01 # a bit of padding
            self.fitInView(r.adjusted(-x, -x, x, x), qt.KeepAspectRatio)
            pps = self.updatePixelSize()
            for item in items:
                if isinstance(item, TTToolDef):
                    item.config()
            if iters == 20 or abs(ps - pps) < 0.0001:
                break
            ps = pps
            iters += 1
    def resizeEvent(self, e):
        super(TTToolView, self).resizeEvent(e)
        self.fitAll()
        if self.dimBox.isVisible():
            self.positionDimBox(self.dimBox)
    def mouseMoveEvent(self, e):
        """Show the mouse position as (D=0.0000 Z=0.0000) in the status bar.
        """
        p = self.mapToScene(e.pos())
        tip = "D={:.4f} Z={:.4f}".format(abs(p.y() * 2), p.x())
        QApplication.sendEvent(self, QStatusTipEvent(tip))
        super(TTToolView, self).mouseMoveEvent(e)
    def mousePressEvent(self, e):
        if e.button() == qt.LeftButton:
            item = self.itemAt(e.pos())
            self.dimBox.hide()
            if item and isinstance(item, DimLabel):
                box = self.dimBox
                box.setItems(item, self.ttDef)
                box.setText(item.text())
                box.selectAll()
                box.show()
                self.positionDimBox(box)
                box.setFocus()
    def positionDimBox(self, box):
        """Ensure the dimension edit text box is not clipped if possible.

        If both the left and right sides are clipped, it's just centered over
        the dim as if it were not clipped.
        """
        item = box.dimLabel
        viewpos = self.mapFromScene(item.pos())
        sz = box.size()
        lclip = min(0, viewpos.x() - sz.width() / 2.0)
        rclip = max(0, viewpos.x() + sz.width() / 2.0 - self.width())
        if lclip and rclip or not lclip and not rclip:
            box.move(int(viewpos.x() - sz.width() / 2),
                     int(viewpos.y() - sz.height() / 2))
        elif lclip:
            box.move(int(viewpos.x() - sz.width() / 2 - lclip),
                     int(viewpos.y() - sz.height() / 2))
        elif rclip:
            box.move(int(viewpos.x() - sz.width() / 2 - rclip),
                     int(viewpos.y() - sz.height() / 2))
    def keyPressEvent(self, e):
        """Ignore all keys.
        """
        pass
    def wheelEvent(self, e):
        """Ignore the mouse wheel.

        This will prevent the wheel from scrolling the view.
        """
        pass
    

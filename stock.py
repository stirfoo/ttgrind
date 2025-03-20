# stock.py
# S. Edward Dolan
# Saturday, January 18 2025

from PyQt5.QtCore import QObject, QLineF
from PyQt5.QtWidgets import QGraphicsPathItem
from PyQt5.QtGui import QTransform, QColor, QPen, QBrush
from PyQt5.QtCore import Qt as qt

from path2d import Path2d
from tttooldef import TTToolDef

mirTy = QTransform().scale(1.0, -1.0)

class Stock(QGraphicsPathItem):
    def __init__(self, length, dia):
        super(Stock, self).__init__()
        self.length = length
        self.dia = dia
        pen = QPen(TTToolDef.lineColor)
        pen.setWidth(0)
        pen.setCosmetic(True)
        pen.setCapStyle(qt.RoundCap)
        pen.setJoinStyle(qt.RoundJoin)
        self.setPen(pen)
        self.setBrush(TTToolDef.fillBrush)
        self.reset()
    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        r = range(self.path().elementCount())
        for i, j in zip(r, r[1:]):
            a = self.path().elementAt(i)
            b = self.path().elementAt(j)
            if a.isMoveTo():
                sp = a
                continue
            l1 = QLineF(sp.x, sp.y, a.x, a.y)
            l2 = QLineF(a.x, a.y, b.x, b.y)
            ang = l1.angleTo(l2)
            if abs(ang) > .01:
                painter.drawLine(QLineF(a.x, a.y, a.x, -a.y))
        # for i in range(self.path().elementCount()):
        #     e = self.path().elementAt(i)
        #     if e.isLineTo():
        #         painter.drawLine(QLineF(e.x, e.y, e.x, -e.y))
    def reset(self):
        self.prepareGeometryChange()
        r = self.dia / 2.0
        p2d = Path2d([0, -r])
        p2d.lineTo(0, r)
        p2d.lineTo(self.length, r)
        p2d.lineTo(self.length, -r)
        p2d.lineTo(0, -r)
        pp = p2d.toQPainterPath()
        # pp.addPath(mirTy.map(pp))
        self.setPath(pp)
        

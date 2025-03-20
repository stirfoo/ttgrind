# wheel.py
# S. Edward Dolan
# Saturday, January 18 2025

from PyQt5.QtCore import QObject, QRectF
from PyQt5.QtWidgets import QGraphicsObject
from PyQt5.QtGui import QTransform, QColor, QPen, QBrush
from PyQt5.QtCore import Qt as qt

from path2d import Path2d
from tttooldef import TTToolDef

mirTy = QTransform().scale(1.0, -1.0)

class Wheel(QGraphicsObject):
    """A 1A1 grinding wheel.
    The wheel has a width and diameter and will be rendered as a rectangle.
    The origin of the wheel is the lower right corner.
    """
    color = QColor(255, 128, 255)
    wheelTaper = .002           # dressed taper in the wheel
    def __init__(self, width, dia):
        super(Wheel, self).__init__()
        self.width = width
        self.diameter = dia
        self.pen = QPen(self.color)
        self.pen.setWidth(0)
        self.pen.setCosmetic(True)
        self.pen.setCapStyle(qt.RoundCap)
        self.pen.setJoinStyle(qt.RoundJoin)
        self.brush = QBrush(self.color)
        # p3 *-------* p4
        #    |       |
        #    |       |
        #    |       |
        #    |       |
        # p2 *-------O p1
        p2d = Path2d([0, 0])                     # p1
        p2d.lineTo(-self.width, self.wheelTaper) # p2
        p2d.lineTo(-self.width, dia)             # p3
        p2d.lineTo(0, dia)                       # p4
        p2d.lineTo(0, 0)                         # p1
        self.pp = p2d.toQPainterPath()
    def boundingRect(self):
        return self.pp.boundingRect()
    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        painter.drawPath(self.pp)
    def smearLinear(self, px, py, dx, dy):
        """Return a QPainterPath of this wheel extruded by dx and dy.
        The path is also mirrored about the y axis if the wheel is above
        the centerline.
        """
        # print(px, py, dx, dy)
        belowZero = False
        w = self.width
        d = self.diameter
        #  p3 *--------* p2
        #     |        | 
        #     |        | 
        #     |        | 
        #     |        |
        #  p4 *--------* p1
        p1 = [px, py]
        p2 = [px, py + d]
        p3 = [px - w, py + d]
        p4 = [px - w, py + self.wheelTaper]
        p2d = Path2d()
        if dx == 0:
            # possible plunge move in Y            
            if dy == 0:
                return self.shape() # no move
            elif dy > 0:
                # 90 vertical move up, nothing to do
                return None
            else:
                # 270 extrude the wheel vertically down
                if p1[1] + dy < 0:
                    belowZero = True # wheel crossed the centerline
                sp = [p1[0], p1[1] + dy]
                p2d.moveTo(*sp)
                p2d.lineTo(*p2)
                p2d.lineTo(*p3)
                p2d.lineTo(p4[0], p4[1] + dy)
                p2d.lineTo(*sp)
        elif dx > 0:
            # wheel moving right (+X)
            if dy == 0:
                # extrude the wheel to the right
                if p1[1] < 0:
                    belowZero = True
                p2d.moveTo(*p4)
                p2d.lineTo(p1[0] + dx, p1[1])
                p2d.lineTo(p1[0] + dx, p2[1])
                p2d.moveTo(*p3)
                p2d.lineTo(*p4)
            elif dy > 0:
                # extrude the wheel up and right
                if p1[1] < 0:
                    belowZero = True
                p2d.moveTo(*p4)
                p2d.lineTo(*p1)
                p2d.lineTo(p1[0] + dx, p1[1] + dy)
                p2d.lineTo(p2[0] + dx, p2[1] + dy)
                p2d.lineTo(p3[0] + dx, p3[1] + dy)
                p2d.moveTo(*p3)
                p2d.lineTo(*p4)
            else:
                # extrude the wheel down and right
                if p1[1] + dy < 0:
                    belowZero = True
                p2d.moveTo(*p4)
                p2d.lineTo(p4[0] + dx, p4[1] + dy)
                p2d.lineTo(p1[0] + dx, p1[1] + dy)
                p2d.lineTo(p2[0] + dx, p2[1] + dy)
                p2d.lineTo(*p2)
                p2d.lineTo(*p3)
                p2d.lineTo(*p4)
        elif dx < 0:                   
            # wheel moving left (-X)
            if dy == 0:
                # extrude the wheel to the left
                if p1[1] < 0:
                    belowZero = True
                p2d.moveTo(*p1)
                p2d.lineTo(*p2)
                p2d.lineTo(p3[0] + dx, p3[1])
                p2d.lineTo(p4[0] + dx, p4[1])
                p2d.lineTo(p1[0] + dx, p1[1])
                p2d.lineTo(*p1)
            elif dy > 0:
                # extrude the wheel left and up
                if p1[1] < 0:
                    belowZero = True
                p2d.moveTo(*p1)
                p2d.lineTo(*p2)
                p2d.lineTo(p2[0] + dx, p2[1] + dy)
                p2d.lineTo(p3[0] + dx, p3[1] + dy)
                p2d.lineTo(p4[0] + dx, p4[1] + dy)
                p2d.lineTo(p1[0] + dx, p1[1] + dy)
                p2d.lineTo(*p1)
                # p2d.moveTo(*p4)
                # p2d.lineTo(*p1)
                # p2d.lineTo(*p2)
                # p2d.lineTo(p2[0] + dx, p2[1] + dy)
                # p2d.lineTo(p3[0] + dx, p3[1] + dy)
                # p2d.lineTo(p4[0] + dx, p4[1] + dy)
                # p2d.lineTo(*p4)
            elif dy < 0:
                # extrude the wheel down and left
                if p1[1] + dy < 0:
                    belowZero = True
                p2d.moveTo(*p1)
                p2d.lineTo(*p2)
                p2d.lineTo(*p3)
                p2d.lineTo(p3[0] + dx, p2[1] + dy)
                p2d.lineTo(p4[0] + dx, p4[1] + dy)
                p2d.lineTo(p1[0] + dx, p1[1] + dy)
                p2d.lineTo(*p1)
        pp = p2d.toQPainterPath()
        if not belowZero:
            pp.addPath(mirTy.map(pp))
        return pp

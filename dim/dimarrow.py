# dimarrow.py
# S. Edward Dolan
# Friday, December 27 2024

from copy import copy
from math import degrees, atan2

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt as qt

class DimArrow(QGraphicsPathItem):
    """Graphical representation of a dimension arrow head.

    Use the config method to update with the following specMap:

    String Key   Value Type   Value Description
    ----------   ----------   -------------------------------------------
    pos          QPointF      Position of arrow tip in screen coordinates
    dir          QVector2D    Direction the arrow points

    The arrow tip is at this item's local origin.
    """
    length = 14                 # pixels
    width = 5                   # pixels
    color = QColor(0, 255, 0)
    def __init__(self, parent,
                 specMap={'pos': QPointF(), 'dir': QVector2D(1, 0)}):
        if specMap['dir'].isNull():
            raise DimArrowException('zero magnitude arrow vector')
        super(DimArrow, self).__init__(parent)
        self.setPen(self.color)
        self.setBrush(QBrush(self.color))
        self.setFlag(self.ItemIgnoresTransformations, True)
        self.specMap = copy(specMap)
        self.config()
    def config(self, specMap={}):
        """Set geometry
        """
        self.prepareGeometryChange()
        self.specMap.update(specMap)
        if self.specMap['dir'].isNull():
            raise DimArrowException('zero magnitude arrow vector')
        self.setPos(self.specMap['pos'])
        v = self.specMap['dir']
        self.specMap['rotAngle'] = degrees(atan2(v.y(), v.x()))
        self._updatePainterPath()
    def setRotation():
        """Noop
        
        Rotations are done manually in _updatePainterPath()
        """
        pass
    def sceneBoundingRect(self):
        scene = self.scene()
        if scene:
            # what a hack O_o
            view = scene.views()[0]
            brect = self.boundingRect().toRect()
            zero = view.mapToScene(QPoint())
            br = view.mapToScene(brect).boundingRect()
            br.moveTopLeft(self.pos() + (br.topLeft() - zero))
            return br
        else:
            return QRectF()
    def _updatePainterPath(self):
        t = QTransform().rotate(-self.specMap['rotAngle'])
        p1 = t.map(QPointF(-self.length, self.width / 2.0))
        p2 = t.map(QPointF(-self.length, -self.width / 2.0))
        pp = QPainterPath()
        pp.moveTo(0, 0)
        pp.lineTo(p1.x(), p1.y())
        pp.lineTo(p2.x(), p2.y())
        pp.lineTo(0, 0)
        self.setPath(pp)

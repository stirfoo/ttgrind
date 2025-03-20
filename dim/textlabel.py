# textlabel.py
# S. Edward Dolan
# Friday, December 27 2024

from copy import copy

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt as qt

class TextLabel(QGraphicsItem):
    """Graphical representation of a single-line text label.

    The item consists of:
      * An empty rectangle the size of the text's bounding rect.
      * The text which is centered on this item's local origin.
    
    Use the config method to update with the following specMap:
    
    String Key   Value Type   Value Description
    ----------   ----------   -----------------------------------------
    pos          QPointF      This item's position in screen coordinates
    text         string       The text to display

    Will render the bounding rect when hovered.
    """
    def __init__(self, parent=None, specMap={'pos': QPointF(),
                                             'text': '1.0'}):
        super(TextLabel, self).__init__(parent)
        self.setFlag(self.ItemIgnoresTransformations, True)
        self.specMap = copy(specMap)
        self.font = QLineEdit().font()
        self.pen = QPen(QColor(0, 255, 0))
        self.setAcceptHoverEvents(True)
        self.config(specMap)
    def text(self):
        return self.specMap['text']
    def config(self, specMap={}):
        self.prepareGeometryChange()
        self.specMap.update(specMap)
        self.setPos(self.specMap['pos'])
        text = self.specMap['text']
        fm = QFontMetrics(self.font)
        r = QRectF(fm.boundingRect(text))
        x = r.width() * .05
        r.adjust(-x, -x, x, x)
        c = r.center()
        self.textOrigin = -c
        r.translate(-c)
        self.textBoundingRect = r
        self.hovered = False
    def boundingRect(self):
        return self.textBoundingRect
    def sceneBoundingRect(self):
        scene = self.scene()
        if scene:
            view = scene.views()[0]
            brect = self.boundingRect().normalized().toRect()
            br = view.mapToScene(brect).boundingRect()
            br.moveCenter(self.pos())
            return br
        else:
            return QRectF()
    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        painter.setFont(self.font)
        painter.drawText(self.textOrigin, self.specMap['text'])
        if self.hovered:
            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.setBrush(qt.NoBrush)
            painter.drawRect(self.textBoundingRect)
    def hoverEnterEvent(self, e):
        self.hovered = True
        self.update()
    def hoverLeaveEvent(self, e):
        self.hovered = False
        self.update()

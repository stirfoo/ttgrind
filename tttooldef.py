# tttooldef.py
# S. Edward Dolan
# Saturday, December 28 2024

from copy import copy
from math import tan, radians, acos

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt as qt

from path2d import Path2d
from dim.dimension import *

mirTx = QTransform().scale(1.0, -1.0)

class TTToolDef(QGraphicsPathItem):
    """Base class for all Tru-Tech tool definitions.
    """
    lineColor = QColor(255, 255, 255) # tool outline
    fillColor = QColor(100, 100, 100) # tool fill
    fillBrush = QBrush(fillColor)     # tool fill
    grindColor = QColor(254, 138, 24) # orange-ish
    grindBrush = QBrush(grindColor)   # ground section of the profile
    def __init__(self, specs):
        super().__init__()
        pen = QPen(self.lineColor)
        pen.setWidth(0)
        pen.setCosmetic(True)
        pen.setCapStyle(qt.RoundCap)
        pen.setJoinStyle(qt.RoundJoin)
        self.setPen(pen)
        self.setBrush(self.fillBrush)
        # the upper half of the tool profile
        self._profile = None
        self.specs = copy(specs)
        self.prepareGeometryChange()
        self._updateProfile()
    def checkGeometry(self, specs={}):
        return True
    def config(self, specs={}):
        """Change the specs of the tool def.

        If any key/val pair is different from this tool def's specs, update
        the profile with the new specs.

        The dims are always updated.
        """
        self.prepareGeometryChange()
        for k, v in specs.items():
            if self.specs[k] != v:
                self.specs.update(copy(specs))
                self._updateProfile()
                break
        self._updateDims()
    def sceneBoundingRect(self):
        return self.path().boundingRect()
    def sceneChange(self, scene):
        if scene:
            self.show()
        else:
            self.hide()
    def itemChange(self, change, value):
        super().itemChange(change, value)
        if change == self.ItemSceneChange:
            self.sceneChange(value)
        return value
    def getPathElements(self):
        return self._profile.elements()

class TTPointDef(TTToolDef):
    """A tool where only the point is ground.

    specs:
      blankDia
      blankLength
      tipAngle
    """
    def __init__(self, specs={'blankDia': .5,
                              'blankLength': 2,
                              'tipAngle': 118}):
        super().__init__(specs)
        self.blankDiaDim = LinearDim('blankDia')
        self.blankLengthDim = LinearDim('blankLength')
        self.tipAngleDim = AngleDim('tipAngle')
    def paint(self, painter, option, widget):
        """Fill the ground section of the profile in a different color.
        """
        super().paint(painter, option, widget)
        br = self.specs['blankDia'] / 2.0
        ta = self.specs['tipAngle']
        x = br / tan(radians(ta / 2.0))
        pp = QPainterPath()
        pp.moveTo(0, 0)
        pp.lineTo(x, br)
        pp.lineTo(x, -br)
        pp.lineTo(0, 0)
        painter.fillPath(pp, self.grindBrush) # order
        painter.setBrush(qt.NoBrush)          # matters
        painter.drawPath(pp)                  # here
    def sceneChange(self, scene):
        super().sceneChange(scene)
        if scene:
            scene.addItem(self.blankDiaDim)
            self.blankDiaDim.show()
            scene.addItem(self.blankLengthDim)
            self.blankLengthDim.show()
            scene.addItem(self.tipAngleDim)
            self.tipAngleDim.show()
        else:
            self.scene().removeItem(self.blankDiaDim)
            self.blankDiaDim.hide()
            self.scene().removeItem(self.blankLengthDim)
            self.blankLengthDim.hide()
            self.scene().removeItem(self.tipAngleDim)
            self.tipAngleDim.hide()
    def checkGeometry(self, specs={}):
        d = copy(self.specs)
        d.update(specs)
        bd = d['blankDia']
        oal = d['blankLength']
        ta = d['tipAngle']
        tl = tipLength(ta, bd)
        return (bd > 0 and oal > 0 and ta > 0 and ta < 180 and oal > tl)
    def _updateProfile(self):
        br = self.specs['blankDia'] / 2
        oal = self.specs['blankLength']
        ta = self.specs['tipAngle']
        p2d = Path2d([0, 0])
        x = br / tan(radians(ta / 2.0))
        p2d.lineTo(x, br)
        p2d.lineTo(oal, br)
        p2d.lineTo(oal, 0)
        self._profile = p2d
        pp = p2d.toQPainterPath()
        pp.addPath(mirTx.map(pp))
        pp.moveTo(x, br)
        pp.lineTo(x, -br)
        self.setPath(pp)
    def _updateDims(self):
        bd = self.specs['blankDia']
        oal = self.specs['blankLength']
        a = self.specs['tipAngle']
        p1, p2, p3, p4 = self._profile.endPoints()
        ll = self.scene().pixelsToScene(Dimension.leaderLen)
        dlg = self.scene().pixelsToScene(Dimension.dimLabelGap)
        # blankDia
        dlbb = self.blankDiaDim.dimText.sceneBoundingRect()
        a1bb = self.blankDiaDim.arrow1.sceneBoundingRect()
        lx = oal + dlbb.width() / 2 + dlg
        ly = 0
        outside = False
        if a1bb.height() * 2 + dlbb.height() + dlg > bd:
            outside = True
            ly = -bd / 2 - ll - dlbb.height() / 2
        self.blankDiaDim.config({'value': bd,
                                 'ref1': QPointF(*p3),
                                 'ref2': QPointF(QPointF(p3[0], -p3[1])),
                                 'outside': outside,
                                 'format': FMTDIN,
                                 'pos': QPointF(lx, ly),
                                 'force': 'vertical'})
        # blankLength
        dlbb = self.blankLengthDim.dimText.sceneBoundingRect()
        a1bb = self.blankLengthDim.arrow1.sceneBoundingRect()
        lx = oal / 2
        ly = bd / 2 + dlbb.height() / 2 + dlg
        outside = False
        if a1bb.width() * 2 + dlbb.width() + dlg > oal:
            outside = True
            lx = -dlbb.width() / 2 - ll
        self.blankLengthDim.config({'value': oal,
                                    'ref1': QPointF(*p1),
                                    'ref2': QPointF(*p3),
                                    'outside': outside,
                                    'format': FMTIN,
                                    'pos': QPointF(lx, ly),
                                    'force': 'horizontal'})
        # tipAngle
        dlbb = self.tipAngleDim.dimText.sceneBoundingRect()
        a1bb = self.tipAngleDim.arrow1.sceneBoundingRect()
        lx = -bd / 2.0
        ly = 0
        outside = False
        # angle required to fit the label inside the lines
        v1 = QVector2D(-bd, dlbb.height() / 2 + a1bb.height())
        v2 = QVector2D(-bd, -dlbb.height() / 2 - a1bb.height())
        try:
            loa = degrees(acos(QVector2D.dotProduct(v1, v2)))
            if a < loa:
                outside = True
        except:
            pass
        self.tipAngleDim.config({'value': a,
                                 'pos': QPointF(lx, ly),
                                 'line1': QLineF(p1[0], p1[1], p2[0], p2[1]),
                                 'line2': QLineF(p1[0], p1[1], p2[0], -p2[1]),
                                 'outside': outside,
                                 'format': FMTANG,
                                 'quadV': QVector2D(-1, 0)})

class TTNeckDef(TTToolDef):
    """A tool where a reduced diameter is ground behind the cutting edge.

    specs:
      blankDia
      blankLength
      neckDia
      cutLength
      neckLength
      chamferAngle
    """
    def __init__(self, specs={'blankDia': .5,
                              'blankLength': 3.,
                              'neckDia': .47,
                              'cutLength': 1.,
                              'neckLength': 2.,
                              'chamferAngle': 45.}):
        super().__init__(specs)
        self.blankDiaDim = LinearDim('blankDia')
        self.blankLengthDim = LinearDim('blankLength')
        self.neckDiaDim = LinearDim('neckDia')
        self.cutLengthDim = LinearDim('cutLength')
        self.neckLengthDim = LinearDim('neckLength')
        self.chamferAngleDim = AngleDim('chamferAngle')
    def paint(self, painter, option, widget):
        """Fill the ground section of the profile in a different color.
        """
        super().paint(painter, option, widget)
        br = self.specs['blankDia'] / 2
        nr = self.specs['neckDia'] / 2
        cl = self.specs['cutLength']
        nl = self.specs['neckLength']
        r = QRectF(cl, nr, nl - cl, -nr * 2)
        painter.fillRect(r, self.grindBrush)
        painter.setBrush(qt.NoBrush)
        painter.drawRect(r)
        ca = self.specs['chamferAngle']
        if ca < 90.0:
            chLen = (br - nr) / tan(radians(ca))
            pp = QPainterPath()
            pp.moveTo(nl, nr)
            pp.lineTo(nl, -nr)
            pp.lineTo(nl + chLen, -br)
            pp.lineTo(nl + chLen, br)
            pp.lineTo(nl, nr)
            painter.fillPath(pp, self.grindBrush)
            painter.setBrush(qt.NoBrush)
            painter.drawPath(pp)
    def sceneChange(self, scene):
        super().sceneChange(scene)
        if scene:
            scene.addItem(self.blankDiaDim)
            self.blankDiaDim.show()
            scene.addItem(self.blankLengthDim)
            self.blankLengthDim.show()
            scene.addItem(self.neckDiaDim)
            self.neckDiaDim.show()
            scene.addItem(self.cutLengthDim)
            self.cutLengthDim.show()
            scene.addItem(self.neckLengthDim)
            self.neckLengthDim.show()
            scene.addItem(self.chamferAngleDim)
            self.chamferAngleDim.show()
        else:
            self.scene().removeItem(self.blankDiaDim)
            self.blankDiaDim.hide()
            self.scene().removeItem(self.blankLengthDim)
            self.blankLengthDim.hide()
            self.scene().removeItem(self.neckDiaDim)
            self.neckDiaDim.hide()
            self.scene().removeItem(self.cutLengthDim)
            self.cutLengthDim.hide()
            self.scene().removeItem(self.neckLengthDim)
            self.neckLengthDim.hide()
            self.scene().removeItem(self.chamferAngleDim)
            self.chamferAngleDim.hide()
    def checkGeometry(self, specs={}):
        d = copy(self.specs)
        d.update(specs)
        bd = d['blankDia']
        bl = d['blankLength']
        nd = d['neckDia']
        cl = d['cutLength']
        nl = d['neckLength']
        ca = d['chamferAngle']
        chLen = (bd - nd) / 2 / tan(radians(ca))
        # all > 0.0?
        if any(map(lambda x : x <= 0, d.values())):
            return False
        return (nd < bd and
                bl > nl and
                nl > cl and
                ca <= 90.0 and
                chLen < bl - nl)
    def _updateProfile(self):
        br = self.specs['blankDia'] / 2.0
        bl = self.specs['blankLength']
        nr = self.specs['neckDia'] / 2.0
        cl = self.specs['cutLength']
        nl = self.specs['neckLength']
        ca = self.specs['chamferAngle']
        chLen = 0.0
        if ca < 90.0:
            chLen = (br - nr) / tan(radians(ca))
        p2d = Path2d([0, 0])
        p2d.lineTo(0, br)
        p2d.lineTo(cl, br)
        p2d.lineTo(cl, nr)
        p2d.lineTo(nl, nr)
        # to chamfer or not to chamfer, that is the question
        if chLen == 0.0:
            p2d.lineTo(nl, br)
        else:
            p2d.lineTo(nl + chLen, br)
        p2d.lineTo(bl, br)
        p2d.lineTo(bl, 0)
        self._profile = p2d
        pp = p2d.toQPainterPath()
        pp.addPath(mirTx.map(pp))
        pp.moveTo(cl, nr)
        pp.lineTo(cl, -nr)
        pp.moveTo(nl, nr)
        pp.lineTo(nl, -nr)
        if chLen != 0.0:
            pp.moveTo(nl + chLen, br)
            pp.lineTo(nl + chLen, -br)
        self.setPath(pp)
    def _updateDims(self):
        bd = self.specs['blankDia']
        bl = self.specs['blankLength']
        nd = self.specs['neckDia']
        cl = self.specs['cutLength']
        nl = self.specs['neckLength']
        ca = self.specs['chamferAngle']
        chLen = (bd - nd) / 2 / tan(radians(ca))
        p1, p2, p3, p4, p5, p6, p7, p8 = self._profile.endPoints()
        ll = self.scene().pixelsToScene(Dimension.leaderLen)
        dlg = self.scene().pixelsToScene(Dimension.dimLabelGap)
        # blankDia
        dlbb = self.blankDiaDim.dimText.sceneBoundingRect()
        a1bb = self.blankDiaDim.arrow1.sceneBoundingRect()
        lx = bl + dlbb.width() / 2 + dlg
        ly = 0
        outside = False
        if a1bb.height() * 2 + dlbb.height() + dlg > bd:
            outside = True
            ly = -bd / 2 - ll - dlbb.height() / 2
        self.blankDiaDim.config({'value': bd,
                                 'ref1': QPointF(*p7),
                                 'ref2': QPointF(QPointF(p7[0], -p7[1])),
                                 'outside': outside,
                                 'format': FMTDIN,
                                 'pos': QPointF(lx, ly),
                                 'force': 'vertical'})
        # cutLength
        dlbb = self.cutLengthDim.dimText.sceneBoundingRect()
        a1bb = self.cutLengthDim.arrow1.sceneBoundingRect()
        lx = cl / 2
        ly = bd / 2 + dlbb.height() / 2 + dlg
        outside = False
        if a1bb.width() * 2 + dlbb.width() + dlg > cl:
            outside = True
            lx = -dlbb.width() / 2 - ll
        self.cutLengthDim.config({'value': cl,
                                  'ref1': QPointF(*p2),
                                  'ref2': QPointF(*p3),
                                  'outside': outside,
                                  'format': FMTIN,
                                  'pos': QPointF(lx, ly),
                                  'force': 'horizontal'})
        # neckLength
        dlbb = self.neckLengthDim.dimText.sceneBoundingRect()
        a1bb = self.neckLengthDim.arrow1.sceneBoundingRect()
        lx = nl / 2
        ly = bd / 2 + dlbb.height() * 2 + dlg
        outside = False
        if a1bb.width() * 2 + dlbb.width() + dlg > nl:
            outside = True
            lx = -dlbb.width() / 2 - ll
        if ca < 90.0:
            ref2 = p5
        else:
            ref2 = p6
        self.neckLengthDim.config({'value': nl,
                                   'ref1': QPointF(*p2),
                                   'ref2': QPointF(*ref2),
                                   'outside': outside,
                                   'format': FMTIN,
                                   'pos': QPointF(lx, ly),
                                   'force': 'horizontal'})
        # blankLength
        dlbb = self.blankLengthDim.dimText.sceneBoundingRect()
        a1bb = self.blankLengthDim.arrow1.sceneBoundingRect()
        lx = bl / 2
        ly = bd / 2 + dlbb.height() * 3.5 + dlg
        outside = False
        if a1bb.width() * 2 + dlbb.width() + dlg > bl:
            outside = True
            lx = -dlbb.width() / 2 - ll
        self.blankLengthDim.config({'value': bl,
                                    'ref1': QPointF(*p2),
                                    'ref2': QPointF(*p7),
                                    'outside': outside,
                                    'format': FMTIN,
                                    'pos': QPointF(lx, ly),
                                    'force': 'horizontal'})
        
        # neckDia
        dlbb = self.neckDiaDim.dimText.sceneBoundingRect()
        a1bb = self.neckDiaDim.arrow1.sceneBoundingRect()
        lx = cl + ((nl - cl) / 2)
        ly = -bd / 2 - ll - dlbb.height()
        self.neckDiaDim.config({'value': nd,
                                 'ref1': QPointF(lx, nd / 2),
                                 'ref2': QPointF(lx, -nd / 2),
                                 'outside': True, # always outside
                                 'format': FMTDIN,
                                 'pos': QPointF(lx, ly),
                                 'force': 'vertical'})
        # chamferAngle
        dlbb = self.chamferAngleDim.dimText.sceneBoundingRect()
        a1bb = self.chamferAngleDim.arrow1.sceneBoundingRect()
        lx = p6[0] - dlbb.width() - a1bb.width()
        ly = ly - dlbb.height()
        outside = True
        self.chamferAngleDim.config({'value': ca,
                                     'pos': QPointF(lx, ly),
                                     'line1': QLineF(p6[0], -p6[1], p7[0],
                                                     -p7[1]),
                                     'line2': QLineF(p5[0], -p5[1], p6[0],
                                                     -p6[1]),
                                     'outside': outside,
                                     'format': FMTANG,
                                     'quadV': QVector2D(1, -1)})

class TTSpindownDef(TTToolDef):
    """A tool where a dia is ground to a shoulder/bevel.

    specs:
      blankDia
      blankLength
      spinDia
      spinLength
      chamferAngle
    """
    def __init__(self, specs={'blankDia': .5,
                              'blankLength': 5.,
                              'spinDia': .3125 + .005,
                              'spinLength': .515,
                              'chamferAngle': 2.}):
        super().__init__(specs)
        self.blankDiaDim = LinearDim('blankDia')
        self.blankLengthDim = LinearDim('blankLength')
        self.spinDiaDim = LinearDim('spinDia')
        self.spinLengthDim = LinearDim('spinLength')
        self.chamferAngleDim = AngleDim('chamferAngle')
    def paint(self, painter, option, widget):
        """Fill the ground section of the profile in a different color.
        """
        super().paint(painter, option, widget)
        br = self.specs['blankDia'] / 2
        sr = self.specs['spinDia'] / 2
        sl = self.specs['spinLength']
        ca = self.specs['chamferAngle']
        r = QRectF(0, sr, sl, -sr * 2)
        painter.fillRect(r, self.grindBrush)
        painter.setBrush(qt.NoBrush)
        painter.drawRect(r)
        if ca < 90.0:
            chLen = (br - sr) / tan(radians(ca))
            pp = QPainterPath()
            pp.moveTo(sl, sr)
            pp.lineTo(sl, -sr)
            pp.lineTo(sl + chLen, -br)
            pp.lineTo(sl + chLen, br)
            pp.lineTo(sl, sr)
            painter.fillPath(pp, self.grindBrush)
            painter.setBrush(qt.NoBrush)
            painter.drawPath(pp)
    def sceneChange(self, scene):
        super().sceneChange(scene)
        if scene:
            scene.addItem(self.blankDiaDim)
            self.blankDiaDim.show()
            scene.addItem(self.blankLengthDim)
            self.blankLengthDim.show()
            scene.addItem(self.spinDiaDim)
            self.spinDiaDim.show()
            scene.addItem(self.spinLengthDim)
            self.spinLengthDim.show()
            scene.addItem(self.chamferAngleDim)
            self.chamferAngleDim.show()
        else:
            self.scene().removeItem(self.blankDiaDim)
            self.blankDiaDim.hide()
            self.scene().removeItem(self.blankLengthDim)
            self.blankLengthDim.hide()
            self.scene().removeItem(self.spinDiaDim)
            self.spinDiaDim.hide()
            self.scene().removeItem(self.spinLengthDim)
            self.spinLengthDim.hide()
            self.scene().removeItem(self.chamferAngleDim)
            self.chamferAngleDim.hide()
    def checkGeometry(self, specs={}):
        d = copy(self.specs)
        d.update(specs)
        bd = d['blankDia']
        bl = d['blankLength']
        sd = d['spinDia']
        sl = d['spinLength']
        ca = d['chamferAngle']
        chLen = (bd - sd) / 2 / tan(radians(ca))
        # all > 0.0?
        if any(map(lambda x : x <= 0, d.values())):
            return False
        return (sd < bd and
                ca <= 90.0 and
                chLen < bl - sl)
    def _updateProfile(self):
        br = self.specs['blankDia'] / 2.0
        bl = self.specs['blankLength']
        sr = self.specs['spinDia'] / 2.0
        sl = self.specs['spinLength']
        ca = self.specs['chamferAngle']
        chLen = 0.0
        if ca < 90.0:
            chLen = (br - sr) / tan(radians(ca))
        p2d = Path2d([0, 0])
        p2d.lineTo(0, sr)
        p2d.lineTo(sl, sr)
        # to chamfer or not to chamfer, that is the question
        if chLen == 0.0:
            p2d.lineTo(sl, br)
        else:
            p2d.lineTo(sl + chLen, br)
        p2d.lineTo(bl, br)
        p2d.lineTo(bl, 0)
        self._profile = p2d
        pp = p2d.toQPainterPath()
        pp.addPath(mirTx.map(pp))
        pp.moveTo(sl, sr)
        pp.lineTo(sl, -sr)
        if chLen != 0.0:
            pp.moveTo(sl + chLen, br)
            pp.lineTo(sl + chLen, -br)
        self.setPath(pp)
    def _updateDims(self):
        bd = self.specs['blankDia']
        bl = self.specs['blankLength']
        sd = self.specs['spinDia']
        sl = self.specs['spinLength']
        ca = self.specs['chamferAngle']
        chLen = (bd - sd) / 2 / tan(radians(ca))
        p1, p2, p3, p4, p5, p6 = self._profile.endPoints()
        ll = self.scene().pixelsToScene(Dimension.leaderLen)
        dlg = self.scene().pixelsToScene(Dimension.dimLabelGap)
        # blankDia
        dlbb = self.blankDiaDim.dimText.sceneBoundingRect()
        a1bb = self.blankDiaDim.arrow1.sceneBoundingRect()
        lx = bl + dlbb.width() / 2 + dlg
        ly = 0
        outside = False
        if a1bb.height() * 2 + dlbb.height() + dlg > bd:
            outside = True
            ly = -bd / 2 - ll - dlbb.height() / 2
        self.blankDiaDim.config({'value': bd,
                                 'ref1': QPointF(*p5),
                                 'ref2': QPointF(QPointF(p5[0], -p5[1])),
                                 'outside': outside,
                                 'format': FMTDIN,
                                 'pos': QPointF(lx, ly),
                                 'force': 'vertical'})
        # spinLength
        dlbb = self.spinLengthDim.dimText.sceneBoundingRect()
        a1bb = self.spinLengthDim.arrow1.sceneBoundingRect()
        lx = sl / 2
        ly = bd / 2 + dlbb.height() / 2 + dlg # blank dia not spin dia
        outside = False
        if a1bb.width() * 2 + dlbb.width() + dlg > sl:
            outside = True
            lx = -dlbb.width() / 2 - ll
        ref1 = QPointF(*p1)
        if p1[0] == p2[0]:
            ref1 = QPointF(*p2)
        self.spinLengthDim.config({'value': sl,
                                   'ref1': ref1,
                                   'ref2': QPointF(*p3),
                                   'outside': outside,
                                   'format': FMTIN,
                                   'pos': QPointF(lx, ly),
                                   'force': 'horizontal'})
        # blankLength
        dlbb = self.blankLengthDim.dimText.sceneBoundingRect()
        a1bb = self.blankLengthDim.arrow1.sceneBoundingRect()
        lx = bl / 2
        ly = bd / 2 + dlbb.height() * 2.0 + dlg
        outside = False
        if a1bb.width() * 2 + dlbb.width() + dlg > bl:
            outside = True
            lx = -dlbb.width() / 2 - ll
        self.blankLengthDim.config({'value': bl,
                                    'ref1': ref1,
                                    'ref2': QPointF(*p5),
                                    'outside': outside,
                                    'format': FMTIN,
                                    'pos': QPointF(lx, ly),
                                    'force': 'horizontal'})
        # spinDia
        dlbb = self.spinDiaDim.dimText.sceneBoundingRect()
        a1bb = self.spinDiaDim.arrow1.sceneBoundingRect()
        lx = sl * .3
        ly = -bd / 2 - ll - dlbb.height()
        self.spinDiaDim.config({'value': sd,
                                'ref1': QPointF(lx, sd / 2),
                                'ref2': QPointF(lx, -sd / 2),
                                'outside': True, # always outside
                                'format': FMTDIN,
                                'pos': QPointF(lx, ly),
                                'force': 'vertical'})
        # chamferAngle
        dlbb = self.chamferAngleDim.dimText.sceneBoundingRect()
        a1bb = self.chamferAngleDim.arrow1.sceneBoundingRect()
        lx = p4[0] - dlbb.width() - a1bb.width()
        ly = -bd - dlbb.height()
        outside = True
        self.chamferAngleDim.config({'value': ca,
                                     'pos': QPointF(lx, ly),
                                     'line1': QLineF(p4[0], -p4[1], p5[0],
                                                     -p5[1]),
                                     'line2': QLineF(p3[0], -p3[1], p4[0],
                                                     -p4[1]),
                                     'outside': outside,
                                     'format': FMTANG,
                                     'quadV': QVector2D(1, -1)})

class TTSpindownDef2(TTSpindownDef):
    """A tool where a tip/dia/shoulder/bevel is ground.

    This adds a tip angle dimension to TTSpindownDef.

    specs:
      blankDia
      blankLength
      spinDia
      spinLength
      tipAngle
      chamferAngle
    """
    def __init__(self, specs={'blankDia': .5,
                              'blankLength': 3.,
                              'spinDia': .375,
                              'spinLength': 1.,
                              'tipAngle': 118,
                              'chamferAngle': 45.}):
        super().__init__(specs)
        self.tipAngleDim = AngleDim('tipAngle')
    def paint(self, painter, option, widget):
        """Fill the ground section of the profile in a different color.
        """
        super(TTToolDef, self).paint(painter, option, widget)
        br = self.specs['blankDia'] / 2
        sr = self.specs['spinDia'] / 2
        sl = self.specs['spinLength']
        ta = self.specs['tipAngle']
        ca = self.specs['chamferAngle']
        tipLen = tipLength(ta, sr * 2)
        pp = QPainterPath()
        pp.moveTo(0, 0)
        pp.lineTo(tipLen, -sr)
        pp.lineTo(tipLen, sr)
        pp.lineTo(0, 0)
        painter.fillPath(pp, self.grindBrush)
        painter.setBrush(qt.NoBrush)
        painter.drawPath(pp)
        r = QRectF(tipLen, sr, sl - tipLen, -sr * 2)
        painter.fillRect(r, self.grindBrush)
        painter.setBrush(qt.NoBrush)
        painter.drawRect(r)
        if ca < 90.0:
            chLen = (br - sr) / tan(radians(ca))
            pp = QPainterPath()
            pp.moveTo(sl, sr)
            pp.lineTo(sl, -sr)
            pp.lineTo(sl + chLen, -br)
            pp.lineTo(sl + chLen, br)
            pp.lineTo(sl, sr)
            painter.fillPath(pp, self.grindBrush)
            painter.setBrush(qt.NoBrush)
            painter.drawPath(pp)
    def sceneChange(self, scene):
        super().sceneChange(scene)
        if scene:
            scene.addItem(self.tipAngleDim)
            self.tipAngleDim.show()
        else:
            self.scene().removeItem(self.tipAngleDim)
            self.tipAngleDim.hide()
    def checkGeometry(self, specs={}):
        if not super().checkGeometry(specs):
            return False
        d = copy(self.specs)
        d.update(specs)
        sd = d['spinDia']
        sl = d['spinLength']
        ta = d['tipAngle']
        tipLen = tipLength(ta, sd)
        # all > 0.0?
        if any(map(lambda x : x <= 0, d.values())):
            return False
        return tipLen < sl and ta < 180.0
    def _updateProfile(self):
        br = self.specs['blankDia'] / 2.0
        bl = self.specs['blankLength']
        sr = self.specs['spinDia'] / 2.0
        sl = self.specs['spinLength']
        ta = self.specs['tipAngle']
        ca = self.specs['chamferAngle']
        tipLen = 0.0
        if ta < 180.0:
            tipLen = tipLength(ta, sr * 2)
        chLen = 0.0
        if ca < 90.0:
            chLen = (br - sr) / tan(radians(ca))
        p2d = Path2d([0, 0])
        if tipLen == 0:
            p2d.lineTo(0, sr)
        else:
            p2d.lineTo(tipLen, sr)
        p2d.lineTo(sl, sr)
        # to chamfer or not to chamfer, that is the question
        if chLen == 0.0:
            p2d.lineTo(sl, br)
        else:
            p2d.lineTo(sl + chLen, br)
        p2d.lineTo(bl, br)
        p2d.lineTo(bl, 0)
        self._profile = p2d
        pp = p2d.toQPainterPath()
        pp.addPath(mirTx.map(pp))
        if tipLen != 0.0:
            pp.moveTo(tipLen, sr)
            pp.lineTo(tipLen, -sr)
        pp.moveTo(sl, sr)
        pp.lineTo(sl, -sr)
        if chLen != 0.0:
            pp.moveTo(sl + chLen, br)
            pp.lineTo(sl + chLen, -br)
        self.setPath(pp)
    def _updateDims(self):
        super()._updateDims()
        bd = self.specs['blankDia']
        ta = self.specs['tipAngle']
        p1, p2, p3, p4, p5, p6 = self._profile.endPoints()
        ll = self.scene().pixelsToScene(Dimension.leaderLen)
        dlg = self.scene().pixelsToScene(Dimension.dimLabelGap)
        # tipAngle
        dlbb = self.tipAngleDim.dimText.sceneBoundingRect()
        a1bb = self.tipAngleDim.arrow1.sceneBoundingRect()
        lx = -bd / 2.0
        ly = 0
        outside = False
        # angle required to fit the label inside the lines
        v1 = QVector2D(-bd, dlbb.height() / 2 + a1bb.height())
        v2 = QVector2D(-bd, -dlbb.height() / 2 - a1bb.height())
        try:
            loa = degrees(acos(QVector2D.dotProduct(v1, v2)))
            if a < loa:
                outside = True
        except:
            pass
        self.tipAngleDim.config({'value': ta,
                                 'pos': QPointF(lx, ly),
                                 'line1': QLineF(p1[0], p1[1], p2[0], p2[1]),
                                 'line2': QLineF(p1[0], p1[1], p2[0], -p2[1]),
                                 'outside': outside,
                                 'format': FMTANG,
                                 'quadV': QVector2D(-1, 0)})

class TTTaperDef(TTToolDef):
    """A tool with a single ground tapered diameter.
    specs:
        blankDia
        blankLength
        tipDia
        includedAngle
    """
    def __init__(self, specs={'blankDia': .5,
                              'blankLength': 3,
                              'tipDia': .25,
                              'includedAngle': 7}):
        super().__init__(specs)
        self.blankDiaDim = LinearDim('blankDia')
        self.blankLengthDim = LinearDim('blankLength')
        self.tipDiaDim = LinearDim('tipDia')
        self.includedAngleDim = AngleDim('includedAngle')
    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        p1, p2, p3, p4, p5, *rest = self._profile.endPoints()
        pp = QPainterPath()
        pp.moveTo(*p2)
        pp.lineTo(p2[0], -p2[1])
        pp.lineTo(p3[0], -p3[1])
        pp.lineTo(p3[0], p3[1])
        pp.lineTo(*p2)
        painter.fillPath(pp, self.grindBrush)
        painter.setBrush(qt.NoBrush)
        painter.drawPath(pp)
    def sceneChange(self, scene):
        super().sceneChange(scene)
        if scene:
            scene.addItem(self.blankDiaDim)
            self.blankDiaDim.show()
            scene.addItem(self.blankLengthDim)
            self.blankLengthDim.show()
            scene.addItem(self.tipDiaDim)
            self.tipDiaDim.show()
            scene.addItem(self.includedAngleDim)
            self.includedAngleDim.show()
        else:
            self.scene().removeItem(self.blankDiaDim)
            self.blankDiaDim.hide()
            self.scene().removeItem(self.blankLengthDim)
            self.blankLengthDim.hide()
            self.scene().removeItem(self.tipDiaDim)
            self.tipDiaDim.hide()
            self.scene().removeItem(self.includedAngleDim)
            self.includedAngleDim.hide()
    def checkGeometry(self, specs={}):
        d = copy(self.specs)
        d.update(specs)
        # all > 0.0?
        if any(map(lambda x : x <= 0, d.values())):
            return False
        bd = d['blankDia']
        bl = d['blankLength']
        td = d['tipDia']
        ia = d['includedAngle']
        dx = (bd - td) / 2 / tan(radians(ia / 2))
        return td < bd and dx < bl and ia < 180
    def _updateProfile(self):
        br = self.specs['blankDia'] / 2
        bl = self.specs['blankLength']
        tr = self.specs['tipDia'] / 2
        ia = self.specs['includedAngle']
        p2d = Path2d([0, 0])
        p2d.lineTo(0, tr)
        dx = (br - tr) / tan(radians(ia / 2.0))
        p2d.lineTo(dx, br)
        p2d.lineTo(bl, br)
        p2d.lineTo(bl, 0)
        self._profile = p2d
        pp = p2d.toQPainterPath()
        pp.addPath(mirTx.map(pp))
        pp.moveTo(dx, br)
        pp.lineTo(dx, -br)
        self.setPath(pp)
    def _updateDims(self):
        bd = self.specs['blankDia']
        bl = self.specs['blankLength']
        td = self.specs['tipDia']
        ia = self.specs['includedAngle']
        p1, p2, p3, p4, p5 = self._profile.endPoints()
        ll = self.scene().pixelsToScene(Dimension.leaderLen)
        dlg = self.scene().pixelsToScene(Dimension.dimLabelGap)
        # blankDia
        dlbb = self.blankDiaDim.dimText.sceneBoundingRect()
        a1bb = self.blankDiaDim.arrow1.sceneBoundingRect()
        lx = bl + dlbb.width() / 2 + dlg
        ly = 0
        outside = False
        if a1bb.height() * 2 + dlbb.height() + dlg > bd:
            outside = True
            ly = -bd / 2 - ll - dlbb.height() / 2
        self.blankDiaDim.config({'value': bd,
                                 'ref1': QPointF(*p4),
                                 'ref2': QPointF(QPointF(p4[0], -p4[1])),
                                 'outside': outside,
                                 'format': FMTDIN,
                                 'pos': QPointF(lx, ly),
                                 'force': 'vertical'})
        # blankLength
        dlbb = self.blankLengthDim.dimText.sceneBoundingRect()
        a1bb = self.blankLengthDim.arrow1.sceneBoundingRect()
        lx = bl / 2
        ly = bd / 2 + dlbb.height() / 2 + dlg
        outside = False
        if a1bb.width() * 2 + dlbb.width() + dlg > bl:
            outside = True
            lx = -dlbb.width() / 2 - ll
        self.blankLengthDim.config({'value': bl,
                                    'ref1': QPointF(*p2),
                                    'ref2': QPointF(*p4),
                                    'outside': outside,
                                    'format': FMTIN,
                                    'pos': QPointF(lx, ly),
                                    'force': 'horizontal'})
        # tipDia
        dlbb = self.tipDiaDim.dimText.sceneBoundingRect()
        a1bb = self.tipDiaDim.arrow1.sceneBoundingRect()
        lx = -dlbb.width() / 2 - dlg
        ly = 0
        outside = False
        if a1bb.height() * 2 + dlbb.height() + dlg > td:
            outside = True
            ly = -td / 2 - ll - dlbb.height() / 2
        self.tipDiaDim.config({'value': td,
                               'ref1': QPointF(*p2),
                               'ref2': QPointF(QPointF(p2[0], -p2[1])),
                               'outside': outside,
                               'format': FMTDIN,
                               'pos': QPointF(lx, ly),
                               'force': 'vertical'})
        # includedAngle
        dlbb = self.includedAngleDim.dimText.sceneBoundingRect()
        a1bb = self.includedAngleDim.arrow1.sceneBoundingRect()
        lx = p3[0] * 1.25
        ly = -bd
        outside = True
        self.includedAngleDim.config({'value': ia,
                                      'pos': QPointF(lx, ly),
                                      'line1': QLineF(p2[0], p2[1], p3[0],
                                                      p3[1]),
                                      'line2': QLineF(p2[0], -p2[1], p3[0],
                                                      -p3[1]),
                                      'outside': outside,
                                      'format': FMTANG,
                                      'quadV': QVector2D(1, 0)})

class TTTaperDef2(TTTaperDef):
    """A tapered tool with an optional bevel at the shank.

    Adds a taper length and bevel angle to the TTTaperDef.
    
    specs:
        blankDia
        blankLength
        tipDia
        includedAngle
        taperLength
        chamferAngle
    """
    def __init__(self, specs={'blankDia': .25,
                              'blankLength': 2,
                              'tipDia': .125,
                              'includedAngle': 7,
                              'taperLength': .5,
                              'chamferAngle': 30}):
        super().__init__(specs)
        self.taperLengthDim = LinearDim('taperLength')
        self.chamferAngleDim = AngleDim('chamferAngle')
    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        br = self.specs['blankDia'] / 2.0
        tr = self.specs['tipDia'] / 2.0
        tl = self.specs['taperLength']
        ia = self.specs['includedAngle']
        ca = self.specs['chamferAngle']
        if ca < 90.0:
            taperBigEndRad = tl * tan(radians(ia / 2)) + tr
            chLen = (br - taperBigEndRad) / tan(radians(ca))
            pp = QPainterPath()
            pp.moveTo(tl, taperBigEndRad)
            pp.lineTo(tl, -taperBigEndRad)
            pp.lineTo(tl + chLen, -br)
            pp.lineTo(tl + chLen, br)
            pp.lineTo(tl, taperBigEndRad)
            painter.fillPath(pp, self.grindBrush)
            painter.setBrush(qt.NoBrush)
            painter.drawPath(pp)
    def sceneChange(self, scene):
        super().sceneChange(scene)
        if scene:
            scene.addItem(self.taperLengthDim)
            self.taperLengthDim.show()
            scene.addItem(self.chamferAngleDim)
            self.chamferAngleDim.show()
        else:
            self.scene().removeItem(self.taperLengthDim)
            self.taperLengthDim.hide()
            self.scene().removeItem(self.chamferAngleDim)
            self.chamferAngleDim.hide()
    def checkGeometry(self, specs={}):
        d = copy(self.specs)
        d.update(specs)
        # all > 0.0?
        if any(map(lambda x : x <= 0, d.values())):
            return False
        bd = d['blankDia']
        bl = d['blankLength']
        td = d['tipDia']
        ia = d['includedAngle']
        tl = d['taperLength']
        ca = d['chamferAngle']
        if ca > 90.0:
            return False
        taperBigEndDia = tl * tan(radians(ia / 2)) * 2 + td
        if taperBigEndDia >= bd:
            return False
        chLen = (bd - taperBigEndDia) / 2 / tan(radians(ca))        
        return (td < bd and tl < bl and ia < 180 and tl + chLen < bl) 
    def _updateProfile(self):
        br = self.specs['blankDia'] / 2
        bl = self.specs['blankLength']
        tr = self.specs['tipDia'] / 2
        ia = self.specs['includedAngle']
        tl = self.specs['taperLength']
        ca = self.specs['chamferAngle']
        taperBigEndRad = tl * tan(radians(ia / 2)) + tr
        p2d = Path2d([0, 0])
        p2d.lineTo(0, tr)
        p2d.lineTo(tl, taperBigEndRad)
        if ca < 90.0:
            chLen = (br - taperBigEndRad) / tan(radians(ca))
            p2d.lineTo(tl + chLen, br)
        else:
            p2d.lineTo(tl, br)
        p2d.lineTo(bl, br)
        p2d.lineTo(bl, 0)
        self._profile = p2d
        pp = p2d.toQPainterPath()
        pp.addPath(mirTx.map(pp))
        pp.moveTo(tl, taperBigEndRad)
        pp.lineTo(tl, -taperBigEndRad)
        self.setPath(pp)
    def _updateDims(self):
        bd = self.specs['blankDia']
        bl = self.specs['blankLength']
        td = self.specs['tipDia']
        ia = self.specs['includedAngle']
        tl = self.specs['taperLength']
        ca = self.specs['chamferAngle']
        p1, p2, p3, p4, p5, p6 = self._profile.endPoints()
        ll = self.scene().pixelsToScene(Dimension.leaderLen)
        dlg = self.scene().pixelsToScene(Dimension.dimLabelGap)
        # blankDia
        dlbb = self.blankDiaDim.dimText.sceneBoundingRect()
        a1bb = self.blankDiaDim.arrow1.sceneBoundingRect()
        lx = bl + dlbb.width() / 2 + dlg
        ly = 0
        outside = False
        if a1bb.height() * 2 + dlbb.height() + dlg > bd:
            outside = True
            ly = -bd / 2 - ll - dlbb.height() / 2
        self.blankDiaDim.config({'value': bd,
                                 'ref1': QPointF(*p5),
                                 'ref2': QPointF(QPointF(p5[0], -p5[1])),
                                 'outside': outside,
                                 'format': FMTDIN,
                                 'pos': QPointF(lx, ly),
                                 'force': 'vertical'})
        # taperLength
        dlbb = self.taperLengthDim.dimText.sceneBoundingRect()
        a1bb = self.taperLengthDim.arrow1.sceneBoundingRect()
        lx = tl / 2
        ly = bd / 2 + dlbb.height() / 2 + dlg
        outside = False
        if a1bb.width() * 2 + dlbb.width() + dlg > tl:
            outside = True
            lx = -dlbb.width() / 2 - ll
        ref2p = p4 if ca == 90.0 else p3
        self.taperLengthDim.config({'value': tl,
                                    'ref1': QPointF(p2[0], p2[1]),
                                    'ref2': QPointF(ref2p[0], ref2p[1]),
                                    'outside': outside,
                                    'format': FMTIN,
                                    'pos': QPointF(lx, ly),
                                    'force': 'horizontal'})
        # blankLength
        dlbb = self.blankLengthDim.dimText.sceneBoundingRect()
        a1bb = self.blankLengthDim.arrow1.sceneBoundingRect()
        lx = bl / 2
        ly = ly + dlbb.height() + dlg
        outside = False
        if a1bb.width() * 2 + dlbb.width() + dlg > bl:
            outside = True
            lx = -dlbb.width() / 2 - ll
        self.blankLengthDim.config({'value': bl,
                                    'ref1': QPointF(*p2),
                                    'ref2': QPointF(*p5),
                                    'outside': outside,
                                    'format': FMTIN,
                                    'pos': QPointF(lx, ly),
                                    'force': 'horizontal'})
        # tipDia
        dlbb = self.tipDiaDim.dimText.sceneBoundingRect()
        a1bb = self.tipDiaDim.arrow1.sceneBoundingRect()
        lx = -dlbb.width() / 2 - dlg
        ly = 0
        outside = False
        if a1bb.height() * 2 + dlbb.height() + dlg > td:
            outside = True
            ly = -td / 2 - ll - dlbb.height() / 2
        self.tipDiaDim.config({'value': td,
                               'ref1': QPointF(*p2),
                               'ref2': QPointF(QPointF(p2[0], -p2[1])),
                               'outside': outside,
                               'format': FMTDIN,
                               'pos': QPointF(lx, ly),
                               'force': 'vertical'})
        # includedAngle
        dlbb = self.includedAngleDim.dimText.sceneBoundingRect()
        a1bb = self.includedAngleDim.arrow1.sceneBoundingRect()
        lx = tl * .3
        ly = -bd / 2 - dlbb.height() - dlg
        outside = True
        self.includedAngleDim.config({'value': ia,
                                      'pos': QPointF(lx, ly),
                                      'line1': QLineF(p2[0], p2[1], p3[0],
                                                      p3[1]),
                                      'line2': QLineF(p2[0], -p2[1], p3[0],
                                                      -p3[1]),
                                      'outside': outside,
                                      'format': FMTANG,
                                      'quadV': QVector2D(1, 0)})
        # chamferAngle
        dlbb = self.chamferAngleDim.dimText.sceneBoundingRect()
        a1bb = self.chamferAngleDim.arrow1.sceneBoundingRect()
        lx = p4[0] - dlbb.width() - a1bb.width()
        ly -= dlbb.height()
        outside = True
        self.chamferAngleDim.config({'value': ca,
                                     'pos': QPointF(lx, ly),
                                     'line1': QLineF(p4[0], -p4[1], p5[0],
                                                     -p5[1]),
                                     'line2': QLineF(p3[0], -p3[1], p4[0],
                                                     -p4[1]),
                                     'outside': outside,
                                     'format': FMTANG,
                                     'quadV': QVector2D(1, -1)})

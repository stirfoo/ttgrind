# ttwidget.py
# S. Edward Dolan
# Saturday, December 28 2024

import pprint
# from itertools import pairwise # needs v3.10
from math import ceil, tan, radians

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt as qt

from algo import tipLength
from ttscene import TTScene
from floatedit import FloatEdit
from tttooldef import (TTNeckDef, TTPointDef, TTTaperDef, TTTaperDef2,
                       TTSpindownDef, TTSpindownDef2)
from tttoolview import TTToolView
from ttwriter import TTWriter, mergeDicts
from ttpathgen import getPlungePoints
from simview import SimView

# .------------------------------------------------------------------------.
# |      Grind Type | Point |v|  Plunge Feed ___________    |   Simulate  ||
# |     Wheel Width ___________   Seg 1 Feed ___________    ----[]-------- |
# | Wheel Overlap % ___________   Seg 2 Feed ___________                   |
# |      Back Taper ___________   Seg 3 Feed ___________    |Write Program||
# |.----------------------------------------------------------------------.|
# ||                                                                      ||
# ||                               TTToolView                             ||
# ||                                                                      ||
# |'----------------------------------------------------------------------'|
# '------------------------------------------------------------------------'
class TTWidget(QWidget):
    defaultWheelWidth = 0.25
    defaultWheelOverlap = 0.9   # 90%
    # The simulator will generate a program that will leave this much in 
    # Y, per-side, for better simulation.
    simY = .0003
    maxPlungeFeed = 1.0
    def __init__(self, parent):
        super(TTWidget, self).__init__(parent)
        # which selected combo indexes (grind type) is the back taper widget
        # valid?
        self.backTaperMap = {
            0: False, # point
            1: False, # neck
            2: True,  # spin down 1
            3: True,  # spin down 2
            4: False, # taper 1
            5: False  # taper 2
        }
        # which segment feedrates are visible for a given grind type
        self.segFeedMap = {
            0: [True, False, False],
            1: [True, True, False],
            2: [True, True, False],
            3: [True, True, True],
            4: [True, False, False],
            5: [True, True, False]
        }
        self.grid = QGridLayout(self)
        # Grind Type 
        lbl = QLabel("Grind Type")
        lbl.setAlignment(qt.AlignRight | qt.AlignCenter)
        self.grid.addWidget(lbl, 1, 1, 1, 1)
        self.cboGrindType = QComboBox(self);
        self.cboGrindType.addItem("Point")
        self.cboGrindType.addItem("Neck")
        self.cboGrindType.addItem("Spindown 1")
        self.cboGrindType.addItem("Spindown 2")
        self.cboGrindType.addItem("Taper 1")
        self.cboGrindType.addItem("Taper 2")
        self.grid.addWidget(self.cboGrindType, 1, 2, 1, 1)
        self.cboGrindType.currentIndexChanged.connect(self.onGrindTypeChanged)
        # Wheel Width
        lbl = QLabel("Wheel Width", self)
        lbl.setAlignment(qt.AlignRight | qt.AlignCenter)
        self.grid.addWidget(lbl, 2, 1, 1, 1)
        self.txtWheelWid = FloatEdit(self.defaultWheelWidth, self, False,
                                     False, .03, 1)
        self.grid.addWidget(self.txtWheelWid, 2, 2, 1, 1)
        # Wheel Overlap %
        lbl = QLabel("Wheel Overlap %", self)
        lbl.setAlignment(qt.AlignRight | qt.AlignCenter)
        self.grid.addWidget(lbl, 3, 1, 1, 1)
        self.txtWheelOverlap = FloatEdit(self.defaultWheelOverlap * 100,
                                         self, False, False, 1, 100)
        self.grid.addWidget(self.txtWheelOverlap, 3, 2, 1, 1)
        # Back Taper
        self.lblBackTaper = QLabel("Back Taper", self)
        self.lblBackTaper.setAlignment(qt.AlignRight | qt.AlignCenter)
        self.grid.addWidget(self.lblBackTaper, 4, 1, 1, 1)
        self.txtBackTaper = FloatEdit(.0005, self, True, False, 0, .002)
        self.grid.addWidget(self.txtBackTaper, 4, 2, 1, 1)
        #
        # Plunge Feed
        lbl = QLabel("Plunge Feed", self)
        lbl.setAlignment(qt.AlignRight | qt.AlignCenter)
        self.grid.addWidget(lbl, 1, 3, 1, 1)
        self.txtPlungeFeed = FloatEdit(0.05, self, False, False,
                                       minValue=.01,
                                       maxValue=self.maxPlungeFeed)
        self.grid.addWidget(self.txtPlungeFeed, 1, 4, 1, 1)
        # Seg1 Feed
        self.lblSeg1Feed = QLabel("Seg 1 Feed", self)
        self.lblSeg1Feed.setAlignment(qt.AlignRight | qt.AlignCenter)
        self.grid.addWidget(self.lblSeg1Feed, 2, 3, 1, 1)
        self.txtSeg1Feed = FloatEdit(0.05, self, False, False,
                                     minValue=.01, maxValue=5)
        self.grid.addWidget(self.txtSeg1Feed, 2, 4, 1, 1)
        # seg 2 Feed
        self.lblSeg2Feed = QLabel("Seg 2 Feed", self)
        self.lblSeg2Feed.setAlignment(qt.AlignRight | qt.AlignCenter)
        self.grid.addWidget(self.lblSeg2Feed, 3, 3, 1, 1)
        self.txtSeg2Feed = FloatEdit(0.05, self, False, False,
                                     minValue=.01, maxValue=5)
        self.grid.addWidget(self.txtSeg2Feed, 3, 4, 1, 1)
        # seg 3 Feed
        self.lblSeg3Feed = QLabel("Seg 3 Feed", self)
        self.lblSeg3Feed.setAlignment(qt.AlignRight | qt.AlignCenter)
        self.grid.addWidget(self.lblSeg3Feed, 4, 3, 1, 1)
        self.txtSeg3Feed = FloatEdit(0.05, self, False, False,
                                     minValue=.01, maxValue=5)
        self.grid.addWidget(self.txtSeg3Feed, 4, 4, 1, 1)
        # 
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                              QSizePolicy.Minimum)
        self.grid.addItem(spacer, 4, 5, 1, 1)
        # Simulate
        self.butSimulate = QPushButton("Simulate", self)
        self.butSimulate.setCheckable(True)
        self.butSimulate.toggled.connect(self.onSimulate)
        self.grid.addWidget(self.butSimulate, 1, 6, 1, 1)
        # Sumulation Feed
        self.sldSimSpeed = QSlider(qt.Horizontal, self)
        self.sldSimSpeed.setSizePolicy(QSizePolicy.Minimum,
                                       QSizePolicy.Preferred)
        self.sldSimSpeed.setMinimum(0)
        self.sldSimSpeed.setMaximum(100)
        self.grid.addWidget(self.sldSimSpeed, 2, 6, 1, 1)
        # Write Program
        self.butWrite = QPushButton("Write Program", self)
        self.butWrite.clicked.connect(self.onWriteProgram)
        self.grid.addWidget(self.butWrite, 4, 6, 1, 1)
        #
        self.scene = TTScene()
        self.toolView = TTToolView(self.scene, self)
        self.grid.addWidget(self.toolView, 5, 1, 1, 6)
        # 
        self.pointDef = TTPointDef()
        self.neckDef = TTNeckDef()
        self.spindownDef1 = TTSpindownDef()
        self.spindownDef2 = TTSpindownDef2()
        self.taperDef1 = TTTaperDef()
        self.taperDef2 = TTTaperDef2()
        self.onGrindTypeChanged(0)
        #
        self.simScene = TTScene()
        self.simView = SimView(self.simScene, self)
        self.simView.hide()
        self.grid.addWidget(self.simView, 5, 1, 1, 6)
        self.sldSimSpeed.valueChanged.connect(self.simView.onSpeedChanged)
        # 31 will set the animatin multiplier to 1 as currently written
        self.sldSimSpeed.setValue(31)
    def enableBackTaper(self, b):
        self.lblBackTaper.setVisible(b);
        self.txtBackTaper.setVisible(b)
    def enableSeg1Feed(self, b):
        self.lblSeg1Feed.setVisible(b);
        self.txtSeg1Feed.setVisible(b)
    def enableSeg2Feed(self, b):
        self.lblSeg2Feed.setVisible(b);
        self.txtSeg2Feed.setVisible(b)
    def enableSeg3Feed(self, b):
        self.lblSeg3Feed.setVisible(b);
        self.txtSeg3Feed.setVisible(b)
    def enableSegFeeds(self, idx):
        x = self.segFeedMap[idx]
        self.enableSeg1Feed(x[0])
        self.enableSeg2Feed(x[1])
        self.enableSeg3Feed(x[2])
    def onSpeedChanged(self, val):
        print(val)
    def onGrindTypeChanged(self, idx):
        self.grid.invalidate()
        self.enableBackTaper(self.backTaperMap[idx])
        self.enableSegFeeds(idx)        
        if idx == 0:            # Point
            self.toolView.setToolDef(self.pointDef)
        elif idx == 1:          # Neck
            self.toolView.setToolDef(self.neckDef)
        elif idx == 2:          # Spindown 1
            self.toolView.setToolDef(self.spindownDef1)
        elif idx == 3:          # Spindown 2
            self.toolView.setToolDef(self.spindownDef2)
        elif idx == 4:          # Taper 1
            self.toolView.setToolDef(self.taperDef1)
        elif idx == 5:          # Taper 2
            self.toolView.setToolDef(self.taperDef2)
    def getGrindSpecs(self):
        if not self.txtWheelWid.isValid():
            QMessageBox.critical(self, "TTGrind",
                                 "The wheel width value is not valid.")
            return None
        if not self.txtWheelOverlap.isValid():
            QMessageBox.critical(self, "TTGrind",
                                 "The wheel overlap % value is not valid.")
            return None
        specs = {
            'wheelWidth': self.txtWheelWid.value(),
            'wheelOverlap': self.txtWheelOverlap.value() / 100.0,
        }
        if self.lblBackTaper.isEnabled():
            if not self.txtBackTaper.isValid():
                QMessageBox.critical(self, "TTGrind",
                                 "The back taper value is not valid.")
                return None
            else:
                specs['backTaper'] = self.txtBackTaper.value()
        return specs
    def getSimProgram(self):
        return self.onWriteProgram(True)
    def onSimulate(self, checked):
        if checked:
            prog = self.getSimProgram()
            if prog is None:
                return
            self.simView.setProgram(self.getSimProgram())
            l, d = self.toolView.getStockDims()
            self.simView.setStock(l, d)
            self.simView.setWheel(self.txtWheelWid.value(), d * 2)
            for child in self.children():
                if (isinstance(child, QLabel) or
                    isinstance(child, QComboBox) or
                    isinstance(child, FloatEdit) or
                    isinstance(child, QGroupBox) or
                    (isinstance(child, QPushButton) and
                     child != self.butSimulate)):
                    child.setEnabled(False)
            self.toolView.hide()
            self.simView.show()
            self.simView.setFocus()
        else:
            self.simDone()
    def simDone(self):
        self.simView.hide();
        self.toolView.show()
        for child in self.children():
            if (isinstance(child, QLabel) or
                isinstance(child, QComboBox) or
                isinstance(child, FloatEdit) or
                isinstance(child, QGroupBox) or
                (isinstance(child, QPushButton) and
                 child != self.butSimulate)):
                    child.setEnabled(True)
        self.enableBackTaper(self.backTaperMap[self.cboGrindType
                                               .currentIndex()])
        # QMessageBox.information(self, "TTGrind", 'Grind Time: '
        #                         + self.simView.anim.getLastGrindTime())
    def getFeedSpecs(self):
        """Return a map of the current feedrates entered by the user.
        """
        if not (self.txtPlungeFeed.isValid() and
                self.txtSeg1Feed.isValid() and
                self.txtSeg2Feed.isValid() and
                self.txtSeg3Feed.isValid()):
            return None
        return {
            'plungeFeed': self.txtPlungeFeed.value(),
            'seg1Feed': self.txtSeg1Feed.value(),
            'seg2Feed': self.txtSeg2Feed.value(),
            'seg3Feed': self.txtSeg3Feed.value()
        }
    def onWriteProgram(self, forSim=False):
        """Write the TT XML file.

        forSim -- True if a simulation program should be generated

        Return the generated sim prog if forSim is True, else return None.
        """
        grindSpecs = self.getGrindSpecs()
        if grindSpecs is None:
            return
        feedSpecs = self.getFeedSpecs()
        if feedSpecs is None:
            return 
        specs = mergeDicts(mergeDicts(self.toolView.getToolSpecs(),
                                      grindSpecs),
                           feedSpecs)
        idx = self.cboGrindType.currentIndex()
        if idx == 0:
            return self.writePointProg(specs, forSim)
        elif idx == 1:
            return self.writeNeckProg(specs,
                                      self.toolView.getToolProfile(),
                                      forSim)
        elif idx == 2:
            return self.writeSpindown1Prog(specs,
                                           self.toolView.getToolProfile(),
                                           forSim)
        elif idx == 3:
            return self.writeSpindown2Prog(specs,
                                           self.toolView.getToolProfile(),
                                           forSim)
        elif idx == 4:
            return self.writeTaper1Prog(specs,
                                        self.toolView.getToolProfile(),
                                        forSim)
        elif idx == 5:
            return self.writeTaper2Prog(specs,
                                        self.toolView.getToolProfile(),
                                        forSim)
        else:
            QMessageBox.information(self, "TTGrind", "Not yet implemented!")
    def writePointProg(self, specs, forSim=False):
        bd = specs['blankDia']
        ta = specs['tipAngle']
        ww = specs['wheelWidth']
        wo = specs['wheelOverlap']
        tl = tipLength(ta, bd)
        n = ceil(tl / (ww * wo)) # number of passes (1 or more)
        dz = tl / n              # z shift per rough pass
        a = ta / 2               # angle for `Angle' move
        z = dz                   # current z position
        ttw = TTWriter()
        ttw.rollerOn()
        if n == 1:
            ttw.rapidIn({'RAPID_IN_TO': z})
        else:
            ttw.rapidIn({'RAPID_IN_TO': z,
                         'AXIS2_BACKLASH': 0})
        for i in range(n - 1):
            # plunge rough passes
            dy = (tl - z) * tan(radians(a))
            ttw.axisOne({'PLUNGE_TO':
                         dy - (self.simY if forSim else 0),
                         'VELOCITY_AXIS1': specs['plungeFeed']})
            z = dz * (i + 2)
            bl = 0 if i < n - 1 else TTWriter.DEFAULT_AXIS_2_BACKLASH
            ttw.rapidIn({'RAPID_IN_TO': z,
                         'AXIS2_BACKLASH': bl})
        # finish pass
        ttw.angle({'ANGLE': a,
                   'TAPER_DOWN_TO': bd / 2 + .01, # .01 passed tip in Y
                   'TAPER_VELOCITY': specs['seg1Feed']})
        ttw.rollerOff()
        if forSim:
            return ttw.getSimProgram(bd)
        else:
            ttw.write()
            QMessageBox.information(self, "TTGrind", "Write OK!")
    def writeNeckProg(self, specs, elements, forSim=False):
        cl = specs['cutLength']
        nl = specs['neckLength']
        nw = nl - cl
        ww = specs['wheelWidth']
        if nw < ww:
            QMessageBox.critical(self, "TTGrind", "The wheel is too wide for"
                                 " the neck.")
            return
        plungePts, te = getPlungePoints(specs, elements, 5, cl + ww)
        ttw = TTWriter()
        ttw.rollerOn()
        # If plungePts is empty, the current wheel width may grind the entire
        # profile in a single pass.
        if plungePts:
            for pp in plungePts:
                ttw.rapidIn({'RAPID_IN_TO': pp[0], 'AXIS2_BACKLASH': 0})
                ttw.axisOne({'PLUNGE_TO': pp[1] - (self.simY
                                                   if forSim
                                                   else 0),
                             'VELOCITY_AXIS1': specs['plungeFeed']})
        # finish pass
        bd = specs['blankDia']
        nd = specs['neckDia']
        ca = specs['chamferAngle']
        chLen = (bd - nd) / 2 / tan(radians(ca)) if ca < 90 else 0
        ttw.rapidIn({'RAPID_IN_TO': nl + chLen})
        if chLen:
            ttw.angle({'ANGLE': ca,
                       'TAPER_DOWN_TO': (bd - nd) / 2,
                       'TAPER_VELOCITY': specs['seg1Feed']})
        else:
            ttw.axisOne({'PLUNGE_TO': (bd - nd) / 2,
                         'RETURN_TO_NEG': False,
                         'VELOCITY_AXIS1': specs['seg1Feed']})
        ttw.axisTwoOut({'MOVE_OUT_TO': cl + ww,
                        'VELOCITY_AXIS2': specs['seg2Feed']})
        ttw.axisOne({'PLUNGE_TO': 0,
                     'VELOCITY_AXIS1': 15,
                     'RETURN_TO_NEG': True})
        ttw.rollerOff()
        if forSim:
            return ttw.getSimProgram(bd)
        else:
            ttw.write()
            QMessageBox.information(self, "TTGrind", "Write OK!")
    def writeSpindown1Prog(self, specs, elements, forSim=False):
        plungePts, te = getPlungePoints(specs, elements, 3)
        ttw = TTWriter()
        ttw.rollerOn()
        # If plungePts is empty, the current wheel width may grind the entire
        # profile in a single pass.
        if plungePts:
            for pp in plungePts:
                ttw.rapidIn({'RAPID_IN_TO': pp[0], 'AXIS2_BACKLASH': 0})
                ttw.axisOne({'PLUNGE_TO': pp[1] - (self.simY
                                                   if forSim
                                                   else 0),
                             'VELOCITY_AXIS1': specs['plungeFeed']})
        # finish pass
        ttw.rapidIn({'RAPID_IN_TO': elements[3][0]}) # with backlash comp
        if specs['chamferAngle'] < 90:
            ttw.angle({'ANGLE': specs['chamferAngle'],
                       'TAPER_DOWN_TO': te[1][1] + specs['backTaper'],
                       'TAPER_VELOCITY': specs['seg1Feed']})
        else:
            ttw.axisOne({'PLUNGE_TO': te[1][1] + specs['backTaper'],
                         'RETURN_TO_NEG': False,
                         'VELOCITY_AXIS1': specs['seg1Feed']})
        ttw.backTaper({'TAPER_UP_TO': te[1][1],
                       'TAPER_OUT_TO': te[1][0],
                       'TAPER_VELOCITY': specs['seg2Feed']})
        ttw.rollerOff()
        if forSim:
            return ttw.getSimProgram(specs['blankDia'])
        else:
            ttw.write()
            QMessageBox.information(self, "TTGrind", "Write OK!")
    def writeSpindown2Prog(self, specs, elements, forSim=False):
        plungePts, te = getPlungePoints(specs, elements, 3)
        ttw = TTWriter()
        ttw.rollerOn()
        # If plungePts is empty, the current wheel width may grind the entire
        # profile in a single pass.
        if plungePts:
            for pp in plungePts:
                ttw.rapidIn({'RAPID_IN_TO': pp[0], 'AXIS2_BACKLASH': 0})
                ttw.axisOne({'PLUNGE_TO': pp[1] - (self.simY
                                                   if forSim
                                                   else 0),
                             'VELOCITY_AXIS1': specs['plungeFeed']})
        # finish pass
        ttw.rapidIn({'RAPID_IN_TO': elements[3][0]}) # with backlash comp
        if specs['chamferAngle'] < 90:
            ttw.angle({'ANGLE': specs['chamferAngle'],
                       'TAPER_DOWN_TO': te[1][1] + specs['backTaper'],
                       'TAPER_VELOCITY': specs['seg1Feed']})
        else:
            ttw.axisOne({'PLUNGE_TO': te[1][1] + specs['backTaper'],
                         'RETURN_TO_NEG': False,
                         'VELOCITY_AXIS1': specs['seg1Feed']})
        ttw.backTaper({'TAPER_UP_TO': te[1][1],
                       'TAPER_OUT_TO': te[1][0],
                       'TAPER_VELOCITY': specs['seg2Feed']})
        ttw.angle({'ANGLE': specs['tipAngle'] / 2,
                   'TAPER_DOWN_TO': te[0][1] + .01,
                   'TAPER_VELOCITY': specs['seg3Feed']})
        ttw.rollerOff()
        if forSim:
            return ttw.getSimProgram(specs['blankDia'])
        else:
            ttw.write()
            QMessageBox.information(self, "TTGrind", "Write OK!")
    def writeTaper1Prog(self, specs, elements, forSim=False):
        plungePts, te = getPlungePoints(specs, elements, 2)
        ttw = TTWriter()
        ttw.rollerOn()
        # If plungePts is empty, the current wheel width may grind the entire
        # profile in a single pass.
        if plungePts:
            for pp in plungePts:
                ttw.rapidIn({'RAPID_IN_TO': pp[0], 'AXIS2_BACKLASH': 0})
                ttw.axisOne({'PLUNGE_TO': pp[1] - (self.simY
                                                   if forSim
                                                   else 0),
                             'VELOCITY_AXIS1': specs['plungeFeed']})
        # finish pass
        bd = specs['blankDia']
        td = specs['tipDia']
        ia = specs['includedAngle']
        grindLen = (bd - td) / 2 / tan(radians(ia / 2))
        ttw.rapidIn({'RAPID_IN_TO': grindLen})
        ttw.angle({'ANGLE': ia / 2,
                   'TAPER_DOWN_TO': (bd - td) / 2,
                   'TAPER_VELOCITY': specs['seg1Feed']})
        ttw.rollerOff()
        if forSim:
            return ttw.getSimProgram(bd)
        else:
            ttw.write()
            QMessageBox.information(self, "TTGrind", "Write OK!")
    def writeTaper2Prog(self, specs, elements, forSim=False):
        plungePts, te = getPlungePoints(specs, elements, 3)
        ttw = TTWriter()
        ttw.rollerOn()
        # If plungePts is empty, the current wheel width may grind the entire
        # profile in a single pass.
        if plungePts:
            for pp in plungePts:
                ttw.rapidIn({'RAPID_IN_TO': pp[0], 'AXIS2_BACKLASH': 0})
                ttw.axisOne({'PLUNGE_TO': pp[1] - (self.simY
                                                   if forSim
                                                   else 0),
                             'VELOCITY_AXIS1': specs['plungeFeed']})
        # finish pass
        bd = specs['blankDia']
        td = specs['tipDia']
        ia = specs['includedAngle']
        tl = specs['taperLength']
        ttw.rapidIn({'RAPID_IN_TO': elements[3][0]}) # with backlash comp
        if specs['chamferAngle'] < 90.0:
            ttw.angle({'ANGLE': specs['chamferAngle'],
                       'TAPER_DOWN_TO': te[2][1],
                       'TAPER_VELOCITY': specs['seg1Feed']})
        else:
            ttw.axisOne({'PLUNGE_TO': te[2][1],
                         'RETURN_TO_NEG': False,
                         'TAPER_VELOCITY': specs['seg1Feed']})
        ttw.angle({'ANGLE': ia / 2,
                   'TAPER_DOWN_TO': (bd - td) / 2,
                   'TAPER_VELOCITY': specs['seg2Feed']})
        ttw.rollerOff()
        if forSim:
            return ttw.getSimProgram(bd)
        else:
            ttw.write()
            QMessageBox.information(self, "TTGrind", "Write OK!")
        

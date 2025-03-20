from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt as qt

# from math import *

from arc import Arc

from util import ms2hms

sign = lambda x: (1, -1)[x<0]

class GrindAnim(QObject):
    rapidIPM = 15               # grinder actual max rapid feedrate
    simRapidIPM = 100           # constant simulation feedrate
    simFeedIPM = 30             # constant simulation feedrate
    feedIPM = 1                 # TODO: used by arc simulation
    minSpeedFactor = .1         # 1/10th simFeedIMP
    maxSpeedFactor = 3          # Nx the simFeedIMP
    def __init__(self, parent=None):
        super(GrindAnim, self).__init__()
        self.parent = parent
        self.arcQueue = []
        self.arcType = None      # none for linear moves
        self.radius = None
        self.startPos = None
        self.speedFactor = 1
        self.anim = QPropertyAnimation();
        self.anim.valueChanged.connect(self.valueChanged)
        self.anim.finished.connect(self.segmentFinished)
    def isRunning(self):
        return self.anim.state() == QAbstractAnimation.Running
    def setSpeed(self, val):
        """Change the speed factor used in the simulation.

        val -- an integer in the interval [0, 100]

        Return None.
        """
        self.speedFactor = (self.minSpeedFactor +
                            (self.maxSpeedFactor - self.minSpeedFactor)
                            * (val / 100))
    def linearInterp(self, feed):
        """Set up the timer and anim for a linear move and start the timer.
        """
        self.arcType = None
        vxy = QVector2D(self.endPos - self.startPos)
        vl = vxy.length()
        # time in milliseconds to complete the segment
        realTime = vl / feed * 60000
        if feed == self.rapidIPM:
            # rapid feed is not scalable by the user slider
            simTime = vl / self.simRapidIPM * 60000
        else:
            simTime = vl / self.simFeedIPM * 60000 / self.speedFactor
        QApplication.sendEvent(self.parent,
                               QStatusTipEvent('Grind Time: ' +
                                               ms2hms(self.grindTime)))
        self.grindTime += realTime
        self.anim.setDuration(int(simTime))
        self.anim.setTargetObject(self.wheel)
        self.anim.setPropertyName(b'pos')
        self.anim.setStartValue(self.startPos)
        self.anim.setEndValue(self.endPos)
        self.anim.start()
    def arcInterp(self, arc, feed):
        alen = arc.length()
        ms =  alen / min(feed * 100, self.feedIPM) * 60000
        self.timer.setDuration(ms)
        self.timer.setCurveShape(self.timer.LinearCurve)
        self.anim.clear()
        self.anim.setItem(self.wheel)
        self.anim.setPosAt(0.0, self.startPos)
        t = .05
        while t < 1.0:
            self.anim.setPosAt(t, arc.posAtT(t))
            t += .05
        self.anim.setPosAt(1.0, self.endPos)
        self.timer.start()
    def animateSegment(self):
        def parseArc(block, arcType):
            self.grinding = True
            x = block[arcType]['x']
            y = block[arcType]['y']
            i = block[arcType]['i']
            j = block[arcType]['j']
            f = block[arcType]['f']
            r = sqrt(i*i + j*j)
            cp = QPointF(self.startPos.x() + i, self.startPos.y() + j)
            v1 = QVector2D(-i, -j)
            v2 = QVector2D(QPointF(x, y) - cp)
            arc1 = Arc.fromVectors(v1, v2, r, arcType == 'ccwarc')
            arc1.center(cp)
            self.arcType = arcType
            for arc in Arc.cardinalSlice(arc1):
                self.arcQueue.append((arc, f))
            self.arcQueue.reverse()
            self.nextQueuedArc()
            self.idx += 1
        try:
            block = self.program[self.idx]
        except IndexError:
            # out of blocks
            QApplication.sendEvent(self.parent,
                                   QStatusTipEvent('Grind Time: ' +
                                                   ms2hms(self.grindTime)))
            return
        if 'home' in block:
            x = block['home']['x']
            y = block['home']['y']
            self.grinding = False
            if self.startPos is None:
                self.wheel.show()
                self.startPos = QPointF(x, y)
                self.idx += 1
                self.animateSegment()
            else:
                self.endPos = QPointF(x, y)
                self.linearInterp(self.rapidIPM)
                self.idx += 1
        elif 'go' in block:
            self.grinding = False
            x = block['go']['x']
            y = block['go']['y']
            self.endPos = QPointF(x, y)
            self.linearInterp(self.rapidIPM)
            self.idx += 1
        elif 'line' in block:
            self.grinding = True
            x = block['line']['x']
            y = block['line']['y']
            f = block['line']['f']
            self.endPos = QPointF(x, y)
            self.linearInterp(f)
            self.idx += 1
        elif 'cwarc' in block:
            parseArc(block, 'cwarc')
        elif 'ccwarc' in block:
            parseArc(block, 'ccwarc')
        elif 'dwell' in block:
            n = block['dwell']['n']
            self.idx += 1
    def nextQueuedArc(self):
        arc, f = self.arcQueue.pop()
        self.endPos = arc.endPoint()
        self.lastT = 0
        self.arcInterp(arc, f)
    def collisionCheck(self, wheelPos):
        # not currently implemented
        pass
    def nextLinearMove(self, wheelPos):
        if self.startPos is None:
            return              # hack
        pxy =  wheelPos - self.startPos
        path = self.wheel.smearLinear(self.startPos.x(), self.startPos.y(),
                                      pxy.x(), pxy.y())
        if path:
            self.stock.setPath(self.stock.path().subtracted(path))
    def nextArcMove(self, t):
        if t == 0:
            return
        curPos = self.anim.posAt(t)
        prevPos = self.anim.posAt(self.lastT)
        pxy =  curPos - prevPos
        path = self.wheel.smearLinear(prevPos.x(), prevPos.y(),
                                      pxy.x(), pxy.y())
        self.stock.setPath(self.stock.path().subtracted(path))
        self.lastT = t
    def valueChanged(self, wheelPos):
        # 
        # NOTE: This can update the grind time in the status bar in real time,
        #       but It uses simTime, not realTime found in
        #       self.linearInterp(). I'd need to make realTime a member and
        #       scale it using currentTime() and totalDuration().
        # 
        # self.grindTime += self.anim.currentTime()
        # QApplication.sendEvent(self.parent,
        #                        QStatusTipEvent('Grind Time: ' +
        #                                        ms2hms(self.grindTime)))
        if not self.grinding:
            self.collisionCheck(wheelPos)
        elif self.arcType is None:
            self.nextLinearMove(wheelPos)
        else:
            self.nextArcMove(wheelPos)
    def segmentFinished(self):
        """Called after a program block or arc segment has completed.
        """
        self.startPos = self.endPos
        self.anim.stop()
        self.anim.setCurrentTime(0)
        if self.arcQueue:
            self.nextQueuedArc()
        else:
            self.animateSegment()
    def start(self, stock, wheel, program):
        self.reset()
        self.stock = stock
        self.stock.reset()
        self.wheel = wheel
        self.program = program
        self.animateSegment()
    def reset(self):
        self.grindTime = 0
        self.idx = 0
        self.lastT = 0
        self.startPos = None
        self.anim.stop()
        self.anim.setCurrentTime(0)
        self.arcQueue = []
        self.arcType = None
        QApplication.sendEvent(self.parent, QStatusTipEvent(''))

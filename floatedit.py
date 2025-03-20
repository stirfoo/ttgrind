# floatedit.py
# S. Edward Dolan
# Sunday, December 22 2024

import re
import sys
import math
import itertools

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt as qt

class FloatEditValidator(QValidator):
    """Validate input from a FloatEdit.

    The text is eval'd and checked for an numeric number.
    """
    sandboxFns = {
        'acos': math.acos, 'asin': math.asin, 'atan': math.atan,
        'atan2': math.atan2, 'ceil': math.ceil, 'cos': math.cos,
        'deg': math.degrees, 'e': math.e, 'exp': math.exp, 'fabs': math.fabs,
        'floor': math.floor, 'fmod': math.fmod, 'hypot': math.hypot,
        'log': math.log, 'log10': math.log10, 'modf': math.modf, 'pi': math.pi,
        'pow': math.pow, 'rad': math.radians, 'radians': math.radians,
        'sin': math.sin, 'sqrt': math.sqrt, 'tan': math.tan,
        'trunc': math.trunc
    }
    def __init__(self, parent, allowZero=True, allowNeg=True,
                 minValue=0.0, maxValue=1000.0):
        super(FloatEditValidator, self).__init__(parent)
        self.editBox = parent
        self.result = None
        self.allowZero = allowZero
        self.allowNeg = allowNeg
        self.minValue = minValue
        self.maxValue = maxValue
    def checkAllowZero(self, val):
        if val == 0.0:
            return self.allowZero is True
        return True
    def checkAllowNeg(self, val):
        if val < 0:
            return self.allowNeg is True
        return True
    def checkMinValue(self, val):
        return val >= self.minValue
    def checkMaxValue(self, val):
        return val <= self.maxValue
    def fixup(self, input):
        pass
    def validate(self, text, pos):
        try:
            self.result = eval(str(text), {'__builtins__': None},
                               self.sandboxFns)
        except Exception:
            self.result = None
            self.editBox.setInvalidStyleSheet()
        else:
            if (isinstance(self.result, (int, float))
                and self.checkAllowZero(self.result)
                and self.checkAllowNeg(self.result)
                and self.checkMinValue(self.result)
                and self.checkMaxValue(self.result)):
                self.editBox.setValidStyleSheet()
            else:
                self.result = None
                self.editBox.setInvalidStyleSheet()
        return (QValidator.Acceptable, text, pos)

class DimEditValidator(FloatEditValidator):
    """Validate dimension input.

    The numeric expression in the edit box is evaluated. Some python
    functions such as sin and cos are premitted. The associated FloatEdit's
    background color reflects the result of this evaluation as the expression
    is typed.
    """
    def validate(self, text, pos):
        try:
            self.result = eval(str(text), {'__builtins__': None},
                               self.sandboxFns)
        except Exception:
            self.result = None
            self.editBox.setInvalidStyleSheet()
        else:
            toolTip = str(self.editBox.dimLabel.toolTip())
            tdef = self.editBox.ttDef
            if (isinstance(self.result, (int, float))
                and self.result > 0.0
                and tdef.checkGeometry({toolTip: self.result})):
                self.editBox.setValidStyleSheet()
                # tdef.config({toolTip: self.result})
            else:
                self.result = None
                self.editBox.setInvalidStyleSheet()
        return (QValidator.Acceptable, text, pos)

class FloatEdit(QLineEdit):
    """A specialized QLineEdit.

    This widget will enable the user to enter a numeric expression, calling a
    validator at each keystroke.

    If the expression is valid, the background will be green-ish. If invalid,
    the background will be red-ish.

    The enter key will place the successful result of the expression into the
    widget.

    The widget may be initialized with a value and two flags to allow zero
    and/or negative values.

    """
    # validSS = 'QLineEdit { background-color: #aaffaa; color: #000000;' \
    #     ' selection-color: #000000; selection-background-color: #00ff00; }'
    # invalidSS = 'QLineEdit { background-color: #ffaaaa; color: #000000;' \
    #     ' selection-color: #000000; selection-background-color: #ff0000; }'
    validSS = """
    QLineEdit {
        background-color: #aaffaa; color: #000000;
        selection-color: #000000; selection-background-color: #00ff00;
    }
    QLineEdit:disabled {
        background-color: #aaffaa; color: #aaaaaa;
        selection-color: #000000; selection-background-color: #00ff00;
    }
    """
    invalidSS = """
    QLineEdit {
        background-color: #ffaaaa; color: #000000;
        selection-color: #000000; selection-background-color: #ff0000;
    }
    QLineEdit:disabled {
        background-color: #ffaaaa; color: #aaaaaa;
        selection-color: #000000; selection-background-color: #ff0000;
    }
    """
    def __init__(self, val, parent, allowZero=True, allowNeg=True,
                 minValue=0, maxValue=1000):
        super(FloatEdit, self).__init__(str(val), parent)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setValidator(FloatEditValidator(self, allowZero, allowNeg,
                                             minValue, maxValue))
        self.validator().result = val
        self.setValidStyleSheet()
    def isValid(self):
        return self.validator().result is not None
    def sizeHint(self):
        fm = QFontMetrics(self.font())
        br = fm.boundingRect('+-.0123456789')
        return br.adjusted(0, 0, 10, 5).size()
    def value(self):
        """Get the current text as a float.
        """
        return float(self.text())
    def setValidStyleSheet(self):
        """Called from the validator
        """
        self.setStyleSheet(self.validSS)
    def setInvalidStyleSheet(self):
        """Called from the validator
        """
        self.setStyleSheet(self.invalidSS)
    def text(self):
        """Return a string not a QString
        """
        return str(super(FloatEdit, self).text())
    def mousePressEvent(self, e):
        """Select all the text when clicked.
        """
        self.selectAll();
    def keyPressEvent(self, e):
        """Handle the Enter key.

        If the expression is invalid, Enter will do nothing. Else place the
        successfully eval'd expression result in the text box.
        """
        if e.key() in [qt.Key_Return, qt.Key_Enter]:
            if self.validator().result is None:
                return
            self.setText(str(self.validator().result))
        super(FloatEdit, self).keyPressEvent(e)

class DimEdit(FloatEdit):
    """A widget to edit dimension values.
    """
    def __init__(self, parent):
        super(DimEdit, self).__init__(0, parent, True, True)
        self.setValidator(DimEditValidator(self, False, False))
        self.dimLabel = None
        self.ttDef = None
    def setText(self, text):
        mo = re.match(u'[ØR]?((\d+\.\d*)|(\d*\.\d+)|\d+)(mm|°|"|in)?', text)
        if not mo:
            raise TTFloatEditException('invalid dimension text')
        super(DimEdit, self).setText(mo.group(1))
    def textValue(self):
        return float(self.text())
    def setItems(self, label, tdef):
        self.dimLabel = label
        self.ttDef = tdef
    def keyPressEvent(self, e):
        """Handle the Enter key.

        If the expression is invalid, Enter will do nothing. Else, config the
        associated TTToolDef, hide this QLineEdit, and call fitAll on this
        widgets's parent (a QGraphicsView).
        
        If the escape key is pressed hide this widget and set focus to its
        parent.

        All other keys are passed on.
        """
        if e.key() in [qt.Key_Return, qt.Key_Enter]:
            if self.validator().result is None:
                return
            self.ttDef.config({self.dimLabel.toolTip():
                               self.validator().result})
            self.hide()
            self.parent().setFocus()
            self.parent().fitAll()
        if e.key() == qt.Key_Escape:
            self.hide()
            self.parent().setFocus()
        FloatEdit.keyPressEvent(self, e)
    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self.hide()


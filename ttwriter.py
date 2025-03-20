#!/usr/bin/python3

# ttwriter.py
# S. Edward Dolan
# Thursday, December 26 2024
# 
# Pretty Print XML in nXML mode: C-x h C-M-\
# 

import os
import platform
from copy import copy
from math import tan, radians
import xml.etree.ElementTree as ET


def mergeDicts(d1, d2):
    d = {};
    d.update(d1);
    d.update(d2);
    return d

class TTWriterError(Exception):
    pass

class TTWriter(object):
    """Create and write a Tru-Tech XML program file.
    """
    progName='271224101020.xml'
    progPath='C:\\Program Files\\Tru Delta\\Customer Files\\Program Files'
    DEFAULT_AXIS_2_BACKLASH = 0.045
    DEFAULT_REPOSITION_VELOCITY = 5.0
    # values written with "%d" instead of "%.5f"
    integerIds = ['RETURN_TO_NEG', 'NUMBER_LOOPS', 'AXIS_2_RETURN',
                  'PROGRAM_LOOPS', 'TRAVERSE_AXIS_3']
    def __init__(self):
        self.reset()
    def reset(self):
        """Start a fresh program.
        """
        self.orderNumber = 1    # grinding operation index number
        # You can pass a path to ET.parse() directly but it will not work with
        # read-only files.
        with open('./dat/std_xml_scripts/skel.xml', 'r') as f:
            self.prog = ET.parse(f)
        self.bsNode = self.prog.getroot()[4]
    def write(self, fname=None):
        """Write the XML to the given file name.

        NOTE: The file will be over-written without warning.
        """
        if fname is None:
            if (platform.system() == 'Windows'):
                fname = os.path.join(self.progPath, self.progName)
            else:
                fname = './' + self.progName
        self.prog.write(fname)
    def nextOrderNumber(self):
        """Return the next order number.
        """
        x = self.orderNumber
        self.orderNumber += 1
        return x
    def _appendNode(self, node, d):
        """Update the node with the dict and append the node to the program.
        """
        n = self.nextOrderNumber()
        node.attrib['Order'] = "%d" % n
        moveIndexNode = node.find('MOVEINDEX')
        moveIndexNode.text = "%d" % (n - 1)
        variableNode = node.find('VARIABLES')
        for n in variableNode:
            idNode = n.find("ID")
            if idNode.text in d:
                valueNode = n.find("VALUE")
                if idNode.text in TTWriter.integerIds:
                    valueNode.text = ("%d" % d[idNode.text])
                else:
                    valueNode.text = ("%.5f" % d[idNode.text])
        self.bsNode.append(node)
    def rollerOn(self, d={}):
        """Append a 'Roller On' MOVE element.
        
        This is program start-up and initialization.
        """
        dd = {                  # default values
            'PLUNGE_DEPTH': 0.0,
            'PROGRAM_LOOPS': 1,
            'FINAL_PLUNGE': 0.0,
            'TRAVERSE_AXIS_3': False
        }
        node = ET.parse('./dat/std_xml_scripts/roller_on.xml').getroot()
        self._appendNode(node, mergeDicts(dd, d))
    def rapidIn(self, d={}):
        """Append a 'Rapid In' MOVE element.

        This is the initial move to the part.
        """
        dd = {
            'ABOVE_PART': 0.01,
            'RAPID_DOWN_TO': 0.0,
            'RAPID_IN_TO': 0.0,
            'RAPID_DOWN_VELOCITY': 0.5,
            'AXIS2_BACKLASH': TTWriter.DEFAULT_AXIS_2_BACKLASH
        }
        node = ET.parse('./dat/std_xml_scripts/rapid_in.xml').getroot()
        self._appendNode(node, mergeDicts(dd, d))
    def axisOne(self, d={}):
        """Append an 'Axis 1' MOVE element.

        This is a Y-axis (vertical) move.
        """
        dd = {
            'PLUNGE_TO': 0.0,
            'VELOCITY_AXIS1': 0.05,
            'RETURN_TO_NEG': True, # written as 1 or 0
            'NEG_POSITION': 0.01
        }
        node = ET.parse('./dat/std_xml_scripts/axis_1.xml').getroot()
        self._appendNode(node, mergeDicts(dd, d))
    def axisTwoOut(self, d={}):
        """Append an 'Axis 2 Out' MOVE element.

        This is a Z-axis move toward the front of the part.
        """
        dd = {
            'MOVE_OUT_TO': 0.0,
            'VELOCITY_AXIS2': 2.0
        }
        node = ET.parse('./dat/std_xml_scripts/axis_2_out.xml').getroot()
        self._appendNode(node, mergeDicts(dd, d))
    def axisTwoIn(self, d={}):
        """Append an 'Axis 2 In' MOVE element.

        This is a Z-axis move toward the back of the part.
        """
        dd = {
            'MOVE_IN_TO': 0,
            'VELOCITY_AXIS2': 5.0,
            'AXIS2_BACKLASH': TTWriter.DEFAULT_AXIS_2_BACKLASH
        }
        node = ET.parse('./dat/std_xml_scripts/axis_2_in.xml').getroot()
        self._appendNode(node, mergeDicts(dd, d))
    def ccwRadius(self, d):
        """Append a 'CCW Radius' MOVE element.

        This is an inside, corner fillet grind move.

        The envelope of the radius is an arc that starts @ 270 degrees and
        sweep CWW 180 degrees. This assumes 0 degrees is at 3 o'clock in a
        right-handed cartesian coordinate system.

        START_PERCENT and END_PERCENT are the 't' times along this arc and
        must be in the interval [0.0, 1.0].

        START_PERCENT = 0, END_PERCENT = 0.5 will produce a 90 deg fillet.
        """
        dd = {
            'RADIUS_VALUE': .01,
            'START_PERCENT': 0,
            'END_PERCENT': .5,
            'RADIUS_VELOCITY': .05
        }
        node = ET.parse('./dat/std_xml_scripts/ccw_radius.xml').getroot()
        self._appendNode(node, mergeDicts(dd, d))
    def cwRadius(self, d):
        """Append a 'CW Radius' MOVE element.

        This is an outside, corner radius grind move.

        The envelope of the radius is an arc that starts @ 270 degrees and
        sweep CW 180 degrees. This assumes 0 degrees is at 3 o'clock in a
        right-handed cartesian coordinate system.

        START_PERCENT and END_PERCENT are the 't' times along this arc and
        must be in the interval [0.0, 1.0].
        
        START_PERCENT = 0.5, END_PERCENT = 1.0 will produce a 90 deg radius.
        """
        dd = {
            'RADIUS_VALUE': .01,
            'START_PERCENT': 0.5,
            'END_PERCENT': 1,
            'RADIUS_VELOCITY': .05
        }
        node = ET.parse('./dat/std_xml_scripts/cw_radius.xml').getroot()
        self._appendNode(node, mergeDicts(dd, d))
    def dwell(self, d={}):
        """Append a 'Dwell' MOVE element.
        """
        dd = {'DWELL': 1.0}
        node = ET.parse('./dat/std_xml_scripts/dwell.xml').getroot()
        self._appendNode(node, mergeDicts(dd, d))
    def angle(self, d={}):
        """Append an 'Angle' MOVE element.
        """
        dd = {
            'ANGLE': 45.0,
            'TAPER_DOWN_TO': 0.0,
            'TAPER_VELOCITY': 0.05
        }
        node = ET.parse('./dat/std_xml_scripts/angle.xml').getroot()
        self._appendNode(node, mergeDicts(dd, d))
    def loopPlunge(self, d={}):
        """Append a 'Loop Plunge' MOVE element.
        """
        dd = {
            'RAPID_DOWN_TO': 0.0,
            'DEPTH_OF_PLUNGE': 0.0,
            'VELOCITY_AXIS1': 0.05,
            'WIDTH_OF_PLUNGE': 0.0,
            'PLUNGE_DWELL': 0.0,
            'NUMBER_LOOPS': 1,
            'RETURN_TO_NEG': True,
            'NEG_POSITION': 0.01
        }
        node = ET.parse('./dat/std_xml_scripts/loop_plunge.xml').getroot()
        self._appendNode(node, mergeDicts(dd, d))
    def backTaper(self, d={}):
        """Append a 'Back Taper' MOVE element.

        This is a Z-axis move toward the front of the part with a bit of
        Y-axis delta toward the sky.
        """
        dd = {
            'TAPER_UP_TO': 0.0,
            'TAPER_OUT_TO': 0.0,
            'TAPER_VELOCITY': 2.0
        }
        node = ET.parse('./dat/std_xml_scripts/back_taper.xml').getroot()
        self._appendNode(node, mergeDicts(dd, d))
    def rollerOff(self, d={}):
        """Append a 'Roller Off' MOVE element.
        """
        dd = {
            'NEG_HOME_AXIS1': 1.5,
            'NEG_HOME_AXIS2': 0.5,
            'AXIS_1_VELOCITY': 15.0,
            'AXIS_2_VELOCITY': 15.0,
            'AXIS_2_RETURN': True
        }
        node = ET.parse('./dat/std_xml_scripts/roller_off.xml').getroot()
        self._appendNode(node, mergeDicts(dd, d))
    def getSimProgram(self, blankDia):
        """Parse the XML generating commands for the simulator.

        blankDia -- blank diameter of tool being sumulated
        
        NOTE: This method expects the MOVE nodes to be in the order in which
              they will be executed. This will always be true for a freshly
              generated program by TTWriter.

              However, if a random XML file is read, the MOVE order may be
              mixed up if the user rearranged the ops in the TT gui.
        """
        x = 0                   # keep track of the...
        y = 0                   # ...current position
        br = blankDia / 2.0
        outProg = []
        order = -1
        for n in self.prog.find('BUILDERSCRIPTS'):
            if int(n.attrib['Order']) <= order:
                raise TTWriterError("Nodes are out of order, cannot proceed.")
            order = int(n.attrib['Order'])
            id = n.attrib['Id']
            d = {}
            for v in n.find('VARIABLES'):
                d[v.find('ID').text] = float(v.find('VALUE').text)
            #
            # Move both x and y at feed
            #
            if id == 'Angle':
                dy = y - (br - d['TAPER_DOWN_TO'])
                x -= dy / tan(radians(d['ANGLE']))
                y -= dy
                outProg.append({'line': {'x': x, 'y': y,
                                         'f': d['TAPER_VELOCITY']},
                                'msg': 'angle x and y at feed'})
            #
            # Move y at feed
            #
            elif id == 'Axis1':
                y = br - d['PLUNGE_TO']
                outProg.append({'line': {'x': x, 'y': y,
                                         'f': d['VELOCITY_AXIS1']},
                                'msg': 'move y at feed'})
                if d['RETURN_TO_NEG']:
                    y = br + d['NEG_POSITION']
                    outProg.append({'go': {'x': x, 'y': y},
                                    'msg': 'return to neg'})
            #
            # Move x to back of blank with possible backlash
            #
            elif id == 'Axis2In':
                bl = d['AXIS2_BACKLASH']
                x = d['MOVE_IN_TO'] + bl
                outProg.append({'line': {'x': x, 'y': y,
                                         'f': d['VELOCITY_AXIS2']},
                                'msg': 'position x at feed'})
                if bl:
                    x -= bl
                    outProg.append({'line': {'x': x, 'y': y,
                                             'f': d['VELOCITY_AXIS2']},
                                    'msg': 'shitty backlash comp'})
            #
            # Move x at feed toward front of part
            #
            elif id == 'Axis2Out':
                x = d['MOVE_OUT_TO']
                outProg.append({'line': {'x': x, 'y': y,
                                         'f': d['VELOCITY_AXIS2']},
                                'msg': 'feed x move'})
            #
            # move x and y, at feed, at a slight taper in y
            #
            elif id == 'Back Taper':
                y = br - d['TAPER_UP_TO']
                x = d['TAPER_OUT_TO']
                outProg.append({'line': {'x': x, 'y': y,
                                         'f': d['TAPER_VELOCITY']},
                                'msg': 'back taper up to'})
            #
            #
            #
            elif id == 'CCWRadius': pass
            #
            #
            #
            elif id == 'CWRadius': pass
            #
            # Shitty groove cycle
            #
            elif id == 'Loop Plunge':
                for i in range(int(d['NUMBER_LOOPS'])):
                    x += d['WIDTH_OF_PLUNGE']
                    outProg.append({'go': {'x': x, 'y': y},
                                    'msg': 'loop position x'})
                    y = br - d['RAPID_DOWN_TO']
                    outProg.append({'go': {'x': x, 'y': y},
                                    'msg': 'loop down to top of blank'})
                    y = br - d['DEPTH_OF_PLUNGE']
                    outProg.append({'line': {'x': x, 'y': y,
                                             'f': d['VELOCITY_AXIS1']},
                                    'msg': 'loop plunge'})
                    if d['PLUNGE_DWELL']:
                        outProg.append({'dwell': d['PLUNGE_DWELL']})
                    if d['RETURN_TO_NEG']:
                        y = br + d['NEG_POSITION']
                        outProg.append({'go': {'x': x, 'y': y},
                                        'msg': 'loop return to neg'})
            #
            # Rapid move toward the back of the blank
            #
            elif id == 'RapidIn':
                bl = d['AXIS2_BACKLASH']
                x = d['RAPID_IN_TO'] + bl
                y = d['ABOVE_PART'] + br
                # move with backlash
                outProg.append({'go': {'x': x, 'y': y},
                                'msg': 'rapid in to x and y'})
                if bl != 0:
                    x = d['RAPID_IN_TO']
                    y = d['ABOVE_PART'] + br
                    # shit move to try to compensate for backlash
                    outProg.append({'go': {'x': x, 'y': y},
                                'msg': 'shitty backlash comp move'})
                # feed down to blank
                y = br + d['RAPID_DOWN_TO']
                outProg.append({'line': {'x': x, 'y': y,
                                         'f': d['RAPID_DOWN_VELOCITY']},
                                'msg': 'move down to top of blank'})
            #
            # Roller Off (end of program)
            #
            elif id == 'Off':
                x = -d['NEG_HOME_AXIS2']
                y = d['NEG_HOME_AXIS1'] + br
                outProg[0]['home']['x'] = x
                outProg[0]['home']['y'] = y
                outProg.append({'home': {'x': x, 'y': y}})
            #
            # Roller On (start of prog)
            #
            elif id == 'On':
                outProg.append({'home': {'x': 0, 'y': 0}}) # stub
        return outProg
# 
# Test it, sorta...
# 
if __name__ == '__main__':
    ttw = TTWriter()
    ttw.rollerOn()
    ttw.dwell()
    ttw.rapidIn()
    ttw.dwell()
    ttw.axisOne()
    ttw.dwell()
    ttw.loopPlunge()
    ttw.dwell()
    ttw.axisTwoIn()
    ttw.dwell()
    ttw.angle()
    ttw.dwell()
    ttw.backTaper()
    ttw.dwell()
    ttw.angle({'ANGLE': 67.5, 'TAPER_DOWN_TO': .1953, 'TAPER_VELOCITY': .1})
    ttw.dwell()
    ttw.rollerOff()
    ttw.dwell()
    ttw.write('test.xml')

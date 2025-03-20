# ttpathgen.py
# S. Edward Dolan
# Monday, January 13 2025

from math import *

from PyQt5.QtCore import QPointF, QLineF

from algo import tipLength

class TTPathGenError(Exception):
    pass

def getPlungePoints(specs, elements, i, startZ=None):
    """Given the elements of a tool profile, return the rough plunge points.

    specs -- tool specs, wheel width, and wheel overlap percentage
    elements -- list of points or arc descriptors for the profile
    i -- index of last element to grind
    startZ -- first plunge position in Z (right side of wheel), or None

    NOTE: arcs are not currently handled

    Return two lists.

    The first contains the plunge coordinates [[z1, dy1], [z2, dy2], ... [zN,
    dyN]] or [] if no plunge roughing is necessary.

    The second is the profile elements translated such that the shank line is
    at Y=0. This will make all shifted non-zero Y coordinates negative.
    """
    bd = specs['blankDia']
    ww = specs['wheelWidth']
    wo = specs['wheelOverlap']
    # Translate the elements so the shank line is at Y=0
    te = []
    for e in elements:
        if len(e) != 2:
            raise TTPathGenError('getPlungePoints() does not currently'
                                 ' handle arcs')
        te.append([e[0], (bd / 2 - e[1])])
    zlen = elements[i][0]
    if startZ is not None and startZ >= zlen:
        raise TTPathGenError('getPlungePoints startZ exceeds last ground'
                             ' element')
    if startZ is not None:
        zlen -= startZ
    n = ceil(zlen / (ww * wo))  # number of rough plunges
    zStep = zlen / n            # z step-over per plunge
    z = zStep
    rp = QPointF()
    # ===================================================================
    # Find the rough plunge coords [[z1, dy1], [z2, dy2], ..., [zN, dyN]]
    #
    plungePts = []
    for i in range(n - (1 if startZ is None else 0)):
        # NOTE: itertools.pairwise() requires python 3.10 or above
        for a, b in zip(te, te[1:]):
            if (a[1] == 0.0 and b[1] == 0.0) or a[0] == b[0]:
                continue    # shank horizontal line or vertical line
            l1 = QLineF(a[0], a[1], b[0], b[1])
            if i == 0 and startZ is not None:
                l2 = QLineF(startZ, bd, startZ, -bd)
            else:
                l2 = QLineF(z, bd, z, -bd)
            if l2.intersect(l1, rp) == QLineF.BoundedIntersection:
                plungePts.append([rp.x(), rp.y()])
                break
        if startZ is not None:
            z = startZ + zStep * (i + 1)
        else:
            z = zStep * (i + 2)
    return plungePts, te

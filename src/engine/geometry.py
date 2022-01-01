import math

from engine.log import log

"""
Note, all angles below are in radians. You can convert
between degrees and radians in your code as follows:

    import math
    r = math.radians(d)
    d = math.degrees(r)
"""


def rectContains(rect, x, y):
    """
    returns True if rect contains x,y else returns False.
    rect must contain at least x, y and should have width, height
    """
    if "point" in rect or (not "width" in rect) or (not "height" in rect) or rect["width"] == 0 or rect["height"] == 0:
        # rect is a point
        return False
    if rect["x"] <= x and x <= rect["x"] + rect["width"] and rect["y"] <= y and y <= rect["y"] + rect["height"]:
        return True
    return False


def rectsContains(rects, x, y):
    """
    returns first rect in list of rects, that contains x,y.
    Each rect must contain at least x, y and should have width, height
    """
    for rect in rects:
        if "point" in rect or (not "width" in rect) or (
                not "height" in rect) or rect["width"] == 0 or rect["height"] == 0:
            # rect is a point
            contine
        if rect["x"] <= x and x <= rect["x"] + rect["width"] and rect["y"] <= y and y <= rect["y"] + rect["height"]:
            return rect
    return None


def allRectsContains(rects, x, y):
    """
    returns list of only those rects, that contains x,y.
    Each rect must contain at least x, y and should have width, height.
    """
    contains = []
    for rect in rects:
        if rectContains(rect, x, y):
            contains.append(rect)
    return contains


def normalizeAngle(a):
    """ Return a in range 0 - 2pi. a must be in radians. """
    while a < 0:
        a += math.pi * 2
    while a >= math.pi * 2:
        a -= math.pi * 2
    return a


def angle(x1, y1, x2, y2):
    """ Return angle from (x1,y1) and (x2,y2) in radians. """
    delta_x = x2 - x1
    delta_y = y2 - y1
    a = math.atan2(delta_y, delta_x)
    # atan2 return between -pi and pi. We want between 0 and 2pi with 0 degrees at 3 oclock
    return normalizeAngle(a)


def distance(x1, y1, x2, y2):
    """ Return distance between (x1,y1) and (x2,y2) """
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def project(x, y, rad, dis):
    """
    Return point (x',y') where angle from (x,y) to (x',y')
    is rad and distance from (x,y) to (x',y') is dis.
    """

    xp = x + dis * math.cos(rad)
    yp = y + dis * math.sin(rad)

    return xp, yp


def sortXY(listOfGameObs, maxWidth, useAnchor=True):
    '''
    sort list of game objects by y and then x. Do sort in place but list is also returned in case needed.

    Schwartzian Transform is used to speed up sort.
    https://gawron.sdsu.edu/compling/course_core/python_intro/intro_lecture_files/fastpython.html#setgetdel
    '''

    if useAnchor:  # use the anchor point to sort by
        listOfGameObs[:] = [(maxWidth * o["anchorY"] + o["anchorX"], o) for o in listOfGameObs]
    else:  # use x,y to sort by
        listOfGameObs[:] = [(maxWidth * (o["y"] + o['height'] / 2) + o["x"] + o['width'] / 2, o) for o in listOfGameObs]
    listOfGameObs.sort(key=lambda x: x[0])
    listOfGameObs[:] = [o for (k, o) in listOfGameObs]

    return listOfGameObs

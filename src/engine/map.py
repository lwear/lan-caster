import json

import engine.log
from engine.log import log
import engine.geometry as geo


class Map:
    '''
    The objects in object layers have the following keys:
    permanent keys: name, type, x, y, width, height, anchorX, anchorY
    dynamic keys (only in object while in use): destX, destY, speed, labelText (see player class)
    tile objects always have key: gid, tilesetName, tilesetTileNumber
    text object always have key: text

    Tiled layer objects are stored as Python Dictionaries. (https://www.w3schools.com/python/python_dictionaries.asp)

    Sample Sprite Object:
    {
      * 'anchorX': 260.2614907044467,
      * 'anchorY': 394.0083806621534,
      o 'destX': 255,
      o 'destY': 394,
      o 'gid': 151,
      * 'height': 32,
      * 'mapName': 'actions',
      * 'name': '',
      o 'playerNumber': 1,
      o 'properties': {'labelText': 'Bob'},
      o 'speed': 120,
      o 'tilesetName': 'fantasy-tileset',
      o 'tilesetTileNumber': 150,
      * 'type': 'player',
      * 'width': 32,
      * 'x': 244.26149070444671,
      * 'y': 378.0083806621534
    }

    * Required keys are always present and can be used with checking if they exist.

    o Optional keys are only present when in use. If not sure then check before use.
      eg. if 'gid' in sprite:
            do something with sprite['gid']

    '''
    ########################################################
    # INIT
    ########################################################

    def __init__(self, tilesets, mapDir, game):
        self.mapDir = mapDir
        self.tilesets = tilesets

        # Flag to say something on this map has changed
        self.changed = False

        # Maps are named based on their mapDirectory
        self.name = mapDir.split("/")[-1]

        # read tiled map file.
        with open(mapDir + "/" + self.name + ".json") as f:
            mapfiledata = json.load(f)

        # ensure tiled map file is correct format.
        if mapfiledata["type"] != "map" or mapfiledata["orientation"] != "orthogonal":
            log(f"{mapDir} does not appear to be an orthogonal map!", "FAILURE")
            exit()

        # store for later use in case needed by a subclass.
        self.mapfiledata = mapfiledata

        # extract basic data from map file
        self.height = mapfiledata["height"]
        self.width = mapfiledata["width"]
        self.tileheight = mapfiledata["tileheight"]
        self.tilewidth = mapfiledata["tilewidth"]
        self.pixelHeight = self.height * self.tileheight
        self.pixelWidth = self.width * self.tilewidth
        self.layers = mapfiledata["layers"]

        # convert layer visibility data into a more useful form.
        self.layerVisabilityMask = 0
        for layerIndex in range(len(self.layers)):
            if self.layers[layerIndex]["visible"] == True:
                self.setLayerVisablitybyIndex(layerIndex, True)

        '''
        Create quick reference dict from tileset name to firstgid.
        {filesetName1: firstgid1, tilesetName2: firstgid2, ...}
        '''
        self.tsFirstGid = {}
        for ts in mapfiledata["tilesets"]:
            name = ts["source"].split("/")[-1].split(".")[0]
            self.tsFirstGid[name] = ts["firstgid"]

        # set up quick reference to object lists of well known object layers.
        self.triggers = []
        self.sprites = []
        self.reference = []
        self.inBounds = []
        self.outOfBounds = []
        self.overlay = []
        for l in mapfiledata["layers"]:
            if l["type"] == "objectgroup":
                if l["name"] == "triggers":
                    self.triggers = l['objects']
                elif l["name"] == "sprites":
                    self.sprites = l['objects']
                elif l["name"] == "reference":
                    self.reference = l['objects']
                elif l["name"] == "inBounds":
                    self.inBounds = l['objects']
                elif l["name"] == "outOfBounds":
                    self.outOfBounds = l['objects']
                elif l["name"] == "overlay":
                    self.overlay = l['objects']

        '''
        objects loaded from tiled need some data conversion and data added to be useful
        '''
        for layer in self.layers:
            if layer["type"] == "objectgroup":
                for object in layer['objects']:
                    '''
                    convert tiled object properties into a more useful form.
                    from: {{name: name1, value: value1},...}
                    to: {name1: value1,...}
                    '''
                    if "properties" in object:
                        newprops = {}
                        for prop in object["properties"]:
                            newprops[prop["name"]] = prop["value"]
                        object["properties"] = newprops

                    # if this is a tiled "tile object"
                    if "gid" in object:
                        '''
                        tiled tile objects are anchored at bottom left but we want to anchor
                        all objects to the top left.
                        '''
                        object["y"] -= object["height"]

                    # finaly check the object for any other missing data that is not directly
                    # related to the tiled file format.
                    self.checkObject(object)

    def __str__(self):
        return engine.log.objectToStr(self, depth=2)

    ########################################################
    # MAP CHANGED
    ########################################################

    def setMapChanged(self, changed=True):
        self.changed = changed

    ########################################################
    # LAYER VISABILITY
    ########################################################

    def setLayerVisablitybyName(self, layerName, visable):
        for layerIndex in range(len(self.layers)):
            if self.layers[layerIndex]["name"] == layerName:
                self.setLayerVisablitybyIndex(layerIndex, visable)

    def setLayerVisablitybyIndex(self, layerIndex, visable):
        old = self.layerVisabilityMask
        if visable:
            self.layerVisabilityMask = self.layerVisabilityMask | (1 << layerIndex)
        else:
            self.layerVisabilityMask = self.layerVisabilityMask & ~(1 << layerIndex)
        if old != self.layerVisabilityMask:
            self.setMapChanged()

    def getLayerVisablitybyName(self, layerName):
        for layerIndex in range(len(self.layers)):
            if self.layers[layerIndex]["name"] == layerName:
                return self.getLayerVisablitybyIndex(layerIndex)

    def getLayerVisablitybyIndex(self, layerIndex):
        if self.layerVisabilityMask & (1 << layerIndex) != 0:
            return True
        return False

    def getLayerVisablityMask(self):
        return self.layerVisabilityMask

    def setLayerVisablityMask(self, layerVisabilityMask):
        if self.layerVisabilityMask == layerVisabilityMask:
            return False
        self.layerVisabilityMask = layerVisabilityMask
        self.setMapChanged()
        return True

    ########################################################
    # TILE GID
    ########################################################

    def findTile(self, tileGid):
        # converts Gid for this map to a tileset specific tile number.
        for tilesetName in self.tsFirstGid:
            firstGid = self.tsFirstGid[tilesetName]
            lastGid = firstGid + self.tilesets[tilesetName].tilecount - 1
            if firstGid <= tileGid and tileGid <= lastGid:
                tilesetTileNumber = tileGid - firstGid
                return tilesetName, tilesetTileNumber

        # By design, this should never happen so we need to quit!
        log(f"tileGid {str(tileGid)} not found in map {self.name}!", "FAILURE")
        exit()

    def findGid(self, tilesetSearchName, tilesetTileSearchNumber):
        # converts a tileset specific tile number to a Gid of this map.
        for tilesetName in self.tsFirstGid:
            if tilesetName == tilesetSearchName:
                return self.tsFirstGid[tilesetName] + tilesetTileSearchNumber

        # By design this should never happen so we need to quit!
        log(f"tilesetName {str(tilesetSearchName)} not found in map {self.name}!", "FAILURE")
        exit()

    ########################################################
    # OBJECT LIST (default objectList is self.sprites)
    ########################################################

    def addObject(self, object, objectList=False):
        # assumes that objectList is from an object layer on this may.
        # recored in the object itself that it is now on this map.
        if not isinstance(objectList, list):
            objectList = self.sprites

        object["mapName"] = self.name

        # add object to list
        objectList.append(object)

        # Update tile gid since destMap may have a different gid for the same tile image.
        if "gid" in object:
            object["gid"] = self.findGid(object["tilesetName"], object["tilesetTileNumber"])

        self.setMapChanged()

    def removeObject(self, object, objectList=False):
        # do not remove self.name from object["mapName"] since the object could be in more than one list for this map.
        if not isinstance(objectList, list):
            objectList = self.sprites

        objectList.remove(object)
        self.setMapChanged()

    def findObject(self, x=False, y=False, name=False, type=False, objectList=False, exclude=False, returnAll=False):
        '''
        if returnAll = False (default) then return first object in objectList that meets criteria provided.
        if none is found then it returns False

        if returnAll = True then return all objects in objectList, that meets criteria provided, in a list.
        if none are found then an empty list is returned.

        Note, exclude is normally used to filter out an object that is being acted on but is also in the
        list being searched.
        '''
        if not isinstance(objectList, list):
            objectList = self.sprites

        found = []
        for object in objectList:
            if (type == False or object['type'] == type) and \
               (name == False or object['name'] == name) and \
               (exclude == False or exclude != object) and \
               (x == False or y == False or geo.objectContains(object, x, y)):
                if not returnAll:
                    return object
                found.append(object)

        if not returnAll:
            return False
        return found

    ########################################################
    # OBJECTS (mostly useful for sprites)
    ########################################################

    def checkObject(self, object):
        # object must be at dict {}

        if "mapName" not in object:
            object["mapName"] = self.name
        if "name" not in object:
            object["name"] = ""
        if "type" not in object:
            object["type"] = ""
        if "width" not in object:
            object["width"] = 0
        if "height" not in object:
            object["height"] = 0

        if "gid" in object and ("tilesetName" not in object or "tilesetTileNumber" not in object):
            '''
            objects may move between maps so in addition to the gid in this map we need to store
            the tileset name and tile number relative to the tileset so it can be used in other maps.
            '''
            object["tilesetName"], object["tilesetTileNumber"] = self.findTile(object["gid"])

        # we assume that if object has x then it has y AND if it has anchorX then it has anchorY
        if "x" not in object and "anchorX" not in object:
            object["x"] = 0
            object["anchorX"] = 0
            object["y"] = 0
            object["anchorY"] = 0
        elif "x" in object and "anchorX" not in object:
            self.setObjectLocationByXY(object, object["x"], object["y"])
        elif "x" not in object and "anchorX" in object:
            self.setObjectLocationByAnchor(object, object["anchorX"], object["anchorY"])

        # The original object has been edited but also return it so the function can be passed
        return object

    def setObjectLocationByXY(self, object, x, y):
        object["x"], object["y"] = x, y
        '''
        set the anchor for the object, this is the point we consider to be the point
        location of the object.
        '''
        if "gid" in object:
            # for tile objects, the tileset will define the anchor point.
            object["anchorX"] = object["x"] + self.tilesets[object["tilesetName"]].tileoffsetX
            object["anchorY"] = object["y"] + self.tilesets[object["tilesetName"]].tileoffsetY
        else:
            # set anchor to be the middle of the objects rect.
            object["anchorX"] = object["x"] + object["width"] / 2
            object["anchorY"] = object["y"] + object["height"] / 2

        self.setMapChanged()

    def setObjectLocationByAnchor(self, object, anchorX, anchorY):
        object["anchorX"], object["anchorY"] = anchorX, anchorY
        if "gid" in object:
            object["x"] = anchorX - self.tilesets[object["tilesetName"]].tileoffsetX
            object["y"] = anchorY - self.tilesets[object["tilesetName"]].tileoffsetY
        else:
            # set anchor to be the middle of the objects rect.
            object["x"] = anchorX - object["width"] / 2
            object["y"] = anchorY - object["height"] / 2
        self.setMapChanged()

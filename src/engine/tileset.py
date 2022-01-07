import json

import engine.log
from engine.log import log


class Tileset:
    '''
    The Tileset class is responsible for loading Tiled tileset files so they can be used by the game engine.

    It is assumed this class will be sub-classed to add additional functionality.

    Tiles within a tileset are numbers from right to left and top to bottom. The top
    left tile is number 0, the tile to it's right is numbered 1, and so on.
    '''
    def __init__(self, tilesetsDir, tilesetFile):
        self.tilesetsDir = tilesetsDir
        self.tilesetFile = tilesetsDir + "/" + tilesetFile

        # Tileset name is based on tilesetFile with .json removed
        self.name = tilesetFile.split("/")[-1].split(".")[0]

        with open(self.tilesetFile) as f:
            ts = json.load(f)

        if ts["type"] != "tileset":
            log(f"{failename} does not appear to be a tileset!", "FAILURE")
            exit()

        self.tileheight = ts["tileheight"]
        self.tilewidth = ts["tilewidth"]
        self.imageheight = ts["imageheight"]
        self.imagewidth = ts["imagewidth"]
        self.tilecount = ts["tilecount"]
        self.imagefile = ts["image"]

        # determine the tile offsets.
        if "tileoffset" in ts:
            # use the offsets provided in the file.
            self.tileoffsetX = ts["tileoffset"]["x"]
            self.tileoffsetY = ts["tileoffset"]["y"]
        else:
            # use middle of tile if data not provided in file
            self.tileoffsetX = self.tilewidth / 2
            self.tileoffsetY = self.tileheight / 2

    def __str__(self):
        return engine.log.objectToStr(self)

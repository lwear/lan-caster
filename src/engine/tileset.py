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

        # store for later use in case needed by a subclass.
        self.tilesetfiledata = ts

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

        self.tiles = {}
        if "tiles" in ts:
            for tile in ts["tiles"]:
                if "properties" in tile:
                    '''
                    convert tiled object properties into a more useful form.
                    from: {{name: name1, value: value1},...}
                    to: {name1: value1,...}
                    '''
                    newprops = {}
                    for prop in tile["properties"]:
                        newprops[prop["name"]] = prop["value"]
                    tile["properties"] = newprops

                # compute total length of animation
                if "animation" in tile:
                    tile["animationDuration"] = 0
                    for t in tile["animation"]:
                        tile["animationDuration"] += t["duration"]
                    # convert to seconds
                    tile["animationDuration"] /= 1000

                self.tiles[tile['id']] = tile

    def __str__(self):
        return engine.log.objectToStr(self)

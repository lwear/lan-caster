import json
import pygame

import engine.log
from engine.log import log


class Tileset:
    '''
    The Tileset class is responsible for:
        1) Loading Tiled tileset files and images so it an be used by the game engine.
        2) Provide utility functions on the tileset data.
    It is assumed the map class with be sub-classed to add additional functionality.

    Tiles within a tileset are numbers from right to left and top to bottom. The top
    left tile is number 0, the tile to it's right is numbered 1, and so on.
    '''
    def __init__(self, tilesetsDir, tilesetFile, loadImages):
        self.tilesetsDir = tilesetsDir
        self.tilesetFile = tilesetsDir + "/" + tilesetFile

        # Don't load the images if they will not be rendered to the screen. e.g. The server does not need images.
        self.loadImages = loadImages

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

        # determine the tile offsets.
        if "tileoffset" in ts:
            # use the offsets provided in the file.
            self.tileoffsetX = ts["tileoffset"]["x"]
            self.tileoffsetY = ts["tileoffset"]["y"]
        else:
            # use middle of tile if data not provided in file
            self.tileoffsetX = self.tilewidth / 2
            self.tileoffsetY = self.tileheight / 2

        if loadImages:
            # load the tileset image file
            self.image = pygame.image.load(f"{self.tilesetsDir}/{ts['image']}")
        else:
            self.image = False

    def __str__(self):
        return engine.log.objectToStr(self)

    def blitTile(self, tileNumber, destImage, destX, destY):
        # blit tileNumber's pixels into destImage at destX, destY

        if not self.image:
            log("Tried to blit a tile when images were not loaded!", "FAILURE")
            exit()

        # width of tileset image in tiles
        width = int(self.imagewidth / self.tilewidth)

        tileX = tileNumber % width
        tileY = int(tileNumber / width)

        srcPixelX = tileX * self.tilewidth
        srcPixelY = tileY * self.tileheight

        destImage.blit(self.image,
                       (destX, destY),
                       (srcPixelX, srcPixelY, self.tilewidth, self.tileheight)
                       )

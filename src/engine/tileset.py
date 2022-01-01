import json
import pygame

import engine.log
from engine.log import log


class Tileset:

    def __init__(self, tilesetsDir, tilesetFile, loadImages):
        self.tilesetsDir = tilesetsDir
        self.tilesetFile = tilesetsDir + "/" + tilesetFile
        self.loadImages = loadImages

        # Tilesets are named based on their tilesetFile with .json removed
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
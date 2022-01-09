import pygame

import engine.log
from engine.log import log

import engine.tileset


class ClientTileset(engine.tileset.Tileset):
    '''
    The ClientTileset class is responsible for:
        1) Loading tileset image so it an be used by the game engine.
        2) Provide tile render method.
    '''

    def __init__(self, tilesetsDir, tilesetFile):
        super().__init__(tilesetsDir, tilesetFile)

        # load the tileset image file
        self.image = pygame.image.load(f"{self.tilesetsDir}/{self.imagefile}")

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

import pygame
from pygame.locals import *

from engine.log import log
import engine.map
import engine.text
import engine.geometry as geo


class ClientMap(engine.map.Map):
    ########################################################
    # INIT METHODS
    #####################################################

    def __init__(self, tilesets, mapDir, game):
        super().__init__(tilesets, mapDir, game)  # Note, this will call readMapJson() before returning

        # pre-blit top and bottom images
        self.blitBottomImage()
        self.blitTopImage()

    ########################################################
    # LAYER VISABILITY
    ########################################################

    def setLayerVisablityMask(self, layerVisabilityMask):
        if super().setLayerVisablityMask(layerVisabilityMask):  # returns True only if new mask was different.
            # re-blit top and bottom images since they may have changed.
            self.blitBottomImage()
            self.blitTopImage()

    #####################################################
    # DRAW METHODS
    #####################################################

    def blitBottomImage(self):
        # blit together all the visible layers below the sprite layer.

        # Start with grey background.
        self.bottomImage = pygame.Surface((self.width * self.tilewidth, self.height * self.tileheight))
        self.bottomImage.fill((128, 128, 128))

        for layerNumber in range(len(self.layers)):
            if self.layers[layerNumber]["name"] == "sprites":
                break
            self.blitLayer(self.bottomImage, layerNumber)

    def blitTopImage(self):
        # blit together all the visible layers above the sprite layer.

        # Start with transparent background.
        self.topImage = pygame.Surface(
            (self.width * self.tilewidth, self.height * self.tileheight),
            pygame.SRCALPHA,
            32)
        self.topImage = self.topImage.convert_alpha()

        passedSpriteLayer = False
        for layerNumber in range(len(self.layers)):
            if self.layers[layerNumber]["name"] == "sprites":
                passedSpriteLayer = True
            if passedSpriteLayer == True:
                self.blitLayer(self.topImage, layerNumber)

    def blitLayer(self, destImage, layerNumber):
        '''
        blit layer onto destImage. Note object layers named "sprites" and "overlay" will not be rendered since
        they are provided by the server and must rendered separately with a direct call to blitObjectLayer().
        '''
        if self.getLayerVisablitybyIndex(layerNumber):
            if self.layers[layerNumber]["type"] == "tilelayer":
                self.blitTileLayer(destImage, self.layers[layerNumber])
            elif self.layers[layerNumber]["type"] == "objectgroup" and \
                    self.layers[layerNumber]["name"] != "sprites" and \
                    self.layers[layerNumber]["name"] != "overlay":
                self.blitObjectLayer(destImage, self.layers[layerNumber]["objects"])

    def blitTileLayer(self, destImage, tilelayer):
        grid = tilelayer["data"]
        for i in range(len(grid)):
            if grid[i] != 0:
                tileX = i % self.width
                tileY = int(i / self.width)
                destPixelX = tileX * self.tilewidth
                destPixelY = tileY * self.tileheight

                tilesetName, tilesetTileNumber = self.findTile(grid[i])
                ts = self.tilesets[tilesetName]

                # tiles that are bigger than the grid tiles are indexed from the bottom left tile of the grid
                # so we need to adjust the destPixelY to the true pixel top left.
                if(ts.tileheight > self.tileheight):
                    destPixelY -= (ts.tileheight - self.tileheight)
                elif(ts.tileheight < self.tileheight):
                    log("using tiles smaller than tile layer is not supported yet.", "FAILURE")
                    exit()

                ts.blitTile(tilesetTileNumber, destImage, destPixelX, destPixelY)


    def blitObjectLayer(self, destImage, objectLayer):
        geo.sortXY(objectLayer, self.pixelWidth)
        for object in objectLayer:
            if "gid" in object:
                self.blitTileObject(destImage, object)
            elif "text" in object:
                self.blitTextObject(destImage, object)
            # other object types not yet supported.

    def blitTileObject(self, destImage, tileObject):
        tilesetName, tilesetTileNumber = self.findTile(tileObject["gid"])
        self.tilesets[tilesetName].blitTile(tilesetTileNumber, destImage, tileObject['x'], tileObject['y'])

        if "properties" in tileObject and "labelText" in tileObject["properties"]:
            engine.text.Text(
                text=tileObject["properties"]["labelText"],
                centerX=tileObject['x'] + tileObject['width'] / 2,
                topY=tileObject['y'] + tileObject['height']
                ).blit(destImage)

    def blitTextObject(self, destImage, textObject):
        # Tiled does not save pixelsize if it is the default size of 16 so we need to check.
        if "pixelsize" not in textObject["text"]:
            textObject["text"]["pixelsize"] = 16

        engine.text.Text(
            textObject["text"]["text"],
            centerX=textObject["x"] + textObject['width'] / 2,
            topY=textObject["y"],
            size=textObject["text"]["pixelsize"],
            maxWidth=textObject['width']
            ).blit(destImage)

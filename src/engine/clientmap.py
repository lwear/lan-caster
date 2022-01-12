import pygame
from pygame.locals import *

from engine.log import log
import engine.map
import engine.geometry as geo


class ClientMap(engine.map.Map):
    """
    The ClientMap class is responsible for rendering a map.
    """

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
        if super().setLayerVisablityMask(layerVisabilityMask):  # returns True only if mask changed.
            # re-blit top and bottom images since they may have changed.
            self.blitBottomImage()
            self.blitTopImage()

    #####################################################
    # DRAW METHODS
    #####################################################

    def blitBottomImage(self):
        '''
        blit together all the visible layers BELOW the sprite layer and store it in
        self.bottomImage. self.bottomImage can then be used for faster screen updates
        rather than doing all the work of blitting these layers together every frame.
        '''

        # Start with grey background.
        self.bottomImage = pygame.Surface((self.width * self.tilewidth, self.height * self.tileheight))
        self.bottomImage.fill((128, 128, 128))

        for layerNumber in range(len(self.layers)):
            if self.layers[layerNumber]["name"] == "sprites":
                break
            self.blitLayer(self.bottomImage, layerNumber)

    def blitTopImage(self):
        '''
        blit together all the visible layers ABOVE the sprite layer and store it in
        self.bottomImage. self.bottomImage can then be used for faster screen updates
        rather than doing all the work of blitting these layers together every frame.
        '''

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

    def blitMap(self, destImage, sprites, overlay):
        # start with the pre-rendered image of all visible layers below the sprites.
        destImage.blit(self.bottomImage, (0, 0))

        # blit the sprite layer from the server
        self.blitObjectLayer(destImage, sprites)

        # add the pre-rendered image of all visible layers above the sprites
        destImage.blit(self.topImage, (0, 0))

        # add the overlay layer from the server
        self.blitObjectLayer(destImage, overlay)

    def blitLayer(self, destImage, layerNumber):
        '''
        blit layer onto destImage. Note object layers named "sprites" and "overlay" will not be rendered since
        they are provided by the server and must be rendered separately with a direct call to blitObjectLayer().
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
            elif "ellipse" in object:
                pass  # not yet supported.
            elif "point" in object:
                pass  # not yet supported.
            else:  # this is a rect
                pass  # not yet supported.

    def blitTileObject(self, destImage, tileObject):
        tilesetName, tilesetTileNumber = self.findTile(tileObject["gid"])
        tileset = self.tilesets[tilesetName]

        # check to see what the actual tileNumber is to be blited.
        tilesetTileNumber, effectiveUntil = tileset.effectiveTileNumber(tilesetTileNumber, tileObject)

        # bit the tile
        tileset.blitTile(tilesetTileNumber, destImage, tileObject['x'], tileObject['y'])

        # If properties -> labelText is present the render it under the tile. Normally used to display player names.
        if "properties" in tileObject and "labelText" in tileObject["properties"]:
            self.blitTextObject(
                destImage,
                {
                    'x': tileObject['x'] + tileObject['width'] / 2 - 128,
                    'y': tileObject['y'] + tileObject['height'],
                    'width': 256,
                    'height': 40,
                    'valign': "top",
                    'text': {'text': tileObject["properties"]["labelText"]}
                    })

    def blitTextObject(self, destImage, textObject):
        text = textObject["text"]["text"]
        maxWidth = textObject['width']
        if "pixelsize" in textObject["text"]:
            size = textObject["text"]["pixelsize"]
        else:
            size = 16

        pixelWidth = 0
        pixelHeight = 0

        font = pygame.freetype.Font(None, size)

        # first, split the text into words
        words = text.split()
        lines = []

        maxLineHeight = 0

        while len(words) > 0:
            # get as many words as will fit within allowed_width
            lineWords = words.pop(0)
            r = font.get_rect(lineWords)
            fw, fh = r.width, r.height
            while fw < maxWidth and len(words) > 0:
                r = font.get_rect(lineWords + ' ' + words[0])
                if r.width > maxWidth:
                    break
                lineWords = lineWords + ' ' + words.pop(0)
                fw, fh = r.width, r.height

            # add a line consisting of those words
            line = lineWords
            if pixelWidth < fw:
                pixelWidth = fw
            if maxLineHeight < fh:
                maxLineHeight = fh
            lines.append((fw, fh, line))

        pixelHeight = maxLineHeight * len(lines)
        pixelWidth += 4
        pixelHeight += 4
        image = pygame.Surface((pixelWidth, pixelHeight))
        image.fill(Color('black'))

        ty = 2
        for line in lines:
            tx = pixelWidth / 2 - line[0] / 2
            font.render_to(image, (tx, ty), line[2],
                           fgcolor=Color('green'), bgcolor=Color('black'))
            ty += maxLineHeight

        centerX = textObject["x"] + textObject['width'] / 2
        topY = textObject["y"]
        if "valign" in textObject and textObject["valign"] == "bottom":
            topY = textObject["height"] - pixelHeight

        destImage.blit(image, (centerX - pixelWidth / 2, topY))

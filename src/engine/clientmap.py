import pygame
from pygame.locals import *
import time

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
        super().__init__(tilesets, mapDir, game)

        # allocate image for each layer (exclude sprites and overlay)
        for layer in self.layers:
            if layer["name"] != "sprites" and layer["name"] != "overlay":
                layer['image'] = pygame.Surface(
                    (self.width * self.tilewidth, self.height * self.tileheight),
                    pygame.SRCALPHA,
                    32)
                layer['image'] = layer['image'].convert_alpha()
                layer['imageValidUntil'] = 0  # invalid and needs to be rendered.

        self.bottomImage = pygame.Surface((self.width * self.tilewidth, self.height * self.tileheight))
        self.bottomImageValidUntil = 0  # invalid and needs to be rendered.

        self.topImage = pygame.Surface(
            (self.width * self.tilewidth, self.height * self.tileheight),
            pygame.SRCALPHA,
            32)
        self.topImage = self.topImage.convert_alpha()
        self.topImageValidUntil = 0  # invalid and needs to be rendered.

    ########################################################
    # LAYER VISABILITY
    ########################################################

    def setLayerVisablityMask(self, layerVisabilityMask):
        if super().setLayerVisablityMask(layerVisabilityMask):  # returns True only if mask changed.
            # invalidate top and bottom images since they may have changed.
            self.bottomImageValidUntil = 0
            self.topImageValidUntil = 0

    #####################################################
    # DRAW METHODS
    #####################################################

    def blitMap(self, destImage, sprites, overlay):
        validUntil = []
        # start with all visible layers below the sprites.
        validUntil.append(self.blitBottomImage(destImage))

        # blit the sprite layer from the server
        validUntil.append(self.blitObjectList(destImage, sprites))

        # add all visible layers above the sprites
        validUntil.append(self.blitTopImage(destImage))

        # add the overlay layer from the server
        validUntil.append(self.blitObjectList(destImage, overlay))

        return min(validUntil)

    def blitBottomImage(self, destImage):
        '''
        blit together all the visible layers BELOW the sprite layer and store it in
        self.bottomImage. self.bottomImage can then be used for faster screen updates
        rather than doing all the work of blitting these layers together every frame.

        Note object layers named "sprites" and "overlay" will not be rendered since
        they are provided by the server and must be rendered separately with a direct
        call to blitObjectList()
        '''
        currentTime = time.perf_counter()
        # if there is already a valid image the don't render a new one
        if self.bottomImageValidUntil < currentTime:
            # Start with grey background.
            self.bottomImage.fill((128, 128, 128, 255))

            self.bottomImageValidUntil = currentTime + 99999
            for layerNumber in range(len(self.layers)):
                if self.layers[layerNumber]["name"] == "sprites":
                    break
                if self.layers[layerNumber]["name"] == "overlay":
                    continue
                # if the layer is visible then add it to the destImage
                if self.getLayerVisablitybyIndex(layerNumber):
                    vu = self.blitLayer(self.bottomImage, self.layers[layerNumber])
                    if self.bottomImageValidUntil > vu:
                        self.bottomImageValidUntil = vu

        destImage.blit(self.bottomImage, (0, 0))
        return self.bottomImageValidUntil

    def blitTopImage(self, destImage):
        '''
        blit together all the visible layers ABOVE the sprite layer and store it in
        self.topImage. self.topImage can then be used for faster screen updates
        rather than doing all the work of blitting these layers together every frame.

        Note object layers named "sprites" and "overlay" will not be rendered since
        they are provided by the server and must be rendered separately with a direct
        call to blitObjectList()
        '''
        currentTime = time.perf_counter()
        # if there is already a valid image the don't render a new one
        if self.topImageValidUntil < currentTime:
            # Start with transparent background.
            self.topImage.fill((0, 0, 0, 0))

            self.topImageValidUntil = currentTime + 99999
            passedSpriteLayer = False
            for layerNumber in range(len(self.layers)):
                if self.layers[layerNumber]["name"] == "sprites":
                    passedSpriteLayer = True
                    continue
                if self.layers[layerNumber]["name"] == "overlay":
                    continue
                if passedSpriteLayer == True:
                    # if the layer is visible then add it to the destImage
                    if self.getLayerVisablitybyIndex(layerNumber):
                        vu = self.blitLayer(self.topImage, self.layers[layerNumber])
                        if self.topImageValidUntil > vu:
                            self.topImageValidUntil = vu

        destImage.blit(self.topImage, (0, 0))
        return self.topImageValidUntil

    def blitLayer(self, destImage, layer):
        '''
        blit layer onto destImage.
        '''
        currentTime = time.perf_counter()
        # if there is already a valid image then don't render a new one
        if layer['imageValidUntil'] < currentTime:
            # Start with transparent background.
            layer['image'].fill((0, 0, 0, 0))

            if layer["type"] == "tilelayer":
                layer['imageValidUntil'] = self.blitTileGrid(layer['image'], layer["data"])
            elif layer["type"] == "objectgroup":
                layer['imageValidUntil'] = self.blitObjectList(layer['image'], layer["objects"])

        destImage.blit(layer['image'], (0, 0))
        return layer['imageValidUntil']

    def blitTileGrid(self, destImage, grid):
        validUntil = time.perf_counter() + 99999
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

                vu = ts.blitTile(tilesetTileNumber, destImage, destPixelX, destPixelY)
                if validUntil > vu:
                    validUntil = vu

        return validUntil

    def blitObjectList(self, destImage, objectList):
        validUntil = time.perf_counter() + 99999
        vu = validUntil
        geo.sortXY(objectList, self.pixelWidth)
        for object in objectList:
            if "gid" in object:
                vu = self.blitTileObject(destImage, object)
            elif "text" in object:
                vu = self.blitTextObject(destImage, object)
            elif "ellipse" in object:
                pass  # not yet supported.
            elif "point" in object:
                pass  # not yet supported.
            else:  # this is a rect
                pass  # not yet supported.

            if validUntil > vu:
                    validUntil = vu
        return validUntil

    def blitTileObject(self, destImage, tileObject):
        tilesetName, tilesetTileNumber = self.findTile(tileObject["gid"])
        tileset = self.tilesets[tilesetName]

        # bit the tile
        validUntil = tileset.blitTile(tilesetTileNumber, destImage, tileObject['x'], tileObject['y'], tileObject)

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
        return validUntil

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

        # text does not have an end time so just sent back a long time from now
        validUntil = time.perf_counter() + 99999
        return validUntil

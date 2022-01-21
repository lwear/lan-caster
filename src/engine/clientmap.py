import pygame
from pygame.locals import *
import engine.time as time
import os
import sys

from engine.log import log
import engine.map
import engine.geometry as geo


class ClientMap(engine.map.Map):
    """
    The ClientMap class is responsible for rendering a map.
    """

    #####################################################
    # INIT METHODS
    #####################################################

    def __init__(self, tilesets, mapDir):
        super().__init__(tilesets, mapDir)

        # Layers with these names will never be rendered to the screen, even if they are set to visible.
        self.HIDELAYERS = (
            "sprites",  # the sprites in the arg list of stepMap will be rendered but not the self.layers["sprites"]
            "inBounds",
            "outOfBounds",
            "triggers",
            "reference"
            )

        # default values for optional keys in a textObject["text"] dict.
        self.DEFAULTTEXT = {
            "bold": False,
            "color": "#00ff00",
            "fontfamily": None,
            "halign": "left",
            "pixelsize": 16,
            "underline": False,
            "valign": "top",
            "wrap": True,
            "bgcolor": "#000000",
            "bgbordercolor": "#000000",
            "bgborderThickness": 0,
            "bgroundCorners": 0,
            "antialiased": True
            }

        # speechText defaults that differ from DEFAULTTEXT
        self.SPEACHTEXT = {
            "valign": "bottom",
            "halign": "center"
            }

        # labelText defaults that differ from DEFAULTTEXT
        self.LABELTEXT = {
            "halign": "center",
            "valign": "top"
            }

        # sort object layers for right-down rendering
        for layer in self.layers:
            if layer["type"] == "objectgroup":
                geo.sortRightDown(layer["objects"], self.pixelWidth)

        # allocate image for each layer (exclude hidden layers since we will never need the image)
        for layer in self.layers:
            if layer["name"] not in self.HIDELAYERS:
                layer['image'] = pygame.Surface(
                    (self.width * self.tilewidth, self.height * self.tileheight),
                    pygame.SRCALPHA,
                    32)
                layer['image'] = layer['image'].convert_alpha()
                layer['imageValidUntil'] = 0  # invalid and needs to be rendered.

        self.bottomImage = pygame.Surface(
            (self.width * self.tilewidth, self.height * self.tileheight),
            pygame.SRCALPHA,
            32)
        self.bottomImage = self.bottomImage.convert_alpha()
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
    # BLIT MAP
    #####################################################

    def blitMap(self, destImage, offset, sprites):

        # sort sprites for right-down render order.
        geo.sortRightDown(sprites, self.pixelWidth)

        # Start with grey background.
        destImage.fill((32, 32, 32, 255))

        validUntil = []
        # start with all visible layers below the sprites.
        validUntil.append(self.blitBottomImage(destImage, offset))

        # blit the sprite label text from the server under all sprites.
        validUntil.append(self.blitObjectListLabelText(destImage, offset, sprites))

        # blit the sprite layer from the server
        validUntil.append(self.blitObjectList(destImage, offset, sprites))

        # add all visible layers above the sprites
        validUntil.append(self.blitTopImage(destImage, offset))

        # blit the sprite speech text from the server on top of everything.
        validUntil.append(self.blitObjectListSpeechText(destImage, offset, sprites))

        return min(validUntil)

    def blitBottomImage(self, destImage, offset):
        '''
        blit together all the visible layers BELOW the sprite layer and store it in
        self.bottomImage. self.bottomImage can then be used for faster screen updates
        rather than doing all the work of blitting these layers together every frame.

        Note object layer "sprites" will not be rendered since
        they are provided by the server and must be rendered separately with a direct
        call to blitObjectList()
        '''
        # if there is already a valid image the don't render a new one
        if self.bottomImageValidUntil < time.perf_counter():
            # Start with transparent background.
            self.topImage.fill((0, 0, 0, 0))

            self.bottomImageValidUntil = sys.float_info.max
            for layerNumber in range(len(self.layers)):
                if self.layers[layerNumber]["name"] == "sprites":
                    break
                if self.layers[layerNumber]["name"] in self.HIDELAYERS:
                    continue
                # if the layer is visible then add it to the destImage
                if self.getLayerVisablitybyIndex(layerNumber):
                    vu = self.blitLayer(self.bottomImage, (0, 0), self.layers[layerNumber])
                    if self.bottomImageValidUntil > vu:
                        self.bottomImageValidUntil = vu

        destImage.blit(self.bottomImage, offset)
        return self.bottomImageValidUntil

    def blitTopImage(self, destImage, offset):
        '''
        blit together all the visible layers ABOVE the sprite layer and store it in
        self.topImage. self.topImage can then be used for faster screen updates
        rather than doing all the work of blitting these layers together every frame.

        Note object layer named "sprites" will not be rendered since
        they are provided by the server and must be rendered separately with a direct
        call to blitObjectList()
        '''
        # if there is already a valid image the don't render a new one
        if self.topImageValidUntil < time.perf_counter():
            # Start with transparent background.
            self.topImage.fill((0, 0, 0, 0))

            self.topImageValidUntil = sys.float_info.max
            passedSpriteLayer = False
            for layerNumber in range(len(self.layers)):
                if self.layers[layerNumber]["name"] == "sprites":
                    passedSpriteLayer = True
                    continue
                if self.layers[layerNumber]["name"] in self.HIDELAYERS:
                    continue
                if passedSpriteLayer == True:
                    # if the layer is visible then add it to the destImage
                    if self.getLayerVisablitybyIndex(layerNumber):
                        vu = self.blitLayer(self.topImage, (0, 0), self.layers[layerNumber])
                        if self.topImageValidUntil > vu:
                            self.topImageValidUntil = vu

        destImage.blit(self.topImage, offset)
        return self.topImageValidUntil

    #####################################################
    # BLIT LAYER, GRIDS, and OBJECTLISTS
    #####################################################

    def blitLayer(self, destImage, offset, layer):
        '''
        blit layer onto destImage.
        '''
        # if there is already a valid image then don't render a new one
        if layer['imageValidUntil'] < time.perf_counter():
            # Start with transparent background.
            layer['image'].fill((0, 0, 0, 0))

            if layer["type"] == "tilelayer":
                layer['imageValidUntil'] = self.blitTileGrid(layer['image'], (0,0), layer["data"])
            elif layer["type"] == "objectgroup":
                layer['imageValidUntil'] = self.blitObjectList(layer['image'], (0,0), layer["objects"])

        destImage.blit(layer['image'], offset)
        return layer['imageValidUntil']

    def blitTileGrid(self, destImage, offset, grid):
        validUntil = sys.float_info.max
        for i in range(len(grid)):
            if grid[i] != 0:
                tileX = i % self.width
                tileY = int(i / self.width)
                destPixelX = tileX * self.tilewidth + offset[0]
                destPixelY = tileY * self.tileheight + offset[1]

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

    def blitObjectList(self, destImage, offset, objectList):
        validUntil = sys.float_info.max
        vu = validUntil
        for object in objectList:
            if "gid" in object:
                vu = self.blitTileObject(destImage, offset, object)
            elif "text" in object:
                vu = self.blitTextObject(destImage, offset, object)
            elif "ellipse" in object:
                vu = self.blitRoundObject(destImage, offset, object)
            elif "point" in object:
                vu = self.blitRoundObject(destImage, offset, object)
            else:  # this is a rect
                vu = self.blitRectObject(destImage, offset, object)

            validUntil = min(validUntil, vu)
        return validUntil

    #####################################################
    # BLIT TILE OBJECT
    #####################################################

    def blitTileObject(self, destImage, offset, tileObject):
        tilesetName, tilesetTileNumber = self.findTile(tileObject["gid"])
        tileset = self.tilesets[tilesetName]

        # bit the tile
        validUntil = tileset.blitTile(tilesetTileNumber, destImage, tileObject['x'] + offset[0], tileObject['y'] + offset[1], tileObject)

        return validUntil

    #####################################################
    # BLIT TEXT
    #####################################################

    def blitObjectListSpeechText(self, destImage, offset, objectList):
        validUntil = sys.float_info.max
        vu = validUntil
        for object in objectList:
            vu = self.blitSpeechText(destImage, offset, object)
            validUntil = min(validUntil, vu)
        return validUntil

    def blitSpeechText(self, destImage, offset, object):
        validUntil = sys.float_info.max
        # If speechText is present then render it above the tile.
        if "speechText" in object:
            text = self.SPEACHTEXT.copy()
            text["text"] = object["speechText"]
            textObject = {
                'x': object['x'] + object['width'] / 2 - 64,
                'y': object['y'],
                'width': 128,
                'height': 0,
                'text': text
                }

            validUntil = self.blitTextObject(destImage, offset, textObject)
        return validUntil

    def blitObjectListLabelText(self, destImage, offset, objectList):
        validUntil = sys.float_info.max
        vu = validUntil
        for object in objectList:
            vu = self.blitLabelText(destImage, offset, object)
            validUntil = min(validUntil, vu)
        return validUntil

    def blitLabelText(self, destImage, offset, object):
        validUntil = sys.float_info.max
        # If labelText is present then render it under the tile. Normally used to display player names.
        if "labelText" in object:
            text = self.LABELTEXT.copy()
            text["text"] = object["labelText"]
            textObject = {
                'x': object['x'] + object['width'] / 2 - 64,
                'y': object['y'] + object['height'],
                'width': 128,
                'height': 0,
                'text': text
                }

            validUntil = self.blitTextObject(destImage, offset, textObject)
        return validUntil

    def blitTextObject(self, destImage, offset, textObject, mapRelative=True):
        maxWidth = textObject['width']

        # add text defaults if they are missing
        text = self.DEFAULTTEXT.copy()
        text.update(textObject["text"])
        textObject["text"] = text

        fontFilename = f'src/{self.game}/fonts/{textObject["text"]["fontfamily"]}.ttf'
        if not os.path.isfile(fontFilename):
            fontFilename = None
        if fontFilename:
            font = pygame.freetype.Font(fontFilename, textObject["text"]["pixelsize"])
        else:
            font = pygame.freetype.SysFont(textObject["text"]["fontfamily"], textObject["text"]["pixelsize"])

        font.strong = textObject["text"]["bold"]
        font.underline = textObject["text"]["underline"]
        font.antialiased = textObject["text"]["antialiased"]

        font.fgcolor = pygame.Color(textObject["text"]["color"])
        # Tiled hex colors with alpha are #argb but pygame needs #rgba so now flip alpha to the end.
        if len(textObject["text"]["color"]) == 9:  # eg. "#AARRGGBB"
            font.fgcolor = pygame.Color(font.fgcolor[1], font.fgcolor[2], font.fgcolor[3], font.fgcolor[0])

        lines = []
        if textObject["text"]["wrap"]:
            words = textObject["text"]["text"].split()
            pixelWidth = 0
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
        else:
            r = font.get_rect(text)
            pixelWidth = r.width
            maxLineHeight = r.height
            lines.append((r.width, r.height, textObject["text"]["text"]))

        pixelHeight = maxLineHeight * len(lines)
        pixelWidth += 4
        pixelHeight += 4
        image = pygame.Surface((pixelWidth, pixelHeight), pygame.SRCALPHA, 32)
        image = image.convert_alpha()
        image.fill((0, 0, 0, 0))

        ty = 2
        for line in lines:
            if textObject["text"]["halign"] == "left":
                tx = 2
            elif textObject["text"]["halign"] == "center":
                tx = pixelWidth / 2 - line[0] / 2
            elif textObject["text"]["halign"] == "right":
                tx = pixelWidth - line[0] - 2
            font.render_to(image, (tx, ty), line[2])
            ty += maxLineHeight

        if textObject["text"]["halign"] == "left":
            destX = textObject["x"]
        elif textObject["text"]["halign"] == "center":
            destX = textObject["x"] + textObject['width'] / 2 - pixelWidth / 2
        elif textObject["text"]["halign"] == "right":
            destX = textObject["x"] + textObject["width"] - pixelWidth
        else:
            log(f'halign == {textObject["text"]["halign"]} is not supported', 'FAILURE')
            exit()

        if textObject["text"]["valign"] == "top":
            destY = textObject["y"]
        elif textObject["text"]["valign"] == "center":
            destY = textObject["y"] + textObject["height"] / 2 - pixelHeight / 2
        elif textObject["text"]["valign"] == "bottom":
            destY = textObject["y"] + textObject["height"] - pixelHeight
        else:
            log(f'valign == {textObject["text"]["valign"]} is not supported', 'FAILURE')
            exit()

        buffer = textObject["text"]["bgborderThickness"] + textObject["text"]["bgroundCorners"]

        if mapRelative:
            destWidth = self.pixelWidth
            destHeight = self.pixelHeight
        else:
            destWidth = destImage.get_width()
            destHeight = destImage.get_height()

        if destX - buffer < 0:
            destX = buffer
        if destY - buffer < 0:
            destY = buffer
        if destX + pixelWidth + buffer * 2 > destWidth:
            destX = destWidth - pixelWidth - buffer
        if destY + pixelHeight + buffer * 2 > destHeight:
            destY = destHeight - pixelHeight - buffer

        destX += offset[0]
        destY += offset[1]

        self.blitRectObject(destImage, (0,0), {
            'x': destX - buffer,
            'y': destY - buffer,
            'width': pixelWidth + buffer * 2,
            'height': pixelHeight + buffer * 2
            },
            fillColor=textObject["text"]["bgcolor"],
            borderColor=textObject["text"]["bgbordercolor"],
            borderThickness=textObject["text"]["bgborderThickness"],
            roundCorners=textObject["text"]["bgroundCorners"])

        destImage.blit(image, (destX, destY))

        # text does not have an end time so just sent back a long time from now
        validUntil = sys.float_info.max
        return validUntil

    #####################################################
    # BLIT/DRAW SHAPE OBJECTS
    #####################################################

    def blitRectObject(self, destImage, offset, rectObject, fillColor=(0, 0, 0, 0),
                       borderColor=(0, 0, 0, 255), borderThickness=1, roundCorners=0):
        image = pygame.Surface((rectObject['width'], rectObject['height']), pygame.SRCALPHA, 32)
        image = image.convert_alpha()

        rect = pygame.Rect(0, 0, rectObject['width'], rectObject['height'])
        pygame.draw.rect(image, fillColor, rect, 0, roundCorners)
        pygame.draw.rect(image, borderColor, rect, borderThickness, roundCorners)

        destImage.blit(image, (rectObject['x']+offset[0], rectObject['y']+offset[1]))

        # rect does not have an end time so just sent back a long time from now
        validUntil = sys.float_info.max
        return validUntil

    def blitRoundObject(self, destImage, offset, roundObject, fillColor=(0, 0, 0, 0),
                        borderColor=(0, 0, 0, 255), borderThickness=1):
        width = roundObject['width']
        height = roundObject['height']
        # points are drawn as small circles
        if width == 0 and height == 0:
            width = height = 3

        image = pygame.Surface((width, height), pygame.SRCALPHA, 32)
        image = image.convert_alpha()

        rect = pygame.Rect(0, 0, width, height)
        pygame.draw.ellipse(image, fillColor, rect, 0)
        pygame.draw.ellipse(image, borderColor, rect, borderThickness)

        destImage.blit(image, (roundObject['x']+offset[0], roundObject['y']+offset[1]))

        # rect does not have an end time so just sent back a long time from now
        validUntil = sys.float_info.max
        return validUntil

import pygame
from pygame.locals import *
import time
import os
import sys

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

        self.HIDELAYERS = (
            "sprites",
            "overlay",
            "inBounds",
            "outOfBounds",
            "triggers",
            "reference"
            )

        self.DEFAULTEXT = {
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
            "bgroundCorners": 0
            }

        # allocate image for each layer (exclude sprites and overlay)
        for layer in self.layers:
            if layer["name"] != "sprites" and layer["name"] != "overlay":
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
        # if there is already a valid image the don't render a new one
        if self.bottomImageValidUntil < time.perf_counter():
            # Start with grey background.
            self.bottomImage.fill((128, 128, 128, 255))

            self.bottomImageValidUntil = sys.float_info.max
            for layerNumber in range(len(self.layers)):
                if self.layers[layerNumber]["name"] == "sprites":
                    break
                if self.layers[layerNumber]["name"] in self.HIDELAYERS:
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
                        vu = self.blitLayer(self.topImage, self.layers[layerNumber])
                        if self.topImageValidUntil > vu:
                            self.topImageValidUntil = vu

        destImage.blit(self.topImage, (0, 0))
        return self.topImageValidUntil

    def blitLayer(self, destImage, layer):
        '''
        blit layer onto destImage.
        '''
        # if there is already a valid image then don't render a new one
        if layer['imageValidUntil'] < time.perf_counter():
            # Start with transparent background.
            layer['image'].fill((0, 0, 0, 0))

            if layer["type"] == "tilelayer":
                layer['imageValidUntil'] = self.blitTileGrid(layer['image'], layer["data"])
            elif layer["type"] == "objectgroup":
                layer['imageValidUntil'] = self.blitObjectList(layer['image'], layer["objects"])

        destImage.blit(layer['image'], (0, 0))
        return layer['imageValidUntil']

    def blitTileGrid(self, destImage, grid):
        validUntil = sys.float_info.max
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
        validUntil = sys.float_info.max
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
                vu = self.blitRectObject(destImage, object)

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
                    'x': tileObject['x'] + tileObject['width'] / 2 - 64,
                    'y': tileObject['y'] + tileObject['height'],
                    'width': 128,
                    'height': 40,
                    'text': {
                        'text': tileObject["properties"]["labelText"],
                        'valign': 'top',
                        'halign': 'center'
                        }
                    })
        return validUntil

    def blitTextObject(self, destImage, textObject):
        text = textObject["text"]["text"]
        maxWidth = textObject['width']

        # add text defaults if they are missing
        for k, v in self.DEFAULTEXT.items():
            if k not in textObject["text"]:
                textObject["text"][k] = v

        fontFilename = f'src/{self.game}/fonts/{textObject["text"]["fontfamily"]}.ttf'
        if not os.path.isfile(fontFilename):
            fontFilename = None
        if fontFilename:
            font = pygame.freetype.Font(fontFilename, textObject["text"]["pixelsize"])
        else:
            font = pygame.freetype.SysFont(textObject["text"]["fontfamily"], textObject["text"]["pixelsize"])

        font.strong = textObject["text"]["bold"]
        font.underline = textObject["text"]["underline"]

        font.fgcolor = pygame.Color(textObject["text"]["color"])
        # Tiled hex colors with alpha are #argb but pygame needs #rgba so now flip alpha to the end.
        if len(textObject["text"]["color"]) == 9:  # eg. "#AARRGGBB"
            font.fgcolor = pygame.Color(font.fgcolor[1], font.fgcolor[2], font.fgcolor[3], font.fgcolor[0])

        lines = []
        if textObject["text"]["wrap"]:
            words = text.split()
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
            lines.append((r.width, r.height, text))

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

        if textObject["text"]["valign"] == "top":
            destY = textObject["y"]
        elif textObject["text"]["valign"] == "center":
            destY = textObject["y"] + textObject["height"] / 2 - pixelHeight / 2
        elif textObject["text"]["valign"] == "bottom":
            destY = textObject["y"] + textObject["height"] - pixelHeight

        self.blitRectObject(destImage,{
                'x': destX - 2,
                'y': destY - 2,
                'width': pixelWidth + 4,
                'height': pixelHeight + 4
            },
            fillColor=textObject["text"]["bgcolor"],
            borderColor=textObject["text"]["bgcolor"],
            borderThickness=textObject["text"]["bgborderThickness"],
            roundCorners=textObject["text"]["bgroundCorners"])

        destImage.blit(image, (destX, destY))

        # text does not have an end time so just sent back a long time from now
        validUntil = sys.float_info.max
        return validUntil

    def blitRectObject(self, destImage, rectObject, fillColor=(0, 0, 0, 0),
                       borderColor=(0, 0, 0, 255), borderThickness=1, roundCorners=0):
        r = pygame.Rect(0, 0, rectObject['width'], rectObject['height'])

        image = pygame.Surface((rectObject['width'], rectObject['height']), pygame.SRCALPHA, 32)
        image = image.convert_alpha()

        rect = pygame.Rect(0, 0, rectObject['width'], rectObject['height'])
        pygame.draw.rect(image, fillColor, rect, 0, roundCorners)
        pygame.draw.rect(image, borderColor, rect, borderThickness, roundCorners)

        destImage.blit(image, (rectObject['x'], rectObject['y']))

        # rect does not have an end time so just sent back a long time from now
        validUntil = sys.float_info.max
        return validUntil

import pygame
import engine.time as time
import sys

import engine.log
from engine.log import log

import engine.geometry as geo
import engine.tileset


class ClientTileset(engine.tileset.Tileset):
    '''
    The ClientTileset class is responsible for:
        1) Loading tileset image so it an be used by the game engine.
        2) Provide tile render method.
    '''

    def __init__(self, tilesetFile):
        super().__init__(tilesetFile)

        # load the tileset image file
        tilesetDir = '/'.join(tilesetFile.split('/')[0:-1])
        self.image = pygame.image.load(f"{tilesetDir}/{self.imagefile}")

    def blitTile(self, tileNumber, destImage, destX, destY, tileObject=False):
        # blit tileNumber's pixels into destImage at destX, destY

        if not self.image:
            log("Tried to blit a tile when images were not loaded!", "FAILURE")
            exit()

        # check to see what the actual tileNumber is to be blited.
        tileNumber, validUntil = self.effectiveTileNumber(tileNumber, tileObject)

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

        return validUntil

    def effectiveTileNumber(self, tileNumber, tileObject=False):
        '''
        return the effective tileNumber based several criteria such as character movement and tile animations
        '''
        validUntil = sys.float_info.max  # how long the effectiveTileNumber is valid for in seconds

        # CHARACTER TILE
        # if tileObject['direction'] exists and tile tileNumber is type 'character'
        if tileObject and 'direction' in tileObject and tileNumber in self.tiles and 'type' in self.tiles[
                tileNumber] and self.tiles[tileNumber]['type'] == 'character':
            '''
            change tileNumber based on tileObject['direction'] and character tile properties
            supported properties are: any combination of:
                ('moving','stationary') combined with ('Up','Down','Left','Right')
            For example, 'movingUp'
            '''
            # if tileObject is currently moving
            if 'speed' in tileObject:
                property = 'prop-moving'
            else:
                property = 'prop-stationary'
            # add direction label to end of property, result will be something like 'stationaryLeft'.
            property = property + geo.angleLable(tileObject['direction'])

            if property in self.tiles[tileNumber]:
                tileNumber = self.tiles[tileNumber][property]

        # ANIMATED TILE
        # if tileNumber is animated then select the correct tileNumber based on time.
        if tileNumber in self.tiles and 'animation' in self.tiles[tileNumber]:
            animationTime = time.perf_counter() % self.tiles[tileNumber]["animationDuration"]
            animationTime *= 1000  # convert to ms
            for frame in self.tiles[tileNumber]['animation']:
                if frame['duration'] >= animationTime:
                    tileNumber = frame['tileid']
                    break
                animationTime -= frame['duration']

            remainingFrameTime = frame['duration'] - animationTime
            # convert remainingFrameTime to seconds and set validUntil
            validUntil = time.perf_counter() + remainingFrameTime / 1000

        return tileNumber, validUntil

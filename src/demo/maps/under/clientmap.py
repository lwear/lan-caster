import pygame
from pygame.locals import *

from engine.log import log
import demo.clientmap


class ClientMap(demo.clientmap.ClientMap):
    '''
    This class makes the map render as black except where players are standing.
    Where players are standing it is as if they are holding a lantern, brighter closer to the player.
    '''

    def __init__(self, tilesets, mapDir):
        super().__init__(tilesets, mapDir)

        self.LIGHTRADIUS = 180

        # allocate darknessImage
        self.darknessImage = pygame.Surface(
            (self.width * self.tilewidth, self.height * self.tileheight),
            pygame.SRCALPHA,
            32)
        self.darknessImage = self.darknessImage.convert_alpha()

        # allocate and draw lightCircleImage
        self.lightCircleImage = pygame.Surface((self.LIGHTRADIUS * 2, self.LIGHTRADIUS * 2), pygame.SRCALPHA, 32)
        self.lightCircleImage = self.lightCircleImage.convert_alpha()
        self.lightCircleImage.fill((0, 0, 0, 0))
        for i in range(255, 0, -5):
            pygame.draw.circle(
                self.lightCircleImage,
                color=(0, 0, 0, 255 - i),  # set the pixel values to subtract during blitMap() below.
                center=(self.LIGHTRADIUS, self.LIGHTRADIUS),
                radius=i / 255.0 * self.LIGHTRADIUS
                )

    def blitMap(self, destImage, sprites):
        # add darkness with light circles to map.

        # start with full darkness (opaque black)
        self.darknessImage.fill((0, 0, 0, 255))

        # add a lightCircle at each players location.
        players = self.findObject(objectList=sprites, type="player", returnAll=True)
        for player in players:
            # subtract the light circle pixel values from the darkness pixel values.
            self.darknessImage.blit(
                self.lightCircleImage,
                (player['anchorX'] - self.LIGHTRADIUS, player['anchorY'] - self.LIGHTRADIUS),
                special_flags=BLEND_RGBA_SUB
                )

        # render the map normally
        validUntil = super().blitMap(destImage, sprites)

        # add darknessImage on top of map rendered by super()
        destImage.blit(self.darknessImage, (0, 0))

        return validUntil

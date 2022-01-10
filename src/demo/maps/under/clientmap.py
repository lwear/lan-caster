import pygame
from pygame.locals import *

from engine.log import log
import engine.clientmap


class ClientMap(engine.clientmap.ClientMap):
    '''
    This class makes the map render as black except where players are standing.
    Where players are standing it is as if they are holding a lantern, brighter closer to the player.
    '''

    def blitMap(self, destImage, sprites, overlay):
        super().blitMap(destImage, sprites, overlay)

        # darkness will be blited on top of the map that was rendered by super() above
        darkness = pygame.Surface(
            (self.width * self.tilewidth, self.height * self.tileheight),
            pygame.SRCALPHA,
            32)
        darkness = darkness.convert_alpha()
        # start with all black with alpha of 255 (255=opaque)
        darkness.fill((0, 0, 0, 255))

        lightCircle = pygame.Surface(
            (self.width * self.tilewidth, self.height * self.tileheight),
            pygame.SRCALPHA,
            32)
        lightCircle = lightCircle.convert_alpha()

        players = self.findObject(objectList=sprites, type="player", returnAll=True)
        for player in players:
            # below subtracts the pixel values so start with all 0s (no change)
            lightCircle.fill((0, 0, 0, 0))
            for i in range(255, 0, -5):
                pygame.draw.circle(
                    lightCircle,
                    color=(0, 0, 0, 255 - i),  # set the pixel values to subtract below.
                    center=(player['anchorX'], player['anchorY']),
                    radius=i / 255.0 * 180
                    )
            # subtract the light circle pixel values from the darkness pixel values.
            darkness.blit(lightCircle, (0, 0), special_flags=BLEND_RGBA_SUB)

        destImage.blit(darkness, (0, 0))

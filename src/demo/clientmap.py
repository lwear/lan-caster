import pygame
from pygame.locals import *

from engine.log import log
import engine.clientmap

class ClientMap(engine.clientmap.ClientMap):

    def __init__(self, tilesets, mapDir, game):
        super().__init__(tilesets, mapDir, game)

        # labelText defaults that differ from DEFAULTTEXT
        self.LABELTEXT = {
            'fontfamily': "Ariel",
            'pixelsize': 12,
            "color": (0,0,0,200),
            "bgcolor": (0,0,0,0),
            "halign": "center",
            "bgbordercolor": (0,0,0,0)
            }

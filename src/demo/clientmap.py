import pygame
from pygame.locals import *

from engine.log import log
import engine.clientmap

class ClientMap(engine.clientmap.ClientMap):

    def __init__(self, tilesets, mapDir):
        super().__init__(tilesets, mapDir)

        # defaults for map text
        newDefaultText = {
            'fontfamily': "Ariel",
            'pixelsize': 16,
            "color": (0,0,0,255),
            "bgcolor": (255,255,255,128),
            "halign": "center",
            "valign": "top",
            "bgbordercolor": (0,0,0,128),
            "bgborderThickness": 3,
            "bgroundCorners": 6
            }
        for k,v in newDefaultText.items():
            self.DEFAULTTEXT[k] = v

        # labelText defaults that differ from DEFAULTTEXT
        newLabelText = {
            'pixelsize': 12,
            "color": (0,0,0,200),
            "bgcolor": (0,0,0,0),
            "bgbordercolor": (0,0,0,0)
            }
        for k,v in newLabelText.items():
            self.LABELTEXT[k] = v


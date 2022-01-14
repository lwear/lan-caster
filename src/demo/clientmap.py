import pygame
from pygame.locals import *

from engine.log import log
import engine.clientmap

class ClientMap(engine.clientmap.ClientMap):

    def __init__(self, tilesets, mapDir):
        super().__init__(tilesets, mapDir)

        # labelText defaults that differ from DEFAULTTEXT
        self.LABELTEXT = {
            'fontfamily': "Ariel",
            'pixelsize': 12,
            "color": (0,0,0,200),
            "bgcolor": (0,0,0,0),
            "halign": "center",
            "bgbordercolor": (0,0,0,0)
            }
            
        # speachText defaults that differ from DEFAULTTEXT
        self.SPEACHTEXT = {
            'fontfamily': "Ariel",
            'pixelsize': 16,
            "color": (0,0,0,255),
            "bgcolor": (255,255,255,128),
            "halign": "center",
            "valign": "bottom",
            "bgbordercolor": (0,0,0,128),
            "bgborderThickness": 3,
            "bgroundCorners": 6
            }
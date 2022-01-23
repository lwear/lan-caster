import pygame
from pygame.locals import *

from engine.log import log
import engine.client


class Client(engine.client.Client):

    '''
    The demo.Client class extends engine.Client by adding text at the start of the game to
    tell the players the goal of the game and text at the end of the game to tell players they
    have won.
    '''

    def __init__(self, args):
        super().__init__(args)

        self.MARQUEETEXT.update({
            'pixelsize': 36,
            "fontfamily": "Old London",
            "color": "#1d232b",
            "bgcolor": "#fafacd",
            "bgbordercolor": "#47361e",
            "bgborderThickness": 6,
            "bgroundCorners": 12
            })

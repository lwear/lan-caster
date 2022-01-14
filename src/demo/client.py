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

    def __init__(self, game, playerDisplayName, screenSize, fps, myIP, myPort, serverIP, serverPort):
        super().__init__(game, playerDisplayName, screenSize, fps, myIP, myPort, serverIP, serverPort)

        self.showOpeningText = True
        self.showWinText = False
        
        # actionText defaults that differ from DEFAULTTEXT
        self.ACTIONTEXT = {
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

    def msgGameWon(self, msg):
        log("Game Won!!!")
        self.showWinText = True
        self.stepChanged = True  # this will cause screen to update again.

    def updateInterface(self):
        super().updateInterface()

        # render open and ending text on top of (after) everything else.
        if self.showOpeningText:
            self.maps[self.step["mapName"]].blitTextObject(
                self.screen,
                {
                    'x': self.screen.get_width() / 4,
                    'y': self.screen.get_height() / 4 * 3,
                    'width': self.screen.get_width() / 2,
                    'height': self.screen.get_height() / 4,
                    'text': {
                        'text': "All players must gather in the stone circle to win!",
                        'pixelsize': 36,
                        'valign': "top",
                        'halign': "center",
                        "fontfamily": "Old London",
                        "color": "#1d232b",
                        "bgcolor": "#fafacd",
                        "bgbordercolor": "#47361e",
                        "bgborderThickness": 3,
                        "bgroundCorners": 6
                        }
                    })
        if self.showWinText:
            self.maps[self.step["mapName"]].blitTextObject(
                self.screen,
                {
                    'x': self.screen.get_width() / 4,
                    'y': self.screen.get_height() / 4 * 3,
                    'width': self.screen.get_width() / 2,
                    'height': self.screen.get_height() / 4,
                    'text': {
                        'text': "Game Won! Good teamwork everyone.",
                        'pixelsize': 36,
                        'valign': "top",
                        'halign': "center",
                        "fontfamily": "Old London",
                        "color": "#1d232b",
                        "bgcolor": "#fafacd",
                        "bgbordercolor": "#47361e",
                        "bgborderThickness": 3,
                        "bgroundCorners": 6
                        }
                    })

    def processEvent(self, event):
        # show the opening text until the players gives a mouse click or key press.
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            self.showOpeningText = False
        super().processEvent(event)

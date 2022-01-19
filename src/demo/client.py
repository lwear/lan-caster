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

        self.MARQUEETEXT.update({
            'pixelsize': 36,
            "fontfamily": "Old London",
            "color": "#1d232b",
            "bgcolor": "#fafacd",
            "bgbordercolor": "#47361e",
            "bgborderThickness": 6,
            "bgroundCorners": 12
            })

    def msgQuitting(self, msg):
        log("Game Won!!!")
        self.showWinText = True
        self.screenValidUntil = 0  # this will cause screen to update again.
        super().msgQuittin(msg)

    def updateInterface(self):
        super().updateInterface()

        # render open and ending text on top of (after) everything else.
        '''
        if self.showOpeningText:
            self.blitMarqueeText("All players must gather in the stone circle to win!")

        if self.showWinText:
            self.blitMarqueeText("Game Won! Good teamwork everyone.")
        '''

    def processEvent(self, event):
        # show the opening text until the players gives a mouse click or key press.
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            self.showOpeningText = False
        super().processEvent(event)

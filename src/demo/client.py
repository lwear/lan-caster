import pygame
from pygame.locals import *

from engine.log import log
import engine.textbox
import engine.client


class Client(engine.client.Client):

    '''
    The demo.Client class extends engine.Client by adding text at the start of the game to
    tell the players the goal of the game and text at the end of the game to tell players they
    have won.
    '''

    def __init__(self, game, playerDisplayName, screenSize, fps, myIP, myPort, serverIP, serverPort):
        self.showOpeningText = True
        self.showWinText = False
        super().__init__(game, playerDisplayName, screenSize, fps, myIP, myPort, serverIP, serverPort)

    def msgGameWon(self, msg):
        log("Game Won!!!")
        self.showWinText = True
        self.stepChanged = True  # this will cause screen to update again.

    def processEvent(self, event):
        # show the opening text until the players gives a mouse click or key press.
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            self.showOpeningText = False
        super().processEvent(event)

    def updateInterface(self):
        super().updateInterface()

        # render open and ending text on top of (after) everything else.
        if self.showOpeningText:
            t = engine.textbox.TextBox(
                "All players must gather in the stone circle to win!",
                maxWidth=self.screen.get_width() / 2,
                size=24
                )
            t.setXY(
                centerX=self.screen.get_width() / 2,
                topY=self.screen.get_height() / 4 * 3
                )
            t.blit(self.screen)

        if self.showWinText:
            t = engine.textbox.TextBox(
                "Game Won! Good teamwork everyone.",
                maxWidth=self.screen.get_width() / 2,
                size=24
                )
            t.setXY(
                centerX=self.screen.get_width() / 2,
                topY=self.screen.get_height() / 4 * 3
                )
            t.blit(self.screen)

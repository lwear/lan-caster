import pygame
from pygame.locals import *

from engine.log import log
import engine.text
import engine.client


class Client(engine.client.Client):

    def __init__(self, game, playerDisplayName, screenSize, fps, myIP, myPort, serverIP, serverPort):
        self.showOpeningText = True
        self.showWinText = False
        super().__init__(game, playerDisplayName, screenSize, fps, myIP, myPort, serverIP, serverPort)

    def msgGameWon(self, msg):
        log("Game Won!!!")
        self.showWinText = True
        self.stepChanged = True  # this will cause screen to update again.

    def processEvent(self, event):
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            self.showOpeningText = False
        super().processEvent(event)

    def updateInterface(self):
        super().updateInterface()

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

import pygame
from pygame.locals import *

import engine.log
from engine.log import log


class TextBox:
    """
    Generate and render centered text. If text is wider than maxWidth then it is wrapped to multiple lines.
    """
    def __init__(self, text, centerX=0, topY=0, maxWidth=255, size=18):
        self.text = text,
        self.centerX = centerX
        self.topY = topY
        self.maxWidth = maxWidth
        self.size = size

        self.pixelWidth = 0
        self.pixelHeight = 0

        self.font = pygame.freetype.Font(None, self.size)

        # first, split the text into words
        words = text.split()
        lines = []

        maxLineHeight = 0

        while len(words) > 0:
            # get as many words as will fit within allowed_width
            lineWords = words.pop(0)
            r = self.font.get_rect(lineWords)
            fw, fh = r.width, r.height
            while fw < self.maxWidth and len(words) > 0:
                r = self.font.get_rect(lineWords + ' ' + words[0])
                if r.width > maxWidth:
                    break
                lineWords = lineWords + ' ' + words.pop(0)
                fw, fh = r.width, r.height

            # add a line consisting of those words
            line = lineWords
            if self.pixelWidth < fw:
                self.pixelWidth = fw
            if maxLineHeight < fh:
                maxLineHeight = fh
            lines.append((fw, fh, line))

        self.pixelHeight = maxLineHeight * len(lines)
        self.pixelWidth += 4
        self.pixelHeight += 4
        self.image = pygame.Surface((self.pixelWidth, self.pixelHeight))
        self.image.fill(Color('black'))

        ty = 2
        for line in lines:
            tx = self.pixelWidth / 2 - line[0] / 2
            self.font.render_to(self.image, (tx, ty), line[2],
                                fgcolor=Color('green'), bgcolor=Color('black'))
            ty += maxLineHeight

    def __str__(self):
        return engine.log.objectToStr(self)

    def setXY(self, centerX, topY):
        self.centerX = centerX
        self.topY = topY

    def blit(self, image):
        image.blit(self.image, (self.centerX - self.pixelWidth / 2, self.topY))

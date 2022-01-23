import signal
import engine.time as time

import pygame
from pygame.locals import *

import engine.log
from engine.log import log

import engine.network
import engine.loaders


def quit(signal=None, frame=None):
    try:
        log(engine.client.CLIENT.socket.getStats())
    except BaseException:
        pass
    log("Quiting", "INFO")
    exit()


class Client:
    """
    The Client class is responsible for:
        1) Opening the game interface window;
        2) Requesting that the server allow the player to join the game;
        3) Collecting user input and sending it to the server over the network;
        4) Receiving updates from the server and rendering them to the screen.
    """

    #####################################################
    # INIT METHODS
    #####################################################

    def __init__(self, args):
        global CLIENT
        CLIENT = self
        signal.signal(signal.SIGINT, quit)

        self.game = args.game
        self.fps = args.fps
        self.serverIpport = engine.network.formatIpPort(args.serverIP, args.serverPort)
        self.testMode = False  # True is server is in testMode. Server provides this in joinReply message.

        # actionText defaults that differ from DEFAULTTEXT
        self.ACTIONTEXT = {
            "halign": "center",
            "valign": "bottom"
            }

        # marqueeText defaults that differ from DEFAULTTEXT
        self.MARQUEETEXT = {
            "halign": "center",
            "valign": "center"
            }

        self.playerNumber = -1  # set to a real number from the joinReply msg sent from the server
        self.step = False  # Currently displayed step. Empty until we get first step msg from server. = {}
        self.mapOffset = (0, 0)

        # Note, we must init pygame before we load tileset data.
        pygame.init()
        pygame.mixer.quit()  # Turn all sound off.
        pygame.display.set_caption(f"{self.game} - {args.playerDisplayName}")  # Set the title of the window
        self.screen = pygame.display.set_mode((args.width, args.height), pygame.RESIZABLE)  # open the window
        self.screenValidUntil = 0  # invalid and needs to be rendered.

        self.tilesets = engine.loaders.loadTilesets(
            game=self.game,
            loadImages=True  # Client needs images so it can render screen.
            )

        self.maps = engine.loaders.loadMaps(
            tilesets=self.tilesets,
            game=self.game,
            maptype="ClientMap"
            )

        log("Loading tilesets and maps was successful.")

        # Set up network, send joinRequest msg to server, and wait for joinReply to be sent back from server.
        try:
            self.socket = engine.network.Socket(
                messages=engine.loaders.loadModule("messages", game=self.game).Messages(),
                msgProcessor=self,
                sourceIP=args.myIP,
                sourcePort=args.myPort,
                destinationIP=args.serverIP,
                destinationPort=args.serverPort
                )

            reply = self.socket.sendRecvMessage({
                'type': 'joinRequest',
                'game': self.game,
                'playerDisplayName': args.playerDisplayName
                },
                retries=300, delay=1, delayMultiplier=1)

            if reply["type"] != "joinReply":
                log(f"Expected joinReply message but got {reply['type']}, quiting!", "FAILURE")
                quit()

            self.playerNumber = reply["playerNumber"]

            # set the time so client engine.time.perf_counter() will return secs in sync (very close) to server.
            time.set(reply['serverSec'])

            self.testMode = reply["testMode"]
            if(self.testMode):
                log("Server running in TEST MODE.")

        except engine.network.SocketException as e:
            log("Is server running at" + args.serverIP + ":" + str(args.serverPort) + "?")
            log(str(e), "FAILURE")
            quit()

        log("Join server was successful.")

    def __str__(self):
        return engine.log.objectToStr(self)

    ########################################################
    # Main Loop
    ########################################################

    def run(self):
        # Run the loop below once every 1/fps seconds.

        startAt = time.perf_counter()
        nextStatusAt = startAt + 10
        sleepTime = 0
        nextStepAt = startAt + (1.0 / self.fps)
        while True:
            # process messages from server (recvReplyMsgs calls msg<msgType> for each msg received)
            self.socket.recvReplyMsgs()

            # update the screen so player can see data that server sent
            self.updateScreen()

            # process any user input and send it to the server as required.
            self.processEvents()

            # busy wait (for accuracy) until next step should start.
            ptime = time.perf_counter()
            if ptime < nextStepAt:
                sleepTime += nextStepAt - ptime

                if ptime > nextStatusAt:
                    # log the amount of time we are busy vs. waiting for the next step.
                    log(f"Status: busy == {int(100-(sleepTime/(ptime-startAt)*100))}%")
                    startAt = ptime
                    nextStatusAt = startAt + 10
                    sleepTime = 0
                while ptime < nextStepAt:
                    ptime = time.perf_counter()
            else:
                log("Client running slower than " + str(self.fps) + " fps.", "VERBOSE")

            nextStepAt = ptime + (1.0 / self.fps)

    ########################################################
    # NETWORK MESSAGE PROCESSING
    ########################################################

    def msgStep(self, ip, port, ipport, msg):
        if ipport != self.serverIpport:
            log(f"Msg received but not from server! Msg from ({ipport}).", "WARNING")
            return
        self.step = msg  # store the new step
        self.screenValidUntil = 0  # flag that we need to redraw the screen.

    def msgQuitting(self, ip, port, ipport, msg):
        if ipport != self.serverIpport:
            log(f"Msg received but not from server! Msg from ({ipport}).", "WARNING")
            return
        log("Received quitting msg from server.")
        quit()

    ########################################################
    # SCREEN DRAWING
    ########################################################

    def updateScreen(self):
        # if we got a updated state from the server then render it to the screen.
        if self.step and self.screenValidUntil < time.perf_counter():
            # find the map that the server wants us to render.
            map = self.maps[self.step["mapName"]]

            # update layer visibility.
            map.setLayerVisablityMask(self.step["layerVisabilityMask"])

            # compute the offset
            self.mapOffset = self.setMapOffset(map)

            # draw the map.
            self.screenValidUntil = map.blitMap(self.screen, self.mapOffset, self.step["sprites"])

            # add on the player and gui specific items.
            self.updateInterface()

            # tell pygame to actually display changes to user.
            pygame.display.update()

    def setMapOffset(self, map):
        mapOffsetX = 0
        mapOffsetY = 0

        if map.pixelWidth < self.screen.get_width():
            mapOffsetX = round((self.screen.get_width() - map.pixelWidth) / 2)
        if map.pixelHeight < self.screen.get_height():
            mapOffsetY = round((self.screen.get_height() - map.pixelHeight) / 2)

        if map.pixelWidth > self.screen.get_width() or map.pixelHeight > self.screen.get_height():
            # find the player.
            for sprite in self.step["sprites"]:
                if "playerNumber" in sprite and self.playerNumber == sprite["playerNumber"]:
                    break

            if map.pixelWidth > self.screen.get_width():
                mapOffsetX = self.screen.get_width() / 2 - sprite["anchorX"]
                if mapOffsetX > 0:
                    mapOffsetX = 0
                if map.pixelWidth + mapOffsetX < self.screen.get_width():
                    mapOffsetX = self.screen.get_width() - map.pixelWidth

            if map.pixelHeight > self.screen.get_height():
                mapOffsetY = self.screen.get_height() / 2 - sprite["anchorY"]
                if mapOffsetY > 0:
                    mapOffsetY = 0
                if map.pixelHeight + mapOffsetY < self.screen.get_height():
                    mapOffsetY = self.screen.get_height() - map.pixelHeight

        mapOffsetX = round(mapOffsetX)
        mapOffsetY = round(mapOffsetY)
        return((mapOffsetX, mapOffsetY))

    def updateInterface(self):
        # render any non-map items, such as player specific data or gui elements.
        # these are relative to the screen, not the map. (eg bottom of screen, not bottom of map)

        if "actionText" in self.step:
            self.blitActionText(self.step["actionText"])

        if 'marqueeText' in self.step:
            self.blitMarqueeText(self.step["marqueeText"])

        if(self.testMode):
            self.blitTestText()

    def blitActionText(self, actionText):
        text = self.ACTIONTEXT.copy()
        text["text"] = actionText + " (spacebar)"
        textObject = {
            'x': 0,
            'y': 0,
            'width': self.screen.get_width(),
            'height': self.screen.get_height(),
            'text': text
            }

        # find the map that the server wants us to render.
        map = self.maps[self.step["mapName"]]
        map.blitTextObject(self.screen, (0, 0), textObject, mapRelative=False)

    def blitMarqueeText(self, marqueeText):
        text = self.MARQUEETEXT.copy()
        text["text"] = marqueeText
        textObject = {
            'x': self.screen.get_width() / 4,
            'y': self.screen.get_height() / 4,
            'width': self.screen.get_width() / 2,
            'height': self.screen.get_height() / 2,
            'text': text
            }

        # find the map that the server wants us to render.
        map = self.maps[self.step["mapName"]]
        map.blitTextObject(self.screen, (0, 0), textObject, mapRelative=False)

    def blitTestText(self):
        textObject = {
            'x': 0, 'y': 0,
            'width': self.screen.get_width(), 'height': self.screen.get_height(),
            'text': {
                'text': "TEST MODE: F1=Toggle_Player_Move_Checking F2=Jump_Map RMB=Jump_Location",
                'pixelsize': 14,
                'vlaign': 'top',
                'halign': 'center',
                "color": "#00ff00",
                "fontfamily": 'Courier New',
                "bgcolor": "#000000",
                "bgbordercolor": "#000000",
                "bgborderThickness": 0,
                "bgroundCorners": 0,
                "antialiased": True
                }
            }

        # find the map that the server wants us to render.
        map = self.maps[self.step["mapName"]]
        map.blitTextObject(self.screen, (0, 0), textObject, mapRelative=False)

    ########################################################
    # USER INPUT HANDLING
    ########################################################

    def processEvents(self):
        # process input events from user.
        for event in pygame.event.get():
            self.processEvent(event)

    def processEvent(self, event):
        if event.type == QUIT:
            quit()
        elif event.type == VIDEORESIZE:
            self.screenValidUntil = 0
        elif event.type == pygame.TEXTINPUT:
            if event.text == ' ':
                self.socket.sendMessage({'type': 'playerAction'})
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                self.socket.sendMessage({'type': 'testTogglePlayerMoveChecking'})
            elif event.key == pygame.K_F2:
                self.socket.sendMessage({'type': 'testPlayerNextMap'})
        elif event.type == pygame.MOUSEBUTTONDOWN:
            btn1, btn2, btn3 = pygame.mouse.get_pressed(num_buttons=3)
            moveDestX, moveDestY = pygame.mouse.get_pos()
            moveDestX -= self.mapOffset[0]
            moveDestY -= self.mapOffset[1]
            msgType = 'playerMove'
            if btn3:
                msgType = 'testPlayerJump'
            self.socket.sendMessage({'type': msgType, 'moveDestX': moveDestX, 'moveDestY': moveDestY})

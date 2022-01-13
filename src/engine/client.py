import signal
import time

import pygame
from pygame.locals import *

import engine.log
from engine.log import log

import engine.network
import engine.loaders


def quit(signal=None, frame=None):
    try:
        log(engine.client.CLIENT.socket.getStats())
    except:
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

    def __init__(self, game, playerDisplayName, screenSize, fps, myIP, myPort, serverIP, serverPort):
        global CLIENT
        CLIENT = self
        signal.signal(signal.SIGINT, quit)

        self.fps = fps
        self.serverIpport = engine.network.formatIpPort(serverIP, serverPort)

        self.playerNumber = -1  # set to a real number from the joinReply msg sent from the server
        self.step = False  # Currently displayed step. Empty until we get first step msg from server. = {}

        # Note, we must init pygame before we load tileset data.
        pygame.init()
        pygame.mixer.quit()  # Turn all sound off.
        pygame.display.set_caption(f"{game} - {playerDisplayName}")  # Set the title of the window
        self.screen = pygame.display.set_mode(screenSize)  # open the window
        self.screenValidUntil = 0  # invalid and needs to be rendered.

        self.tilesets = engine.loaders.loadTilesets(
            game=game,
            loadImages=True  # Client needs images so it can render screen.
            )

        self.maps = engine.loaders.loadMaps(
            tilesets=self.tilesets,
            game=game,
            maptype="ClientMap"
            )

        log("Loading tilesets and maps was successful.")

        # Set up network, send joinRequest msg to server, and wait for joinReply to be sent back from server.
        try:
            self.socket = engine.network.Socket(
                engine.loaders.loadModule("messages", game=game).Messages(),
                myIP,
                myPort,
                serverIP,
                serverPort
                )

            reply = self.socket.sendRecvMessage({
                'type': 'joinRequest',
                'game': game,
                'playerDisplayName': playerDisplayName
                },
                retries=300, delay=1, delayMultiplier=1)

            if reply["type"] != "joinReply":
                log(f"Expected joinReply message but got {reply['type']}, quiting!", "FAILURE")
                quit()
            self.playerNumber = reply["playerNumber"]
        except engine.network.SocketException as e:
            log("Is server running at" + serverIP + ":" + str(serverPort) + "?")
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
            # process messages from server (recvReplyMsgs calls processMsg once for each msg received)
            self.socket.recvReplyMsgs(self.processMsg)

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

    def processMsg(self, ip, port, ipport, msg, callbackData):
        # This method is called for each msg received.

        if ipport != self.serverIpport:
            # Msg recived was NOT from the server. Ignore this message.
            log(f"Msg received but not from server! Msg from ({ipport}).", "WARNING")
            return None

        if msg['type'] == 'step':
            self.msgStep(msg)
        elif msg['type'] == 'gameWon':
            self.msgGameWon(msg)
        elif msg['type'] == 'gameLost':
            self.msgGameLost(msg)

        return None

    def msgStep(self, msg):
        self.step = msg  # store the new step
        self.screenValidUntil = 0  # flag that we need to redraw the screen.

    def msgGameWon(self, msg):
        log("Game Won!!!")
        quit()

    def msgGameLost(self, msg):
        log("Game Lost!!!")
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

            # draw the map.
            self.screenValidUntil = map.blitMap(self.screen, self.step["sprites"], self.step["overlay"])

            # add on the player and gui specific items.
            self.updateInterface()

            # tell pygame to actually display changes to user.
            pygame.display.update()

    def updateInterface(self):
        # render any non-map items, such as player specific data or gui elements.

        # find the player of this client and render actionText if they have any.
        for sprite in self.step["sprites"]:
            if "playerNumber" in sprite and sprite["playerNumber"] == self.playerNumber:
                if "actionText" in sprite:
                    # find the map that the server wants us to render.
                    map = self.maps[self.step["mapName"]]
                    map.blitTextObject(
                        self.screen,
                        {
                            'x': 0,
                            'y': 0,
                            'width': self.screen.get_width(),
                            'height': self.screen.get_height(),
                            'valign': "bottom",
                            'text': {'text': sprite["actionText"] + " (spacebar)"}
                            })
                break

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
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.socket.sendMessage({'type': 'playerAction'})
        elif event.type == pygame.MOUSEBUTTONDOWN:
            destX, destY = pygame.mouse.get_pos()
            self.socket.sendMessage({'type': 'playerMove', 'destX': destX, 'destY': destY})

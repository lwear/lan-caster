import signal
import engine.time as time
import random
import os

from engine.log import log
import engine.log
import engine.network
import engine.loaders


def quit(signal=None, frame=None):
    try:
        log(engine.server.SERVER.socket.getStats())
    except BaseException:
        pass
    log("Quiting", "INFO")
    exit()


class Server:
    """
    The Server class is responsible for:
        1) Opening the game network interface and allow players to join the game;
        2) Initiating game logic: step forward, global game logic such as detect end game;
        3) Send updated map data to players for the map they are on;
        4) Receiving messages from players and store the data for processing by the step logic.
    """

    def __init__(self, game, fps, serverIP, serverPort):
        global SERVER
        SERVER = self
        signal.signal(signal.SIGINT, quit)
        random.seed()

        self.game = game
        self.fps = fps

        self.playerModule = engine.loaders.loadModule("player", game=self.game)
        self.players = {}  # dict of player object indexed by their ipport (eg. '192.168.3.4:20013')
        self.socket = None  # set up below

        self.tilesets = engine.loaders.loadTilesets(
            game=self.game,
            loadImages=False  # Server does not need to render images so save memory and don't load them.
            )

        self.maps = engine.loaders.loadMaps(
            tilesets=self.tilesets,
            game=self.game,
            maptype="ServerMap"
            )

        # find player starting locations. Number of locations determines how many players can play game.
        self.unassignedPlayerSprites = []  # List of player sprites that have not been assigned to any client yet.
        for m in self.maps:
            for player in self.maps[m].sprites:
                if player["type"] == "player":
                    self.unassignedPlayerSprites.append((player, self.maps[m].name))
        # ensure players are assigned random player sprites even if they join in the same order.
        random.shuffle(self.unassignedPlayerSprites)

        # set up networking
        try:
            self.socket = engine.network.Socket(
                engine.loaders.loadModule("messages", game=game).Messages(),
                serverIP,
                serverPort
                )

        except Exception as e:
            log(str(e), "FAILURE")
            quit()

    def __str__(self):
        return engine.log.objectToStr(self)

    ########################################################
    # MAIN LOOP
    ########################################################

    def run(self):
        '''
        Run the loop below once every  1/fps seconds.
        '''

        startAt = time.perf_counter()
        nextStatusAt = startAt + 10
        sleepTime = 0
        nextStepAt = startAt + (1.0 / self.fps)
        while True:
            # process messages from server (recvReplyMsgs calls processMsg once for each msg received)
            self.socket.recvReplyMsgs(self.processMsg)

            # Run the game logic to move everything forward one step
            self.stepServer()

            # Send updates to players for maps that have changed during the step
            self.sendStepMsgs()

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
                log("Server running slower than " + str(self.fps) + " fps.", "VERBOSE")

            nextStepAt = ptime + (1.0 / self.fps)

    ########################################################
    # Network Message Processing
    ########################################################

    def processMsg(self, ip, port, ipport, msg, callbackData):
        # This method is called from self.socket.recvReplyMsgs for each message received from clients.

        # process joinRequests from any ipport but other messages only from players who have joined game successfully.
        if msg['type'] == 'joinRequest':
            reply = self.msgJoinRequest(ip, port, ipport, msg)
        elif ipport in self.players:  # if this is a player who has already joined the game
            sprite = self.players[ipport].sprite
            map = self.maps[sprite["mapName"]]
            if msg['type'] == 'playerMove':
                map.setSpriteDest(sprite, msg["destX"], msg["destY"], self.players[ipport].speed)
                reply = False
            elif msg['type'] == 'playerAction':
                map.setSpriteAction(sprite)
                reply = False
            else:
                log(f"Player at {ipport} sent a message of type = {msg['type']} which can't be processed.", "WARNING")
        else:
            reply = {'type': 'Error', 'result': "Players that have not joined game may only send joinRequest msg type."}

        return reply

    def msgJoinRequest(self, ip, port, ipport, msg):
        # process joinRequest msg from client.

        # if player has already joined then just send them back OK.
        if ipport in self.players:
            result = "OK"
            log("Player at " + ipport + " sent joinRequest again.")
        elif msg["game"] != self.game:
            result = "Client and Server are not running the same game."
            log("Player at " + ipport + " tried to join wrong game.")
        else:
            if len(self.unassignedPlayerSprites) == 0:
                result = "Game is full. No more players can join."
                log("Player from " + ipport + " tried to join full game.")
            else:
                # add the client to the game.
                sprite, mapName = self.unassignedPlayerSprites.pop()
                self.players[ipport] = self.playerModule.Player(
                    sprite,
                    ip,
                    port,
                    len(self.players) + 1,
                    msg['playerDisplayName'],
                    mapName)
                result = "OK"
                log("Player from " + ipport + " joined the game.")

        if result == "OK":
            # send the new client back their player number
            return {
                'type': "joinReply", 
                'playerNumber': self.players[ipport].sprite["playerNumber"],
                'serverSec': time.perf_counter()
                }
        else:
            return {'type': 'Error', 'result': result}

    def sendStepMsgs(self):
        # For each map that is marked as changed, send a step message to all players on that map.

        for ipport in self.players:
            # find name of map player is on
            mapName = self.players[ipport].sprite["mapName"]
            if self.maps[mapName].changed:
                self.socket.sendMessage(msg={
                    'type': 'step',
                    'gameSec': time.perf_counter(),
                    'mapName': mapName,
                    'layerVisabilityMask': self.maps[mapName].getLayerVisablityMask(),
                    'sprites': self.maps[mapName].sprites,
                    'overlay': self.maps[mapName].overlay
                    },
                    destinationIP=self.players[ipport].ip,
                    destinationPort=self.players[ipport].port
                    )
        # All players have updated step msg so we can reset all the map changed flags to False
        for mapName in self.maps:
            self.maps[mapName].setMapChanged(False)

    ########################################################
    # GAME LOGIC
    ########################################################

    def stepServer(self):
        '''
        process one step that should take place over 1/fps seconds.
        '''
        self.stepServerStart()

        # Run map.stepMap() for any maps that have players on them. We do not bother
        # to process maps that do not currently contain players.

        # find mapNames that have at least one player on them.
        mapNames = []
        for ipport in self.players:
            mapNames.append(self.players[ipport].sprite["mapName"])

        # set() removes duplicates and sorted() ensures we process maps in the same order each time.
        mapNames = sorted(set(mapNames))

        # call stepMap for each map with at least one player
        for mapName in mapNames:
            self.maps[mapName].stepMap()

        self.stepServerEnd()

    def stepServerStart(self):
        '''
        perform any game logic for the start of a step that is not map specific.
        '''

        '''
        if game is won or lost then tell players and quit.
        We do this by simply checking if any player is holding
        a sprite that has type gameWon or gameLose. This assumes
        that if one player wins or loses then so do all players!

        This will normally be overwritten by the sub-class
        and there is no need to call super since this method
        is just an example and will not apply to any specific
        game.
        '''
        for ipport in self.players:
            sprite = self.players[ipport].sprite
            if "holding" in sprite and "prop-endGame" in sprite["holding"]:
                if sprite["holding"]["prop-endGame"] == "won":
                    for ipport2 in self.players:
                        self.socket.sendMessage(
                            msg={'type': 'gameWon'},
                            destinationIP=self.players[ipport2].ip,
                            destinationPort=self.players[ipport2].port
                            )
                    log("Game Won!!!")
                    quit()
                elif sprite["holding"]["prop-endGame"] == "lost":
                    for ipport2 in self.players:
                        self.socket.sendMessage(
                            msg={'type': 'gameLost'},
                            destinationIP=self.players[ipport2].ip,
                            destinationPort=self.players[ipport2].port
                            )
                    log("Game Lost!!!")
                    quit()

    def stepServerEnd(self):
        '''
        perform any game logic for the end of a step that is not map specific.
        '''
        pass

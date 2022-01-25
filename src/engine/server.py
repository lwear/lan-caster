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
        5) Receive and process test messages from players. (on with -test cmd line flag)
    """

    def __init__(self, args):
        global SERVER
        SERVER = self
        signal.signal(signal.SIGINT, quit)
        random.seed()

        self.CONNECTOR_KEEP_ALIVE = 10  # send a keepalive to connector every 10 secs until all players have joined.

        self.game = args.game
        self.registerName = args.registerName
        self.connectorHostName = args.connectorHostName
        self.connectorPort = args.connectorPort
        self.serverIP = args.serverIP
        self.serverPort = args.serverPort
        self.fps = args.fps
        self.pause = args.pause
        self.testMode = args.testMode

        self.playerMoveCheck = True

        if(self.testMode):
            log("Server running in TEST MODE.")

        self.players = {}  # dict of players indexed by their ipport (eg. '192.168.3.4:20013')
        self.playersByNum = {}  # same as above but indexed by playerNumber
        self.gameStartSec = 0  # time_perfcounter() that the game started (send in step msgs)

        # set up networking
        try:
            log(f"Server Default IP: {engine.network.getDefaultIP()}")

            if self.registerName:
                self.serverIP = '0.0.0.0'  # ignore serverIP arg if we are going to register with connector.

            self.socket = engine.network.Socket(
                messages=engine.loaders.loadModule("messages", game=self.game).Messages(),
                msgProcessor=self,
                sourceIP=self.serverIP,
                sourcePort=self.serverPort
                )
            log("Network socket created.")

            if self.registerName:
                log(f"Adding server to connector as '{self.registerName}'.")
                reply = self.socket.sendRecvMessage(
                    self.getAddServerMsg(),
                    destinationIP=self.connectorHostName,
                    destinationPort=self.connectorPort,
                    retries=10, delay=5, delayMultiplier=1)
                if reply["type"] == "serverAdded":
                    log(f"Server added to connector as {self.registerName}.")
                    self.sendAddServerAfter = time.perf_counter() + self.CONNECTOR_KEEP_ALIVE
                else:
                    log(msg["result"], "FAILURE")
                    quit()
        except Exception as e:
            if self.registerName:
                log("Is connector running?")
            log(str(e), "FAILURE")
            quit()

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
            # process messages from server (recvReplyMsgs calls msg<msgType> for each msg received)
            self.socket.recvReplyMsgs()

            # Run the game logic to move everything forward one step
            self.stepServer()

            # Send updates to players for maps that have changed during the step
            self.sendStepMsgs()

            # send keep alive messages to connector
            self.sendConnectorKeepAlive()

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

    def msgJoinRequest(self, ip, port, ipport, msg):
        # process joinRequest msg from client.

        # if player has already joined then just send them back OK.
        if ipport in self.players:
            result = "OK"
            log("Player at " + ipport + " sent joinRequest again.")
        elif msg["game"] != self.game:
            result = f"Client and Server are not running the same game: client->{msg['game']}, server->{self.game}"
            log("Player at " + ipport + " tried to join wrong game.")
        else:
            if len(self.unassignedPlayerSprites) == 0:
                result = "Game is full. No more players can join."
                log("Player from " + ipport + " tried to join full game.")
            else:
                # add the client to the game.
                self.addPlayer(ip, port, ipport, msg)
                result = "OK"

        if result == "OK":
            # if using connector and all players have joined we can delServer from connector
            if self.registerName and len(self.unassignedPlayerSprites) == 0:
                self.socket.sendMessage(
                    {
                        'type': 'delServer',
                        'serverName': self.registerName
                        },
                    destinationIP=self.connectorHostName,
                    destinationPort=self.connectorPort
                    )

            # send the new client back their player number
            return {
                'type': "joinReply",
                'playerNumber': self.players[ipport]["sprite"]["playerNumber"],
                'serverSec': time.perf_counter(),
                'testMode': self.testMode
                }
        else:
            return {'type': 'Error', 'result': "Players that have not joined game may only send joinRequest msg type."}

    def msgPlayerMove(self, ip, port, ipport, msg):
        if ipport in self.players:  # if this is a player who has already joined the game
            sprite = self.players[ipport]["sprite"]
            map = self.maps[sprite["mapName"]]
            map.setSpriteDest(sprite, msg["moveDestX"], msg["moveDestY"], self.players[ipport]["moveSpeed"])
        return False

    def msgPlayerAction(self, ip, port, ipport, msg):
        if ipport in self.players:  # if this is a player who has already joined the game
            sprite = self.players[ipport]["sprite"]
            map = self.maps[sprite["mapName"]]
            map.setSpriteAction(sprite)
        return False

    def msgTestPlayerJump(self, ip, port, ipport, msg):
        if ipport in self.players:  # if this is a player who has already joined the game
            if self.testMode:
                sprite = self.players[ipport]["sprite"]
                map = self.maps[sprite["mapName"]]
                map.setObjectLocationByAnchor(sprite, msg["moveDestX"], msg["moveDestY"])
                map.delSpriteDest(sprite)
                log(f"TEST: Player Jumped: {self.players[ipport]['sprite']['labelText']} {ipport}")

    def msgTestTogglePlayerMoveChecking(self, ip, port, ipport, msg):
        if ipport in self.players:  # if this is a player who has already joined the game
            if self.testMode:
                self.playerMoveCheck = not self.playerMoveCheck
                if self.playerMoveCheck:
                    log(f"TEST: playerMoveCheck turned ON by {self.players[ipport]['sprite']['labelText']} {ipport}")
                else:
                    log(f"TEST: playerMoveCheck turned OFF by {self.players[ipport]['sprite']['labelText']} {ipport}")

    def msgTestPlayerNextMap(self, ip, port, ipport, msg):
        if ipport in self.players:  # if this is a player who has already joined the game
            if self.testMode:
                sprite = self.players[ipport]["sprite"]
                mapNames = []
                for mapName in self.maps.keys():
                    mapNames.append(mapName)
                mapNames.sort
                destMapName = mapNames[0]
                for i in range(len(mapNames)):
                    if mapNames[i] == sprite["mapName"] and i != len(mapNames) - 1:
                        destMapName = mapNames[i + 1]
                        break
                map = self.maps[sprite["mapName"]]
                destMap = self.maps[destMapName]
                map.setObjectMap(sprite, destMap)
                if sprite["anchorX"] > map.pixelWidth or sprite["anchorY"] > map.pixelHeight:
                    destMap.setObjectLocationByAnchor(sprite, map.pixelWidth / 2, map.pixelHeight / 2)
                destMap.delSpriteDest(sprite)
                log(f"TEST: Player Changed Maps: {self.players[ipport]['sprite']['labelText']} {ipport}")

    def sendStepMsgs(self):
        # If the player has changed or map the player is on has changed then send that player a step message.
        for ipport in self.players:
            player = self.players[ipport]
            map = self.maps[player["sprite"]["mapName"]]
            if map.changed or self.getPlayerChanged(player):
                self.socket.sendMessage(
                    self.getStepMsg(player),
                    destinationIP=self.players[ipport]["ip"],
                    destinationPort=self.players[ipport]["port"]
                    )
            # reset the change detection on player.
            self.resetPlayerChanged(self.players[ipport])

        # reset the change detection on all maps
        for mapName in self.maps:
            self.maps[mapName].setMapChanged(False)

    def getStepMsg(self, player):
        map = self.maps[player["sprite"]["mapName"]]
        msg = {
            'type': 'step',
            'gameSec': time.perf_counter() - self.gameStartSec,
            'mapName': map.name,
            'layerVisabilityMask': map.getLayerVisablityMask(),
            'sprites': map.sprites
            }

        if player["actionText"]:
            msg["actionText"] = player["actionText"]

        if player["marqueeText"]:
            msg["marqueeText"] = player["marqueeText"]

        return msg

    ########################################################
    # Network Message Processing for Connector
    ########################################################

    def msgConnectInfo(self, ip, port, ipport, msg):
        # if server is using connector and server is on different LAN from client
        # then send a packet to the client. It does not matter if this packet
        # reaches the client, only that it open the server's LAN NAT so packets
        # are allowed from the client to the server.
        if self.registerName and msg["serverPublicIP"] != msg["clientPublicIP"]:
            self.socket.sendMessage(
                {'type': 'udpPunchThrough'},
                destinationIP=msg["clientPublicIP"],
                destinationPort=msg["clientPublicPort"]
                )
        # do not respond to connector
        return None

    def msgServerAdded(self, ip, port, ipport, msg):
        pass

    def msgServerDeleted(self, ip, port, ipport, msg):
        pass

    def sendConnectorKeepAlive(self):
        # if we are still waiting for players to join then
        # we need to keep udp punch through open for traffic from connector
        # we need to make sure connector does not time out our registration.
        if self.registerName and len(self.unassignedPlayerSprites) != 0:
            if self.sendAddServerAfter < time.perf_counter():
                self.socket.sendMessage(
                    self.getAddServerMsg(),
                    destinationIP=self.connectorHostName,
                    destinationPort=self.connectorPort
                    )
                self.sendAddServerAfter = time.perf_counter() + self.CONNECTOR_KEEP_ALIVE

    def getAddServerMsg(self):
        return {
            'type': 'addServer',
            'serverName': self.registerName,
            'serverPrivateIP': engine.network.getDefaultIP(),
            'serverPrivatePort': self.serverPort
            }

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
            mapNames.append(self.players[ipport]["sprite"]["mapName"])

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

    def stepServerEnd(self):
        '''
        perform any game logic for the end of a step that is not map specific.
        '''
        pass

    ########################################################
    # PLAYER
    ########################################################

    def addPlayer(self, ip, port, ipport, msg):
        # add the client to the game.
        sprite, mapName = self.unassignedPlayerSprites.pop()

        # add player data to sprite
        sprite["playerNumber"] = len(self.unassignedPlayerSprites) + 1
        sprite["mapName"] = mapName
        # add playerDisplaName to sprite as "labelText" so client can display it.
        sprite["labelText"] = msg['playerDisplayName']

        self.players[ipport] = {
            'ip': ip,
            'port': port,
            'moveSpeed': 120,  # default move speed in pixels per second.
            'sprite': sprite,
            'actionText': False,
            'lastActionText': False,
            'marqueeText': False,
            'lastMarqueeText': False
            }
        # Also add player to self.playersByNum with the playerNumber so we can look up either way.
        self.playersByNum[sprite["playerNumber"]] = self.players[ipport]

        # The sprite so the map needs to be sent to all players
        self.maps[mapName].setMapChanged()

        log(f"Player named {msg['playerDisplayName']} from {ipport} joined the game.")

    def resetPlayerChanged(self, player):
        player["lastActionText"] = player["actionText"]
        player["lastMarqueeText"] = player["marqueeText"]

    def getPlayerChanged(self, player):
        if player["lastActionText"] != player["actionText"] or player["lastMarqueeText"] != player["marqueeText"]:
            return True
        return False

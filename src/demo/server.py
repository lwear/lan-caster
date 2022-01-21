import sys
import engine.time as time
from engine.log import log
import engine.server
import engine.geometry as geo


class Server(engine.server.Server):

    def __init__(self, game, fps, serverIP, serverPort, testMode):
        super().__init__(game, fps, serverIP, serverPort, testMode)

        # server will quit after this time.
        self.quitAfter = sys.float_info.max

        self.mode = "waitingForPlayers"

    def msgPlayerMove(self, ip, port, ipport, msg):
        # ignore playerMove msgs until all players have joined game.
        if self.mode == "waitingForPlayers":
            return

        # clear start marqueeText if player has moved and game is ongoing.
        if self.mode == "gameOn":
            self.players[ipport]['marqueeText'] = False

        return super().msgPlayerMove(ip, port, ipport, msg)

    def msgPlayerAction(self, ip, port, ipport, msg):
        # ignore playerAction msgs until all players have joined game.
        if self.mode == "waitingForPlayers":
            return

        return super().msgPlayerAction(ip, port, ipport, msg)

    def addPlayer(self, ip, port, ipport, msg):
        super().addPlayer(ip, port, ipport, msg)

        if self.mode == "waitingForPlayers":
            for ipport in self.players:
                self.players[ipport]['marqueeText'] = "All players must gather in the stone circle to win."
                if len(self.unassignedPlayerSprites) == 0:
                    self.mode = "gameOn"
                    self.players[ipport]['marqueeText'] += " Game On! Click to move."
                else:
                    self.players[ipport]['marqueeText'] += f" Waiting for {len(self.unassignedPlayerSprites)} more players to join."
                    
            if self.mode == "gameOn":
                self.gameStartSec = time.perf_counter()
                log("GAME ON: All players have joined.")

    def stepServerStart(self):
        super().stepServerStart()

        # check for game won
        # if all players have joined game
        if self.mode == "gameOn":
            end = self.maps["end"]
            endGame = end.findObject(name="endGame", objectList=end.reference)
            playersIn = 0
            for ipport in self.players:
                sprite = self.players[ipport]["sprite"]
                if sprite["mapName"] == "end" and geo.objectContains(endGame, sprite["anchorX"], sprite["anchorY"]):
                    playersIn += 1
            # if all players have made it to the end.
            if playersIn == len(self.players):
                self.mode = "gameOver"
                secsToWin = round(time.perf_counter() - self.gameStartSec)
                self.quitAfter = time.perf_counter() + 30
                log("GAME OVER: Quiting in 30 seconds")
                for ipport in self.players:
                    self.players[ipport]['marqueeText'] = f"Game Won! Good teamwork everyone. You took {secsToWin} secs to win."

        # check if it is time for server to quit
        if self.quitAfter < time.perf_counter():
            log("Sending quitting msg to all clients.")
            for ipport in self.players:
                self.socket.sendMessage(
                    msg={'type': 'quitting'},
                    destinationIP=self.players[ipport]["ip"],
                    destinationPort=self.players[ipport]["port"]
                    )
            engine.server.quit()

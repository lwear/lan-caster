import sys
import engine.time as time
from engine.log import log
import engine.server
import engine.geometry as geo


class Server(engine.server.Server):

    def __init__(self, game, fps, serverIP, serverPort):
        super().__init__(game, fps, serverIP, serverPort)

        # server will quit after this time.
        self.quitAfter = sys.float_info.max

    def processMsg(self, ip, port, ipport, msg, callbackData):
        if msg["type"] == 'playerMove':
            self.players[ipport]['marqueeText'] = False

        return super().processMsg(ip, port, ipport, msg, callbackData)

    def addPlayer(self, ip, port, ipport, msg):
        super().addPlayer(ip, port, ipport, msg)
        self.players[ipport]['marqueeText'] = "All players must gather in the stone circle to win!"

    def stepServerStart(self):
        super().stepServerStart()

        # check for game won
        end = self.maps["end"]
        endGame = end.findObject(name="endGame", objectList=end.reference)
        playersIn = 0
        for ipport in self.players:
            sprite = self.players[ipport]["sprite"]
            if sprite["mapName"] == "end" and geo.objectContains(endGame, sprite["anchorX"], sprite["anchorY"]):
                playersIn += 1
        if playersIn == 3:
            self.quitAfter = time.perf_counter()+10
            for ipport in self.players:
                self.players[ipport]['marqueeText'] = "Game Won! Good teamwork everyone."

        if self.quitAfter < time.perf_counter():
            self.socket.sendMessage(
                msg={'type': 'quiting'},
                destinationIP=self.players[ipport]["ip"],
                destinationPort=self.players[ipport]["port"]
                )
            engine.server.SERVER.quit()

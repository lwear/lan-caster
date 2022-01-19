
from engine.log import log
import engine.server
import engine.geometry as geo


class Server(engine.server.Server):

    def stepServerStart(self):
        super().stepServerStart()

        end = self.maps["end"]
        endGame = end.findObject(name="endGame", objectList=end.reference)

        playersIn = 0

        for ipport in self.players:
            sprite = self.players[ipport]["sprite"]
            if sprite["mapName"] != "end" or not geo.objectContains(endGame, sprite["anchorX"], sprite["anchorY"]):
                return
            playersIn += 1

        if playersIn != 3:
            return

        for ipport in self.players:
            self.socket.sendMessage(
                msg={'type': 'quiting'},
                destinationIP=self.players[ipport]["ip"],
                destinationPort=self.players[ipport]["port"]
                )
        log("Game Won!!!")
        engine.server.quit()

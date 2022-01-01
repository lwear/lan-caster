import engine.log
from engine.log import log

import engine.server


class Player():

    def __init__(self, sprite, ip, port, playerNumber, playerDisplayName, mapName):
        self.ip = ip
        self.port = port
        self.speed = 120  # pixels per second.

        self.sprite = sprite
        self.sprite["playerNumber"] = playerNumber
        self.sprite["mapName"] = mapName

        if not "properties" in self.sprite:
            self.sprite["properties"] = {}
        self.sprite["properties"]["labelText"] = playerDisplayName

        # The changed displayName may be visible so we need to set this map to changed.
        engine.server.SERVER.maps[mapName].setMapChanged()

    def __str__(self):
        return engine.log.objectToStr(self)

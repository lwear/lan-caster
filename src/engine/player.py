import engine.log
from engine.log import log

import engine.server


class Player():
    """
    The Player class is used by the server and provides a place to store player information
    that does not need to be in the sprite and is not needed by the client. Some items, such
    as ip and port should never be shared with other clients for security and therefore can't
    be stored in the sprite since sprites are sent to all clients.
    """

    def __init__(self, sprite, ip, port, playerNumber, playerDisplayName, mapName):
        self.ip = ip
        self.port = port
        self.speed = 120  # pixels per second.

        self.sprite = sprite
        self.sprite["playerNumber"] = playerNumber
        self.sprite["mapName"] = mapName

        # add playerDisplaName to sprite as "labelText" so client can display it.
        self.sprite["labelText"] = playerDisplayName

        # The changed displayName may be visible so we need to set this map to changed.
        engine.server.SERVER.maps[mapName].setMapChanged()

    def __str__(self):
        return engine.log.objectToStr(self)

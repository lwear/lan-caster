from engine.log import log
import demo.servermap


class ServerMap(demo.servermap.ServerMap):
    '''
    This class implements the Saw and StopSaw mechanics.

    The objects in object layers have the following keys added for this subclass:
    dynamic keys (only in object while in use): stopSawDestX, stopSawDestY, stopSawSpeed
    '''

    ########################################################
    # INIT
    ########################################################

    def __init__(self, tilesets, mapDir):
        super().__init__(tilesets, mapDir)

        self.initSaws()

    ############################################################
    # STEP MAP GENERAL PROCESSING
    ############################################################

    def stepMapStart(self):
        super().stepMapStart()

        self.animateSaws()

    def stepMapEnd(self):
        self.delStopSaw()

        super().stepMapEnd()

    ########################################################
    # TRIGGER DISPATCHER
    ########################################################

    def stepProcessTrigger(self, trigger, sprite):
        if trigger['type'] == "saw":
            self.triggerSaw(trigger, sprite)
        elif trigger['type'] == "stopSaw":
            self.triggerStopSaw(trigger, sprite)
        else:
            super().stepProcessTrigger(trigger, sprite)

    ########################################################
    # TRIGGER SAW
    ########################################################

    def initSaws(self):
        '''
        Saw Mechanic init.
        copy (by reference) all tile objects with name saw from the sprite layer to the trigger layer.
        Type "saw" will act as both a sprite and a trigger! Note, when we move the sprite the trigger will
        also move.
        '''
        for saw in self.findObject(type="saw", returnAll=True):
            self.triggers.append(saw)

    def animateSaws(self):
        for saw in self.findObject(type="saw", returnAll=True):
            # if saw has stopped then reverse their direction.
            if "destX" not in saw:
                if saw["properties"]["speed"] > 0:
                    self.setObjectDest(
                        saw,
                        saw["properties"]["maxX"],
                        saw["anchorY"],
                        saw["properties"]["speed"])
                else:
                    self.setObjectDest(
                        saw,
                        saw["properties"]["minX"],
                        saw["anchorY"],
                        saw["properties"]["speed"] * -1)
                # change direction saw will go the next time is stops.
                saw["properties"]["speed"] *= -1

            # animate the spinning of the saw blade
            saw["gid"] += 1
            if saw["gid"] == self.tsFirstGid["sawtrap"] + 5:
                saw["gid"] = self.tsFirstGid["sawtrap"]

    def triggerSaw(self, trigger, sprite):
        # For a saw hitting a sprite to work, the sprite had to previously had a respawn point set.
        self.setSpriteLocationByRespawnPoint(sprite)

    ########################################################
    # TRIGGER STOP SAW
    ########################################################

    def delStopSaw(self):
        for saw in self.sprites:
            if "stopSawDestX" in saw:
                self.setObjectDest(saw, saw["stopSawDestX"], saw["stopSawDestY"], saw["stopSawSpeed"])
                del saw["stopSawDestX"]
                del saw["stopSawDestY"]
                del saw["stopSawSpeed"]

    def triggerStopSaw(self, trigger, sprite):
        saw = self.findObject(name=trigger["properties"]["sawName"])
        if "destX" in saw:
            saw["stopSawDestX"] = saw["destX"]
            saw["stopSawDestY"] = saw["destY"]
            saw["stopSawSpeed"] = saw["speed"]
            self.stopObject(saw)

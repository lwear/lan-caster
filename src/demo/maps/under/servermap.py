from engine.log import log
import demo.servermap
import engine.time as time

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

        '''
        Saw Mechanic init.
        copy (by reference) all tile objects with name saw from the sprite layer to the trigger layer.
        Type "saw" will act as both a sprite and a trigger! Note, when we move the sprite the trigger will
        also move.
        '''
        for saw in self.findObject(type="saw", returnAll=True):
            self.triggers.append(saw)

    ############################################################
    # STEP SPRITE START/END PROCESSING
    ############################################################
    def stepSpriteStart(self, sprite):
        super().stepSpriteStart(sprite)

        if sprite["type"] == "saw":
            self.animateSaw(sprite)

    def stepSpriteEnd(self, sprite):
        if sprite["type"] == "saw":
            self.delStopSaw(sprite)

        super().stepSpriteEnd(sprite)


    ########################################################
    # TRIGGER SAW
    ########################################################

    def animateSaw(self, sprite):
        # if saw has stopped then reverse direction.
        if "destX" not in sprite:
            if sprite["prop-speed"] > 0:
                self.setObjectDest(
                    sprite,
                    sprite["prop-maxX"],
                    sprite["anchorY"],
                    sprite["prop-speed"])
            else:
                self.setObjectDest(
                    sprite,
                    sprite["prop-minX"],
                    sprite["anchorY"],
                    sprite["prop-speed"] * -1)
            # change direction sprite will go the next time is stops.
            sprite["prop-speed"] *= -1

        # animate the spinning of the sprite blade
        sprite["gid"] += 1
        if sprite["gid"] == self.tsFirstGid["sawtrap"] + 5:
            sprite["gid"] = self.tsFirstGid["sawtrap"]

    def triggerSaw(self, trigger, sprite):
        # For a saw hitting a sprite to work, the sprite had to previously had a respawn point set.
        self.setSpriteLocationByRespawnPoint(sprite)
        sprite["speachText"] = "^$#$^*&$"
        sprite["speachTextValidUntil"] = time.perf_counter() + 1  # show text for only 1 sec.

    ########################################################
    # TRIGGER STOP SAW
    ########################################################

    def delStopSaw(self, sprite):
        # assume sprite is a saw
        if "stopSawDestX" in sprite:
            self.setObjectDest(sprite, sprite["stopSawDestX"], sprite["stopSawDestY"], sprite["stopSawSpeed"])
            del sprite["stopSawDestX"]
            del sprite["stopSawDestY"]
            del sprite["stopSawSpeed"]

    def triggerStopSaw(self, trigger, sprite):
        # find saw that trigger stops
        saw = self.findObject(name=trigger["prop-sawName"])
        if "destX" in saw:
            saw["stopSawDestX"] = saw["destX"]
            saw["stopSawDestY"] = saw["destY"]
            saw["stopSawSpeed"] = saw["speed"]
            self.stopObject(saw)

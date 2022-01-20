import random
from engine.log import log
import demo.servermap
import engine.time as time


class ServerMap(demo.servermap.ServerMap):
    '''
    This class implements the Saw, StopSaw, and modified spreedMultipler mechanics

    The objects in object layers have the following keys added for this subclass:
    dynamic keys (only in object while in use): stopSawDestX, stopSawDestY, stopSawSpeed
    '''

    ########################################################
    # TRIGGER SAW (uses RespawnPoint)
    ########################################################
    def initSaws(self):
        '''
        Saw Mechanic init.
        copy (by reference) all tile objects with name saw from the sprite layer to the trigger layer.
        Type "saw" will act as both a sprite and a trigger! Note, when we move the sprite the trigger will
        also move.
        '''
        for saw in self.findObject(type="saw", returnAll=True):
            if not self.checkKeys(saw, ["prop-maxX", "prop-minX", "prop-speed"]):
                log("Cannot init stepSpriteStartSaw().", "ERROR")
                saw["type"] = "sawBroken"
            else:
                self.triggers.append(saw)

    def stepSpriteStartSaw(self, sprite):
        if sprite["type"] == "saw":
            # if saw has stopped then reverse direction.
            if "moveDestX" not in sprite:
                if sprite["prop-speed"] > 0:
                    self.setSpriteDest(
                        sprite,
                        sprite["prop-maxX"],
                        sprite["anchorY"],
                        sprite["prop-speed"])
                else:
                    self.setSpriteDest(
                        sprite,
                        sprite["prop-minX"],
                        sprite["anchorY"],
                        sprite["prop-speed"] * -1)
                # change direction sprite will go the next time is stops.
                sprite["prop-speed"] *= -1

    def triggerSaw(self, trigger, sprite):
        # When hit by a saw the sprite is moved to it's last respawn point.
        # assume sprite has been through a respawn point.
        self.setSpriteLocationByRespawnPoint(sprite)

        # That saw probably hurt so they should say something.
        text = random.choice((
            "ARRRH!",
            "*&^@%", "Bad Idea!",
            "Good thing I have public health care."
            ))
        self.setSpriteSpeechText(sprite, text, time.perf_counter() + 1)  # show text for only 1 sec.

    ########################################################
    # SPEED MULTIPLIER (Add exception for saws)
    ########################################################
    def triggerSpeedMultiplier(self, trigger, sprite):
        # stops saws from having there speed changed.
        if sprite["type"] != "saw":
            super().triggerSpeedMultiplier(trigger, sprite)

    ########################################################
    # TRIGGER STOP SAW (uses Move)
    ########################################################

    def setStopSawDest(self, sprite):
        # assume sprite is a saw
        if "moveDestX" in sprite:
            sprite["stopSawDestX"] = sprite["moveDestX"]
            sprite["stopSawDestY"] = sprite["moveDestY"]
            sprite["stopSawSpeed"] = sprite["moveSpeed"]

    def delStopSawDest(self, sprite):
        # assume sprite is a saw
        if "stopSawDestX" in sprite:
            del sprite["stopSawDestX"]
            del sprite["stopSawDestY"]
            del sprite["stopSawSpeed"]

    def triggerStopSaw(self, trigger, sprite):
        # stop a saw for this step

        if not self.checkKeys(trigger, ["prop-sawName"]):
            log("Cannot process stopSaw trigger.", "ERROR")
            return

        # find saw that trigger stops
        saw = self.findObject(name=trigger["prop-sawName"])
        if "moveDestX" in saw:
            self.setStopSawDest(sprite)
            self.delSpriteDest(saw)

    def stepSpriteEndStopSaw(self, sprite):
        # if a saw was stopped for this step then restore it back to moving.
        if sprite["type"] == "saw" and "stopSawDestX" in sprite:
            self.setSpriteDest(sprite, sprite["stopSawDestX"], sprite["stopSawDestY"], sprite["stopSawSpeed"])
            self.delStopSawDest(sprite)

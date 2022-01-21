import random

import engine.time as time
from engine.log import log
import engine.geometry as geo
import engine.servermap

'''
The objects in object layers have the following keys added for this subclass:
dynamic keys (only in object while in use): normalSpeed, respawnX, respawnY, respawnMapName
'''


class ServerMap(engine.servermap.ServerMap):
    '''
    This class implements the Chicken, Throw, SpeedMultiplier (mud), Bomb, and RespawnPoint mechanics.
    '''

    ########################################################
    # BOMBAREA (uses action)
    ########################################################

    def initBomb(self):
        '''
        Bomb Mechanic init. Note, this is hard coded to the one bomb area in the game.

        Remove and store the map doors and inBounds that are covered by rocks.
        It will get put back when the bomb is set off. see actionBomb()
        '''
        if self.name == "start" or self.name == "under":
            self.bombLadder1MapDoor = self.findObject(name="ladder1MapDoor", objectList=self.triggers)
            self.removeObject(self.bombLadder1MapDoor, objectList=self.triggers)
            self.bombLadder1InBounds = self.findObject(name="ladder1InBounds", objectList=self.inBounds)
            self.removeObject(self.bombLadder1InBounds, objectList=self.inBounds)

    def triggerBombArea(self, bombArea, sprite):
        # if we are holding a bomb in a bombArea then set it off.
        '''
        this code not in generic and will only work with the one rock in this game
        for the one bomb in this game.
        '''
        if "holding" in sprite and sprite["holding"]["name"] == "bomb":
            if "action" in sprite:
                self.delSpriteAction(sprite)
                del sprite["holding"]  # remove bomb and delete it from game completely

                # find maps at top and bottom of ladder.
                start = engine.server.SERVER.maps["start"]
                under = engine.server.SERVER.maps["under"]

                # update start map to after the bomb has done off.
                start.setLayerVisablitybyName("rockOnStairs", False)
                start.setLayerVisablitybyName("rockOnStairs2", False)
                start.setLayerVisablitybyName("rockOffStairs", True)
                start.triggers.append(start.bombLadder1MapDoor)
                start.inBounds.append(start.bombLadder1InBounds)

                # update under map to after the bomb has done off.
                under.setLayerVisablitybyName("rockOnStairs", False)
                under.setLayerVisablitybyName("rockOffStairs", True)
                under.triggers.append(under.bombLadder1MapDoor)
                under.inBounds.append(under.bombLadder1InBounds)
            else:
                self.setSpriteActionText(sprite, f"Available Action: Set off {sprite['holding']['name']}.")
        elif sprite["type"] == "player":  # if sprite is a player and is not holding bomb
            # if the rock has not been blown up yet.
            start = engine.server.SERVER.maps["start"]
            if start.getLayerVisablitybyName("rockOnStairs"):
                self.setSpriteSpeechText(sprite, f"Hmmm I wonder if I could blow this up?")
            else:
                self.setSpriteSpeechText(sprite, f"That done blow up good!")

    ########################################################
    # THROWAREA (uses action)
    ########################################################

    def initThrowArea(self):
        self.THROWSPEED = 360

    def triggerThrowArea(self, throwArea, sprite):
        # if we are holding anything while in a throwArea then throw it.

        if not self.checkKeys(throwArea, ["prop-deltaX", "prop-deltaY"]):
            log("Cannot process throwArea trigger.", "ERROR")
            return

        if "holding" in sprite:
            if "action" in sprite:
                self.delSpriteAction(sprite)
                throwable = sprite["holding"]
                self.delHoldable(sprite)  # drop throwable on the ground.
                self.setSpriteDest(
                    throwable,
                    throwable["anchorX"] + throwArea["prop-deltaX"],
                    throwable["anchorY"] + throwArea["prop-deltaY"],
                    self.THROWSPEED
                    )
            else:
                self.setSpriteActionText(sprite, f"Available Action: Throw {sprite['holding']['name']}")
        elif sprite["type"] == "player":
            self.setSpriteSpeechText(sprite, f"I could throw something from here.")

    def checkMove(self, object, x, y):
        # allow things that have bee thrown to go out of bounds so they can be thrown over water.
        # The way the throw zones are set up ensures that objects can't be thrown off the map.
        if "moveSpeed" in object and object["moveSpeed"] == self.THROWSPEED:
            return True

        return super().checkMove(object, x, y)

    ########################################################
    # SPEED MULTIPLIER
    ########################################################

    def triggerSpeedMultiplier(self, trigger, sprite):
        if not self.checkKeys(trigger, ["prop-speedMultiplier"]):
            log("Cannot process speedMultiplier trigger.", "ERROR")
            return

        # if sprite is moving.
        if "moveSpeed" in sprite:
            sprite["speedMultiNormalSpeed"] = sprite["moveSpeed"]
            sprite["moveSpeed"] *= trigger["prop-speedMultiplier"]

    def stepSpriteEndSpeedMultiplier(self, sprite):
        if "speedMultiNormalSpeed" in sprite:
            if "moveSpeed" in sprite:
                sprite["moveSpeed"] = sprite["speedMultiNormalSpeed"]
            del sprite["speedMultiNormalSpeed"]

    ########################################################
    # CHICKEN
    ########################################################

    def initChichen(self):
        self.CHICKENSPEED = 10

    def stepSpriteStartChicken(self, sprite):
        if sprite["name"] == "chicken":
            # if this chicken is not being thrown right now then have it walk to closest player.
            # we know something is being thrown because it's moveSpeed will be self.THROWSPEED
            if ("moveSpeed" not in sprite or (
                    "moveSpeed" in sprite and sprite["moveSpeed"] != self.THROWSPEED)):
                player = False
                playerDistance = 0
                # find the closet player.
                for p in self.findObject(type="player", returnAll=True):
                    pDis = geo.distance(sprite["anchorX"], sprite["anchorY"], p["anchorX"], p["anchorY"])
                    if pDis < playerDistance or player == False:
                        player = p
                        playerDistance = pDis
                if player and playerDistance > 50:
                    self.setSpriteDest(sprite, player["anchorX"], player["anchorY"], self.CHICKENSPEED)
                else:
                    self.delSpriteDest(sprite)

            if random.randint(0, 5000) == 0:
                # chicken sounds from https://www.chickensandmore.com/chicken-sounds/
                text = random.choice((
                    "cluck cluck",
                    "Life is good, I'm having a good time.",
                    "Take cover I think I see a hawk!",
                    "buk, buk, buk, ba-gawk"
                    ))
                self.setSpriteSpeechText(sprite, text, time.perf_counter() + 2)

    ########################################################
    # RESPAWN POINT
    ########################################################

    def setRespawnPoint(self, sprite):
        '''
        Remember sprites location as the last safe point the sprite was at. In case the sprite
        is killed then they can be respawned back to this point.
        '''
        sprite["respawnMapName"] = sprite["mapName"]
        sprite["respawnX"] = sprite["anchorX"]
        sprite["respawnY"] = sprite["anchorY"]

    def delRespawnPoint(self, sprite):
        if "respawnMapName" in sprite:
            del sprite["respawnMapName"]
        if "respawnX" in sprite:
            del sprite["respawnX"]
        if "respawnY" in sprite:
            del sprite["respawnY"]

    def setSpriteLocationByRespawnPoint(self, sprite):
        # Move sprite to respawn point if one was previously stored.
        if "respawnX" in sprite:
            destMap = self
            if sprite["respawnMapName"] != self.name:
                destMap = engine.server.SERVER.maps[sprite["respawnMapName"]]
                self.setObjectMap(sprite, destMap)
            destMap.setObjectLocationByAnchor(sprite, sprite["respawnX"], sprite["respawnY"])
            destMap.delSpriteDest(sprite)
        else:
            # else this sprite never went through a respawn point. Perhaps it is something the player carried into over
            # the respawn area. Let's hope it's OK to leave it where it is.
            log("Tried to respawn a sprite that does not have a respawn point.", "WARNING")

    def triggerSaveRespawnPoint(self, trigger, sprite):
        self.setRespawnPoint(sprite)

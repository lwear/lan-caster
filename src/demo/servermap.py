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
    # INIT
    ########################################################

    def __init__(self, tilesets, mapDir):
        super().__init__(tilesets, mapDir)

        self.CHICKENSPEED = 10
        self.THROWSPEED = 360
        self.initBomb()

    ############################################################
    # STEP MAP START/END PROCESSING
    ############################################################

    def stepMapStart(self):
        super().stepMapStart()

    def stepMapEnd(self):
        super().stepMapEnd()

    ############################################################
    # STEP SPRITE START/END PROCESSING
    ############################################################
    def stepSpriteStart(self, sprite):
        super().stepSpriteStart(sprite)
        self.animateChicken(sprite)

    def stepSpriteEnd(self, sprite):
        self.delSpeedMultiplier(sprite)
        super().stepSpriteEnd(sprite)
        

    ########################################################
    # CHICKENS
    ########################################################

    def animateChicken(self, sprite):
        if sprite["name"] == "chicken":
            # if this chicken is not being thrown right now then have it walk to closest player.
            # we know something is being thrown because it's speed will be self.THROWSPEED
            if ("speed" not in sprite or (
                    "speed" in sprite and sprite["speed"] != self.THROWSPEED)):
                player = False
                playerDistance = 0
                # find the closet player.
                for p in self.findObject(type="player", returnAll=True):
                    pDis = geo.distance(sprite["anchorX"], sprite["anchorY"], p["anchorX"], p["anchorY"])
                    if pDis < playerDistance or player == False:
                        player = p
                        playerDistance = pDis
                if player and playerDistance > 50:
                    self.setObjectDest(sprite, player["anchorX"], player["anchorY"], self.CHICKENSPEED)
                else:
                    self.stopObject(sprite)

    ########################################################
    # TRIGGER BOMBAREA
    ########################################################

    def initBomb(self):
        '''
        Bomb Mechanic init. Note, this is hard coded to the one bomb area in the game.

        Remove and store the map doors and inBounds that are covered by rocks.
        It will get put back when the bomb is set off. see actionBomb()
        '''
        if self.name == "start" or self.name == "under":
            self.ladder1MapDoor = self.findObject(name="ladder1MapDoor", objectList=self.triggers)
            self.removeObject(self.ladder1MapDoor, objectList=self.triggers)
            self.ladder1InBounds = self.findObject(name="ladder1InBounds", objectList=self.inBounds)
            self.removeObject(self.ladder1InBounds, objectList=self.inBounds)

    def triggerBombArea(self, bombArea, sprite):
        # if we are holding a bomb in a bombArea then set it off.

        '''
        this code not in generic and will only work with the one rock in this game
        for the one bomb in this game.
        '''
        if "holding" in sprite and sprite["holding"]["name"] == "bomb":
            if "action" in sprite:
                del sprite["holding"]  # remove bomb and delete it from game completely

                # find maps at top and bottom of ladder.
                start = engine.server.SERVER.maps["start"]
                under = engine.server.SERVER.maps["under"]

                # update start map to after the bomb has done off.
                start.setLayerVisablitybyName("rockOnStairs", False)
                start.setLayerVisablitybyName("rockOnStairs2", False)
                start.setLayerVisablitybyName("rockOffStairs", True)
                start.triggers.append(start.ladder1MapDoor)
                start.inBounds.append(start.ladder1InBounds)

                # update under map to after the bomb has done off.
                under.setLayerVisablitybyName("rockOnStairs", False)
                under.setLayerVisablitybyName("rockOffStairs", True)
                under.triggers.append(under.ladder1MapDoor)
                under.inBounds.append(under.ladder1InBounds)
                self.delSpriteAction(sprite)
            elif "actionText" not in sprite:
                sprite["actionText"] = f"Available Action: Set off {sprite['holding']['name']}."
        elif sprite["type"] == "player":  # if sprite is a player and is not holding bomb
            # if the rock has not been blown up yet.
            start = engine.server.SERVER.maps["start"]
            if start.getLayerVisablitybyName("rockOnStairs"):
                sprite["speachText"] = f"Hmmm I wonder if I could blow this up?"
            else:
                sprite["speachText"] = f"That done blow up good!"

    ########################################################
    # TRIGGER THROWAREA
    ########################################################

    def triggerThrowArea(self, throwArea, sprite):
        # if we are holding anything while in a throwArea then throw it.
        if "holding" in sprite:
            if "action" in sprite:
                throwable = sprite["holding"]
                self.actionDrop(sprite)
                self.setObjectDest(
                    throwable,
                    throwable["anchorX"] + throwArea["prop-deltaX"],
                    throwable["anchorY"] + throwArea["prop-deltaY"],
                    self.THROWSPEED
                    )
                self.delSpriteAction(sprite)
            elif "actionText" not in sprite:
                sprite["actionText"] = f"Available Action: Throw {sprite['holding']['name']}"
        elif sprite["type"] == "player":
            sprite["speachText"] = f"I could throw something from here."

    ########################################################
    # TRIGGER SAVE RESPAWN POINT
    ########################################################

    def delRespawnPoint(self, object):
        if "respawnMapName" in object:
            del object["respawnMapName"]
        if "respawnX" in object:
            del object["respawnX"]
        if "respawnY" in object:
            del object["respawnY"]

    def setSpriteLocationByRespawnPoint(self, sprite):
        # Move sprite to respawn point if one was previously stored.

        if "respawnX" in sprite:
            destMap = self
            if sprite["respawnMapName"] != self.name:
                destMap = engine.server.SERVER.maps[sprite["respawnMapName"]]
                self.removeObject(sprite)
                destMap.addObject(sprite)
            destMap.setObjectLocationByAnchor(sprite, sprite["respawnX"], sprite["respawnY"])
            destMap.stopObject(sprite)
        # else this object never went through a respawn point. Perhaps it is something the player carried into over
        # the respawn area. Let's hope it's OK to leave it where it is.

    def triggerSaveRespawnPoint(self, trigger, object):
        '''
        Remember sprites location as the last safe point the sprite was at. In case the sprite
        is killed then they can be respawned back to this point.
        '''
        object["respawnMapName"] = object["mapName"]
        object["respawnX"] = object["anchorX"]
        object["respawnY"] = object["anchorY"]

    ########################################################
    # TRIGGER SPEED MULTIPLIER
    ########################################################

    def triggerSpeedMultiplier(self, trigger, sprite):
        if "speed" in sprite and sprite["type"] != "saw":
            sprite["normalSpeed"] = sprite["speed"]
            sprite["speed"] *= trigger["prop-speedMultiplier"]

    def delSpeedMultiplier(self, sprite):
        if "normalSpeed" in sprite:
            if "speed" in sprite:
                sprite["speed"] = sprite["normalSpeed"]
            del sprite["normalSpeed"]

    ########################################################
    # STEP MOVE / THROW TRIGGER
    ########################################################

    def objectInBounds(self, object, x, y):
        # allow things that have bee thrown to go out of bounds so they can be thrown over water.
        # The way the throw zones are set up ensures that objects can't be thrown off the map.
        if "speed" in object and object["speed"] == self.THROWSPEED:
            return True

        return super().objectInBounds(object, x, y)

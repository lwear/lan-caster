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
    # STEP MAP GENERAL PROCESSING
    ############################################################

    def stepMapStart(self):
        super().stepMapStart()
        self.animateChickens()

    def stepMapEnd(self):
        self.delSpeedMultiplier()
        super().stepMapEnd()

    ########################################################
    # CHICKENS
    ########################################################

    def animateChickens(self):
        for chicken in self.findObject(name="chicken", returnAll=True):
            # if this chicken is not being thrown right now then have it walk to closest player.
            # we know something is being thrown because it's speed will be self.THROWSPEED
            if ("speed" not in chicken or (
                    "speed" in chicken and chicken["speed"] != self.THROWSPEED)):
                player = False
                playerDistance = 0
                # find the closet player.
                for p in self.findObject(type="player", returnAll=True):
                    pDis = geo.distance(chicken["anchorX"], chicken["anchorY"], p["anchorX"], p["anchorY"])
                    if pDis < playerDistance or player == False:
                        player = p
                        playerDistance = pDis
                if player and playerDistance > 50:
                    self.setObjectDest(chicken, player["anchorX"], player["anchorY"], self.CHICKENSPEED)
                else:
                    self.stopObject(chicken)

    ########################################################
    # ACTION DISPATCHER
    ########################################################

    def stepAction(self, sprite):
        # if we are holding a bomb in a bombArea then set it off.
        if "action" in sprite and "holding" in sprite:
            if sprite["holding"]["name"] == "bomb":
                bombArea = self.findObject(
                    x=sprite["anchorX"],
                    y=sprite["anchorY"],
                    type="bombArea",
                    objectList=self.reference
                    )
                if bombArea:
                    self.actionBomb(sprite)
                    self.delSpriteAction(sprite)

        # if we are holding anything while in a throwArea then throw it.
        if "action" in sprite and "holding" in sprite:
            throwarea = self.findObject(
                x=sprite["anchorX"],
                y=sprite["anchorY"],
                type="throwArea",
                objectList=self.reference
                )
            if throwarea:
                self.actionThrow(sprite, throwarea)
                self.delSpriteAction(sprite)

        super().stepAction(sprite)

    ########################################################
    # ACTION BOMB
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

    def actionBomb(self, sprite):
        '''
        this code not in generic and will only work with the one rock in this game
        for the one bomb in this game.
        '''
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

    ########################################################
    # ACTION THROW
    ########################################################

    def actionThrow(self, sprite, throwarea):
        throwable = sprite["holding"]
        self.actionDrop(sprite)
        self.setObjectDest(
            throwable,
            throwable["anchorX"] + throwarea["prop-deltaX"],
            throwable["anchorY"] + throwarea["prop-deltaY"],
            self.THROWSPEED
            )

    ########################################################
    # TRIGGER DISPATCHER
    ########################################################

    def stepProcessTrigger(self, trigger, sprite):
        if trigger['type'] == "saveRespawnPoint":
            self.triggerSaveRespawnPoint(trigger, sprite)
        elif trigger['type'] == "speedMultiplier":
            self.triggerSpeedMultiplier(trigger, sprite)
        else:
            super().stepProcessTrigger(trigger, sprite)

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

    def delSpeedMultiplier(self):
        for sprite in self.sprites:
            if "normalSpeed" in sprite:
                if "speed" in sprite:
                    sprite["speed"] = sprite["normalSpeed"]
                del sprite["normalSpeed"]

    def triggerSpeedMultiplier(self, trigger, sprite):
        if "speed" in sprite and sprite["type"] != "saw":
            sprite["normalSpeed"] = sprite["speed"]
            sprite["speed"] *= trigger["prop-speedMultiplier"]

    ########################################################
    # STEP MOVE
    ########################################################

    def objectInBounds(self, object, x, y):
        # allow things that have bee thrown to go out of bounds so they can be thrown over water.
        # The way the throw zones are set up ensures that objects can't be thrown off the map.
        if "speed" in object and object["speed"] == self.THROWSPEED:
            return True

        return super().objectInBounds(object, x, y)

    ########################################################
    # SPEACHTEXT
    ########################################################

    def stepSpeachText(self, sprite):
        # these speach texts are only for players to say (not things like chickens, or keys)
        if sprite["type"] == "player":
            if "holding" not in sprite or sprite['holding']['name'] != "bomb":
                    bombArea = self.findObject(
                        x=sprite["anchorX"],
                        y=sprite["anchorY"],
                        type="bombArea",
                        objectList=self.reference
                        )
                    if bombArea:
                        # if the rock has not been blown up yet.
                        start = engine.server.SERVER.maps["start"]
                        if start.getLayerVisablitybyName("rockOnStairs"):
                            sprite["speachText"] = f"Hmmm I wonder if I could blow this up?"
                        else:
                            sprite["speachText"] = f"That done blow up good!"
                        return

            if "holding" not in sprite:
                throwarea = self.findObject(
                    x=sprite["anchorX"],
                    y=sprite["anchorY"],
                    type="throwArea",
                    objectList=self.reference
                    )
                if throwarea:
                    sprite["speachText"] = f"I could throw something from here."
                    return

        super().stepSpeachText(sprite)

    ########################################################
    # ACTIONTEXT
    ########################################################

    def stepActionText(self, sprite):
        if sprite["type"] != "player":
            return  # only players can see their action text.

        if "holding" in sprite:
            if sprite["holding"]["name"] == "bomb":
                bombArea = self.findObject(
                    x=sprite["anchorX"],
                    y=sprite["anchorY"],
                    type="bombArea",
                    objectList=self.reference
                    )
                if bombArea:
                    sprite["actionText"] = f"Available Action: Set off {sprite['holding']['name']}."
                    return

            throwarea = self.findObject(
                x=sprite["anchorX"],
                y=sprite["anchorY"],
                type="throwArea",
                objectList=self.reference
                )
            if throwarea:
                sprite["actionText"] = f"Available Action: Throw {sprite['holding']['name']}"
                return

        super().stepActionText(sprite)

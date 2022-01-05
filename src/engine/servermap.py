from engine.log import log
import engine.map
import engine.geometry as geo

import engine.server


class ServerMap(engine.map.Map):
    '''
    The objects in object layers have the following keys added for this subclass:
    dynamic keys (only in object while in use): action, actionText, holding

    Sample Sprite Object with added 'action', 'actionText', 'holding', and 'text'
    {
      o 'action' = True
      o 'actionText': 'Available Action: Drop book',
        'anchorX': 260.2614907044467,
        'anchorY': 394.0083806621534,
        'destX': 255,
        'destY': 394,
        'gid': 151,
        'height': 32,
      o 'holding': {
            'anchorX': 558.91942244993,
            'anchorY': 395.714951094551,
            'gid': 53,
            'height': 32,
            'mapName': 'actions',
            'name': 'book',
            'tilesetName': 'fantasy-tileset',
            'tilesetTileNumber': 52,
            'type': 'holdable',
            'width': 32,
            'x': 542.91942244993,
            'y': 379.714951094551
        },
        'mapName': 'actions',
        'name': '',
        'playerNumber': 1,
        'properties': {'labelText': 'Bob'},
        'speed': 120,
      o 'text': {
            'color': '#00ff00',
            'pixelsize': 16,
            'text': "The door is locked."
        },
        'tilesetName': 'fantasy-tileset',
        'tilesetTileNumber': 150,
        'type': 'player',
        'width': 32,
        'x': 244.26149070444671,
        'y': 378.0083806621534
    }
    '''

    ########################################################
    # STEP DISPATCHER (Order of steps matters!)
    ########################################################

    def step(self):
        self.stepStart()
        self.stepSprites()
        self.stepEnd()

    def stepSprites(self):
        for sprite in self.sprites:
            self.stepAction(sprite)
        for sprite in self.sprites:
            self.stepTrigger(sprite)
        for sprite in self.sprites:
            self.stepMove(sprite)
        for sprite in self.sprites:
            self.stepActionText(sprite)

    ############################################################
    # STEP MAP GENERAL PROCESSING
    ############################################################
    def stepStart(self):
        self.delPopUpText()

    def stepEnd(self):
        pass

    ########################################################
    # ACTION DISPATCHER
    ########################################################
    def setSpriteAction(self, sprite):
        sprite["action"] = True

    def delSpriteAction(self, sprite):
        del sprite["action"]

    def stepAction(self, sprite):

        # order of action priority needs to be: pickup, use, drop.

        if "action" in sprite and "holding" not in sprite:
            holdable = self.findObject(x=sprite["anchorX"], y=sprite["anchorY"], type="holdable", exclude=sprite)
            if holdable:
                self.actionPickUp(sprite, holdable)
                self.delSpriteAction(sprite)

        if "action" in sprite:
            useable = self.findObject(x=sprite["anchorX"], y=sprite["anchorY"], type="useable", exclude=sprite)
            if useable:
                self.actionUse(sprite, useable)
                self.delSpriteAction(sprite)

        if "action" in sprite and "holding" in sprite:
            self.actionDrop(sprite)
            self.delSpriteAction(sprite)

        if "action" in sprite:
            self.delSpriteAction(sprite)

    ########################################################
    # ACTION - DROP
    ########################################################

    def actionPickUp(self, sprite, holdable):
        self.removeObject(holdable)
        sprite["holding"] = holdable

    ########################################################
    # ACTION USE - MapDoor
    ########################################################

    def actionUse(self, sprite, useable):
        '''
        simple example that let's an object of type useable act as a
        mapdoor assuming it has same properties as a mapdoor.
        '''
        if "properties" in useable and "trigger" in useable["properties"]:
            if useable["properties"]["trigger"] == "mapDoor":
                self.triggerMapDoor(useable, sprite)  # assume usable has the properties required by a mapDoor trigger

    ########################################################
    # ACTION DROP
    ########################################################

    def actionDrop(self, sprite):
        # Assumes sprite is holding something
        dropping = sprite["holding"]
        del sprite["holding"]

        # put the dropped item at the feet of the sprite that was holding it.
        self.setObjectLocationByAnchor(dropping, sprite["anchorX"], sprite["anchorY"])
        self.stopObject(dropping)
        self.addObject(dropping)

    ########################################################
    # ACTIONTEXT
    ########################################################

    def stepActionText(self, sprite):
        # order of action priority is always: pickup, use, drop.

        if sprite["type"] != "player":
            return  # only players can see their action text.

        holdable = self.findObject(x=sprite["anchorX"], y=sprite["anchorY"], type="holdable", exclude=sprite)
        useable = self.findObject(x=sprite["anchorX"], y=sprite["anchorY"], type="useable", exclude=sprite)

        if "actionText" in sprite:
            old = sprite["actionText"]
        else:
            old = False

        if holdable and not "holding" in sprite:
            sprite["actionText"] = f"Available Action: Pick Up {holdable['name']}"
        elif useable:
            sprite["actionText"] = f"Available Action: Use {useable['name']}"
        elif "holding" in sprite:
            sprite["actionText"] = f"Available Action: Drop {sprite['holding']['name']}"
        elif "actionText" in sprite:
            del sprite["actionText"]

        if "actionText" in sprite:
            new = sprite["actionText"]
        else:
            new = False

        if new != old:
            self.setMapChanged()

    ########################################################
    # STEP MOVE
    ########################################################

    def setObjectDest(self, object, destX, destY, speed):
        object["destX"] = destX
        object["destY"] = destY
        object["speed"] = speed

    def stopObject(self, object):
        if "destX" in object:
            del object["destX"]
        if "destY" in object:
            del object["destY"]
        if "speed" in object:
            del object["speed"]

    def objectInBounds(self, object, x=False, y=False):
        '''
        return True if object's anchor point is inbounds considering the map size, inBounds layer, and
        outOfBounds layer; else return False. If x and y are provided then they are used instead of the
        object anchor. This is useful to test if an object would be inbounds before setting it to a
        new location.

        Priority of evaluation is as follows:
        1) if object is not on the map then it is NOT inbounds.
        2) if object is inside an object on the inBounds layer then it IS inbounds.
        3) if object is inside an object on the outOfBounds layer then it is NOT inbounds.
        4) else it IS inbounds.

        '''
        if x == False:
            x = object["anchorX"]
        if y == False:
            y = object["anchorY"]
        if geo.objectContains({"x": 0, "y": 0, "width": self.pixelWidth, "height": self.pixelHeight}, x, y) and \
                (geo.objectsContains(self.inBounds, x, y) or (not geo.objectsContains(self.outOfBounds, x, y))):
            return True
        return False

    def stepMove(self, sprite):
        # Move within this map while respecting inBounds and outOfBounds
        if "destX" in sprite and "destY" in sprite and "speed" in sprite:
            stepSpeed = sprite["speed"] / engine.server.SERVER.fps  # convert pixels per second to pixels per step
            # compute a new anchor x,y which moves directly towards destination
            newAnchorX, newAnchorY = geo.project(
                sprite["anchorX"],
                sprite["anchorY"],
                geo.angle(sprite["anchorX"], sprite["anchorY"], sprite["destX"], sprite["destY"]),
                stepSpeed
                )

            # movement is only allowed if it is inbounds.
            inBounds = False
            # if sprite can move directly towards destination
            if self.objectInBounds(sprite, newAnchorX, newAnchorY):
                inBounds = True
            # elif sprite is moving along X then try to stay at the same Y and move along only along X
            elif newAnchorX != sprite["anchorX"] and self.objectInBounds(sprite, newAnchorX, sprite["anchorY"]):
                newAnchorY = sprite["anchorY"]
                inBounds = True
            # elif sprite is moving along Y then try to stay at the same X and move along only along Y
            elif newAnchorY != sprite["anchorY"] and self.objectInBounds(sprite, sprite["anchorX"], newAnchorY):
                newAnchorX = sprite["anchorX"]
                inBounds = True

            if inBounds:
                # move sprite to new location
                self.setObjectLocationByAnchor(sprite, newAnchorX, newAnchorY)

                # stop sprite if we are close to destination
                if geo.distance(sprite["anchorX"], sprite["anchorY"], sprite["destX"], sprite["destY"]) < stepSpeed:
                    self.stopObject(sprite)
            else:
                # sprite has hit an inside corner and can't continue.
                self.stopObject(sprite)

    ########################################################
    # TRIGGER DISPATCHER
    ########################################################

    def stepTrigger(self, sprite):
        # find all triggers that contain this sprites anchor and process each one.
        triggers = self.findObject(
            x=sprite["anchorX"],
            y=sprite["anchorY"],
            objectList=self.triggers,
            returnAll=True,
            exclude=sprite)
        for trigger in triggers:
            self.stepProcessTrigger(trigger, sprite)

    def stepProcessTrigger(self, trigger, sprite):
        if trigger['type'] == "mapDoor":
            self.triggerMapDoor(trigger, sprite)
        elif trigger['type'] == "popUpText":
            self.triggerPopUpText(trigger, sprite)

    ########################################################
    # TRIGGER MAPDOOR
    ########################################################

    def triggerMapDoor(self, trigger, sprite):
        # find destX, destY based on object named trigger["properties"]["destReference"] on
        # layer "reference" of map trigger["properties"]["destMapName"]

        destMap = engine.server.SERVER.maps[trigger["properties"]["destMapName"]]
        dest = self.findObject(name=trigger["properties"]["destReference"], objectList=destMap.reference)
        if dest:
            self.removeObject(sprite)
            destMap.setObjectLocationByAnchor(sprite, dest["anchorX"], dest["anchorY"])
            destMap.stopObject(sprite)
            destMap.addObject(sprite)

    ########################################################
    # TRIGGER POPUPTEXT
    ########################################################

    def delPopUpText(self):
        # popUpText only lasts one step so it's to be added every step to be seen by player.
        # Remove all popUpText. It will get added in the triggers below. see triggerPopUpText()
        for popUpText in self.findObject(type="popUpText", objectList=self.overlay, returnAll=True):
            self.removeObject(popUpText, objectList=self.overlay)

    def triggerPopUpText(self, trigger, sprite):
        # find destX, destY based on object named trigger["properties"]["destReference"] on
        # layer"reference"

        if sprite["type"] != "player":
            return  # only players can trigger pop up text.

        dest = self.findObject(name=trigger["properties"]["textReference"], objectList=self.reference)
        if dest:
            if "textColor" not in trigger["properties"]:
                trigger["properties"]["textColor"] = "#00ff00"

            if "textSize" not in trigger["properties"]:
                trigger["properties"]["textSize"] = 16

            popUpText = self.checkObject(
                {
                    "height": dest["height"],
                    "text":
                        {
                            "color": trigger["properties"]["textColor"],
                            "pixelsize": trigger["properties"]["textSize"],
                            "text": trigger["properties"]["text"]
                            },
                    "type": "popUpText",
                    "width": dest["width"],
                    "x": dest["x"],
                    "y": dest["y"]
                    })

            self.addObject(popUpText, objectList=self.overlay)
        else:
            log(f'Could not find name=f{trigger["properties"]["textReference"]} on reference layer.', "WARNING")

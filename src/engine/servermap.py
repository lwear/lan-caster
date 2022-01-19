from engine.log import log
import engine.map
import engine.geometry as geo
import engine.time as time
import engine.stepmap
import engine.server


class ServerMap(engine.stepmap.StepMap):
    '''
    The ServerMap class is responsible for implementing several basic game mechanics.
    '''

    ########################################################
    # MECHANIC TEMPLATE
    ########################################################
    '''

    def initName():
        pass

    def stepMapStartName():
        pass

    def stepSpriteStartName(sprite):
        pass

    def triggerName(sprite):
        # called when an object on the trigger layer with type="name" is triggered by a sprite entering it's rect.
        pass

    def stepMoveName(sprite):
        pass

    def stepSpriteEndName(sprite):
        pass

    def stepMapEndName():
        pass
    '''

    ########################################################
    # STEP MOVE
    ########################################################

    def setSpriteDest(self, sprite, moveDestX, moveDestY, moveSpeed):
        # flag a sprite as wanting to move to a new location at a specific moveSpeed.
        # Normally set in a player sprite after the server receives a playerMove message from the client.
        sprite["moveDestX"] = moveDestX
        sprite["moveDestY"] = moveDestY
        sprite["moveSpeed"] = moveSpeed

    def delSpriteDest(self, sprite):
        # stop a sprite from moving
        if "moveDestX" in sprite:
            del sprite["moveDestX"]
        if "moveDestY" in sprite:
            del sprite["moveDestY"]
        if "moveSpeed" in sprite:
            del sprite["moveSpeed"]

    def stepMove(self, sprite):
        # Move sprite within this map while respecting inBounds and outOfBounds

        # if sprite is moving
        if "moveDestX" in sprite and "moveDestY" in sprite and "moveSpeed" in sprite:

            # convert pixels per second to pixels per step
            stepSpeed = sprite["moveSpeed"] / engine.server.SERVER.fps

            # compute a new angle in radians which moves directly towards destination
            # sprite["direction"] is stored and never removed so client will know the last
            # direction the sprite was facing.
            sprite["direction"] = geo.angle(
                sprite["anchorX"],
                sprite["anchorY"],
                sprite["moveDestX"],
                sprite["moveDestY"])

            # compute a new anchor x,y which moves directly towards destination for this step
            newAnchorX, newAnchorY = geo.project(
                sprite["anchorX"],
                sprite["anchorY"],
                sprite["direction"],
                stepSpeed
                )

            # movement is only allowed if it is inbounds.
            inBounds = False

            # if sprite can move directly towards destination
            if self.checkMove(sprite, newAnchorX, newAnchorY):
                inBounds = True
            # elif sprite is moving along X then try to stay at the same Y and move along only along X
            elif newAnchorX != sprite["anchorX"] and self.checkMove(sprite, newAnchorX, sprite["anchorY"]):
                newAnchorY = sprite["anchorY"]
                inBounds = True
            # elif sprite is moving along Y then try to stay at the same X and move along only along Y
            elif newAnchorY != sprite["anchorY"] and self.checkMove(sprite, sprite["anchorX"], newAnchorY):
                newAnchorX = sprite["anchorX"]
                inBounds = True

            if inBounds:
                if geo.distance(sprite["anchorX"], sprite["anchorY"], newAnchorX, newAnchorY) < 0.1:
                    # if sprite is only going to move less than 0.1 pixel then stop it.
                    self.delSpriteDest(sprite)
                elif geo.distance(newAnchorX, newAnchorY, sprite["moveDestX"], sprite["moveDestY"]) < stepSpeed:
                    # if sprite is close to destination then stop it.
                    self.delSpriteDest(sprite)

                # move sprite to new location
                self.setObjectLocationByAnchor(sprite, newAnchorX, newAnchorY)
            else:
                # sprite cannot move.
                self.delSpriteDest(sprite)

    def checkMove(self, object, x, y):
        '''
        return True if object's anchor point is inbounds considering the map size, inBounds layer, and
        outOfBounds layer; else return False.

        If x and y are provided then they are used instead of the object anchor. This is useful to test
        if an object would be inbounds before setting it to a new location.

        Priority of evaluation is as follows:
        1) if object is not on the map then it is NOT inbounds.
        2) if object is inside an object on the inBounds layer then it IS inbounds.
        3) if object is inside an object on the outOfBounds layer then it is NOT inbounds.
        4) else it IS inbounds.

        '''
        if geo.objectContains({"x": 0, "y": 0, "width": self.pixelWidth, "height": self.pixelHeight}, x, y) and \
                (geo.objectsContains(self.inBounds, x, y) or (not geo.objectsContains(self.outOfBounds, x, y))):
            return True
        return False

    ########################################################
    # MAPDOOR
    ########################################################

    def initMapDoor(self):
        self.addStepMethodPriority("trigger", "triggerMapDoor", 1)

    def triggerMapDoor(self, trigger, sprite):
        # Move sprite based on trigger. This may include moving to a new map.

        if not self.checkKeys(trigger, ("prop-destMapName", "prop-destReference")):
            log("Cannot process mapDoor trigger.", "ERROR")
            return

        # find destination based on object named trigger["prop-destReference"] on
        # layer "reference" of map trigger["prop-destMapName"]
        destMap = engine.server.SERVER.maps[trigger["prop-destMapName"]]
        dest = self.findObject(name=trigger["prop-destReference"], objectList=destMap.reference)
        if dest:
            self.removeObject(sprite)
            destMap.setObjectLocationByAnchor(sprite, dest["anchorX"], dest["anchorY"])
            destMap.delSpriteDest(sprite)
            destMap.addObject(sprite)
            return True  # stop the processing of other triggers since sprite has moved.
        else:
            log(
                f'Trigger destination not found = {trigger["prop-destMapName"]} - {trigger["prop-destReference"]}',
                "ERROR")

    ########################################################
    # Holdable (uses action)
    ########################################################

    def setHoldable(self, holdable, sprite):
        # sprite picks up holdable
        self.removeObject(holdable, objectList=self.sprites)
        self.removeObject(holdable, objectList=self.triggers)
        sprite["holding"] = holdable

    def delHoldable(self, sprite):
        # delete holdable from sprite and "drop" holdable in same location as sprite.
        dropping = sprite["holding"]
        del sprite["holding"]

        # put the dropped item at the feet of the sprite that was holding it.
        self.setObjectLocationByAnchor(dropping, sprite["anchorX"], sprite["anchorY"])
        self.delSpriteDest(dropping)
        self.addObject(dropping, objectList=self.sprites)
        # add holdable type object back as a trigger so it can be picked up again.
        self.addObject(dropping, objectList=self.triggers)

    def initHoldable(self):
        # holdable sprites need to be triggers so things can
        # be done when another sprite interacts with them.
        # copy (by refernece) sprites to triggers
        for holdable in self.findObject(type="holdable", returnAll=True):
            self.addObject(holdable, objectList=self.triggers)

        self.addStepMethodPriority("trigger", "triggerHoldable", 10)
        self.addStepMethodPriority("stepSpriteEnd", "stepSpriteEndHoldable", 89)

    def triggerHoldable(self, holdable, sprite):
        if "holding" not in sprite:
            if "action" in sprite:
                self.delSpriteAction(sprite)
                self.setHoldable(holdable, sprite)
            else:
                self.setSpriteActionText(sprite, f"Available Action: Pick Up {holdable['name']}")

    def stepSpriteEndHoldable(self, sprite):
        # dropping is not triggered. It only requires an unused action request so it needs to be checked for
        # during end of step sprite processing, after all triggers have had a chance to see that an action is requested.
        if "holding" in sprite:
            if "action" in sprite:
                self.delSpriteAction(sprite)
                self.delHoldable(sprite)
            else:
                self.setSpriteActionText(sprite, f"Available Action: Drop {sprite['holding']['name']}")

    ########################################################
    # Portkey (uses action, and mapdoor)
    ########################################################

    '''
    A portkey is a map door that is a visable sprite and requires the player to request an action before
    they will go through the mapDoor.
    '''

    def initPortkey(self):
        # portkey sprites need to be triggers so things can
        # be done when another sprite interacts with them.
        # copy (by refernece) sprites to triggers
        for portkey in self.findObject(type="portkey", returnAll=True):
            self.addObject(portkey, objectList=self.triggers)

    def triggerPortkey(self, portkey, sprite):
        '''
        Portkey acts as a mapdoor but also requires a user to request an action.
        Requires the same properties as a mapdoor.
        '''
        if "action" in sprite:
            self.delSpriteAction(sprite)
            self.triggerMapDoor(portkey, sprite)  # assume portkey has the properties required by a mapDoor trigger
        else:
            self.setSpriteActionText(sprite, f"Available Action: Touch {portkey['name']}")

    ########################################################
    # GENERAL ACTION HANDLING
    ########################################################

    def initDelAction(self):
        self.addStepMethodPriority("stepSpriteEnd", "stepSpriteEndDelAction", 90)

    def setSpriteAction(self, sprite):
        # flag a sprite as waiting to perform an action.
        # Normally set in a player sprite after the server receives an playerAction message from client.
        sprite["action"] = True

    def delSpriteAction(self, sprite):
        # clear sprite flag from sprite.
        if "action" in sprite:
            del sprite["action"]

    def stepSpriteEndDelAction(self, sprite):
        # if an action was requested by no possible action was found during the step then just delete it.
        self.delSpriteAction(sprite)

    ########################################################
    # ACTION TEXT
    ########################################################

    def setSpriteActionText(self, sprite, actionText):
        # only allow setting actionText if something else has not already done so this step.
        if sprite["type"] == "player" and "playerNumber" in sprite:
            player = engine.server.SERVER.playersByNum[sprite["playerNumber"]]
            if not player["actionText"]:
                player["actionText"] = actionText

    def delSpriteActionText(self, sprite):
        if sprite["type"] == "player" and "playerNumber" in sprite:
            player = engine.server.SERVER.playersByNum[sprite["playerNumber"]]
            if "actionText" in player:
                player["actionText"] = False

    def stepSpriteStartDelActionText(self, sprite):
        # delete actionText at the start of a step. It will be set again during the step if an action is available.
        self.delSpriteActionText(sprite)

    ########################################################
    # SPEECH TEXT
    ########################################################

    def setSpriteSpeechText(self, sprite, speechText, speechTextDelAfter=0):
        old = sprite["speechText"]
        self.delSpriteSpeechText(sprite)
        sprite["speechText"] = speechText
        if speechTextDelAfter > 0:
            sprite["speechTextDelAfter"] = speechTextDelAfter
        if old != sprite["speechText"]:
            self.setMapChanged()

    def delSpriteSpeechText(self, sprite):
        if "speechText" in sprite:
            del sprite["speechText"]
        if "speechTextDelAfter" in sprite:
            del sprite["speechTextDelAfter"]

    def stepSpriteStartSpeechTextTimers(self, sprite):
        if "speechTextDelAfter" not in sprite or (
                "speechTextDelAfter" in sprite and sprite["speechTextDelAfter"] < time.perf_counter()):
            self.delSpriteSpeechText(sprite)

    ########################################################
    # LAYER (showAfter/hideAfter) TIMERS
    ########################################################

    def setLayerShowAfter(self, layer, showAfter=0):
        layer["showAfter"] = showAfter

    def delLayerShowAfter(self, layer):
        del layer["showAfter"]

    def setLayerHideAfter(self, layer, hideAfter=0):
        layer["hideAfter"] = hideAfter

    def delLayerHideAfter(self, layer):
        del layer["hideAfter"]

    def initLayerTimers(self):
        self.addStepMethodPriority("stepMapStart", "stepMapStartLayerTimers", 10)

    def stepMapStartLayerTimers(self):
        # Set visibility to true/false for any layers with expired "hideAfter"/"showAfter".
        currentTime = time.perf_counter()
        for layer in self.layers:
            if "hideAfter" in layer and layer["hideAfter"] < currentTime:
                # hide the layer
                self.setLayerVisablitybyName(layer["name"], False)
                self.delLayerHideAfter(layer)
            if "showAfter" in layer and layer["showAfter"] < currentTime:
                # show the layer
                self.setLayerVisablitybyName(layer["name"], True)
                self.delLayerShowAfter(layer)

    ########################################################
    # OBJECT (delAfter) TIMERS
    ########################################################

    def setObjectDelAfter(self, object, delAfter=0):
        if delAfter > 0:
            object["delAfter"] = delAfter
        else:
            self.delObjectDelAfter(object)

    def delObjectDelAfter(self, object):
        del object["delAfter"]

    def initObjectTimers(self):
        self.addStepMethodPriority("stepMapStart", "stepMapStartObjectTimers", 10)

    def stepMapStartObjectTimers(self):
        currentTime = time.perf_counter()
        for layer in self.layers:
            if layer["type"] == "objectgroup":
                for object in layer['objects']:
                    # del any objects on object layers that have expired "delAfter".
                    if "delAfter" in object and object["delAfter"] > currentTime:
                        # remove expired object
                        self.removeObject(object, objectList=layer["objects"])

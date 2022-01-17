from engine.log import log
import engine.map
import engine.geometry as geo
import engine.time as time

import engine.server


class ServerMap(engine.map.Map):
    '''
    The ServerMap class is responsible for:
        1) Implementing the game logic of "stepping" the map forward in time.
        2) Implement several basic game mechanics that occur within a step.

    This class implements the Pick Up, Use, Drop, Move, Map Door, ActionText, and PopUpText mechanics.

    The objects in object layers have the following keys added for this subclass:
        - Required keys (always present): no added keys
        - Dynamic keys (only in object while in use): action, actionText, holding, destX, destY, speed
        - Text objects also have required keys: text

    Sample Sprite Object with added 'action', 'actionText', 'holding', 'text', destX, destY, speed, direction
    {
      o 'action' = True
      o 'actionText': 'Available Action: Drop book',
      o 'destX': 255,
      o 'destY': 394,
      o 'direction': 2.346,
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
      o 'speed': 120,
      o 'text': {
            'color': '#00ff00',
            'pixelsize': 16,
            'text': "The door is locked."
        },
        ...
        ...
        ...
        < see other keys already in engine.map,Map >
        ...
        ...
        ...
    }

    o Optional keys are only present when in use. If not sure then check before use.
      eg. if 'gid' in sprite:
            do something with sprite['gid']
    '''

    def __init__(self, tilesets, mapDir):
        super().__init__(tilesets, mapDir)

        '''
        some trigger types must be processed before others for a given sprite
        lower number triggers will be processed before higher number triggers.
        '''
        '''
        If an action has been requested then see if an action can be run.
        Perform at most one action and then clear the action request.
        Order of action priority is: pickup, use, drop.
        If an action has been requested but none is available then just clear the action flag.
        '''
        self.TRIGGER_PRIORITY = {
            'mapDoor': 1,  # do map door first since player may move and other tiggers should not run.
            'default': 50,
            'holdable': 60,
            'useable': 61
        }

        # list of object keys that support DelAfter
        self.OBJECT_VALIDUNTIL_KEYS = ("actionText", "speachText")

        # useable and holdable sprites need to be triggers so things can
        # be done when another sprite interacts with them.
        # copy (by refernece) sprites to triggers
        for useable in self.findObject(type="useable", returnAll=True):
            self.addObject(useable, objectList=self.triggers)
        for holdable in self.findObject(type="holdable", returnAll=True):
            self.addObject(holdable, objectList=self.triggers)

    ########################################################
    # SPRITE DATA METHODS
    ########################################################
    
    def setSpriteAction(self, sprite):
        # flag a sprite as waiting to perform an action.
        # Normally set in a player sprite after the server receives an playerAction message from client.
        sprite["action"] = True

    def delSpriteAction(self, sprite):
        # clear sprite flag from sprite.
        if "action" in sprite:
            del sprite["action"]

    def setSpriteDest(self, object, destX, destY, speed):
        # flag a sprite as wanting to move to a new location at a specific speed.
        # Normally set in a player sprite after the server receives a playerMove message from the client.
        object["destX"] = destX
        object["destY"] = destY
        object["speed"] = speed

    def delSpriteDest(self, object):
        # stop a sprite from moving
        if "destX" in object:
            del object["destX"]
        if "destY" in object:
            del object["destY"]
        if "speed" in object:
            del object["speed"]

    ########################################################
    # STEP DISPATCHER (Order of steps matters!)
    ########################################################

    def stepMap(self):

        self.stepTimers()

        # move the map forward one step in time.
        self.stepMapStart()

        for sprite in self.sprites:
            self.stepSpriteStart(sprite)

        # process all triggers that have sprites inside them.
        for sprite in self.sprites:
            self.stepTrigger(sprite)

        # move any sprites that are in motion.
        for sprite in self.sprites:
            self.stepMove(sprite)

        for sprite in self.sprites:
            self.stepSpriteEnd(sprite)

        self.stepMapEnd()

    ########################################################
    # STEP TIMERS
    ########################################################

    def stepTimers(self):
        # Set visibility to true/false for any layers with expired "hideAfter"/"showAfter".
        # Also, del any objects on object layers that have expired "delAfter".
        currentTime = time.perf_counter()
        for layer in self.layers:
            if "hideAfter" in layer and layer["hideAfter"] > currentTime:
                # hide the layer
                self.setLayerVisablitybyName(layer["name"], False)
                del layer["hideAfter"]
            if "showAfter" in layer and layer["showAfter"] > currentTime:
                # show the layer
                self.setLayerVisablitybyName(layer["name"], True)
                del layer["showAfter"]
            if layer["type"] == "objectgroup":
                for object in layer['objects']:
                    if "delAfter" in object and object["delAfter"] > currentTime:
                        # remove expired object
                        self.removeObject(object, objectList=layer["objects"])
                    else:
                        for key in self.OBJECT_VALIDUNTIL_KEYS:
                            keyDelAfter = key + "DelAfter"
                            if keyDelAfter not in object or object[keyDelAfter] > currentTime:
                                # remove expired object[key+"DelAfter"] and object[key]
                                if keyDelAfter in object:
                                    del object[keyDelAfter];
                                if key in object:
                                    del object[key]
                                    self.setMapChanged()

    ############################################################
    # STEP MAP START/END PROCESSING
    ############################################################
    def stepMapStart(self):
        # Logic needed at the start of the step that is not related to any specific sprite.
        self.delPopUpText()

    def stepMapEnd(self):
        # Logic needed at the end of the step that is not related to any specific sprite.
        pass

    ############################################################
    # STEP SPRITE START/END PROCESSING
    ############################################################
    def stepSpriteStart(self, sprite):
        # Logic needed at the start of the step for a sprite
        pass
        

    def stepSpriteEnd(self, sprite):
        # Logic needed at the end of the step for a sprite.
        
        # The Drop action is not a trigger so we need to do it here.
        self.actionDrop(sprite)
        
        # if an action was requested by no possible action was found then just delete it.
        self.delSpriteAction(sprite)

        # remove actionText from non-players, since they will never see it.
        if sprite["type"] != "player" and "actionText" in sprite:
            del sprite["actionText"]

    def actionDrop(self, sprite):
        if "holding" in sprite:
            if "action" in sprite:
                # Remove object that sprite is holding.
                dropping = sprite["holding"]
                del sprite["holding"]

                # put the dropped item at the feet of the sprite that was holding it.
                self.setObjectLocationByAnchor(dropping, sprite["anchorX"], sprite["anchorY"])
                self.delSpriteDest(dropping)
                self.addObject(dropping, objectList=self.sprites)
                self.addObject(dropping, objectList=self.triggers)

                self.delSpriteAction(sprite)
            elif "actionText" not in sprite:
                sprite["actionText"] = f"Available Action: Drop {sprite['holding']['name']}"

    ########################################################
    # TRIGGER DISPATCHER
    ########################################################

    def stepTrigger(self, sprite):
        # find all triggers that contain this sprite's anchor and process each one.
        # make sure to exclude sprite since objects may be on the sprite and trigger layer at the same time.
        triggers = self.findObject(
            x=sprite["anchorX"],
            y=sprite["anchorY"],
            objectList=self.triggers,
            returnAll=True,
            exclude=sprite)
        # if trigger is not in priority list then add it with the default priority
        for trigger in triggers:
            if trigger['type'] not in self.TRIGGER_PRIORITY:
                self.TRIGGER_PRIORITY[trigger['type']] = self.TRIGGER_PRIORITY["default"]
        # sort triggers by priority (lower first)
        triggers.sort(key=lambda o: self.TRIGGER_PRIORITY[o["type"]])
        # call each triggers method. e.g. trigger['mapDoor'] will call triggerMapDoor(trigger, sprite)
        for trigger in triggers:
            # generate the triggers method name
            triggerMehodName = "trigger" + trigger['type'][:1].capitalize() + trigger['type'][1:]
            # try to get the method object from self
            triggerMethod = getattr(self, triggerMehodName, None)
            # if getattr returned a valid callable method
            if callable(triggerMethod):
                stopOtherTriggers = triggerMethod(trigger, sprite)
                if stopOtherTriggers:
                    break # do not process any more triggers for this sprite on this step.
            else:
                log(f"ServerMap does not have method named {triggerMehodName} to call for trigger type {trigger['type']}.", "ERROR")

    ########################################################
    # Trigger Holdable
    ########################################################

    def triggerHoldable(self, holdable, sprite):
        if "holding" not in sprite:
            if "action" in sprite:
                # sprite picks up holdable
                self.removeObject(holdable, objectList=self.sprites)
                self.removeObject(holdable, objectList=self.triggers)
                sprite["holding"] = holdable
                self.delSpriteAction(sprite)
            elif "actionText" not in sprite:
                sprite["actionText"] = f"Available Action: Pick Up {holdable['name']}"

    ########################################################
    # Trigger Useable
    ########################################################

    def triggerUseable(self, useable, sprite):
        '''
        simple example that let's an object of type useable act as a
        mapdoor assuming, it has same properties as a mapdoor.
        More interesting things can be done with use in sub-classes.
        '''
        if "action" in sprite:
            if "prop-trigger" in useable:
                if useable["prop-trigger"] == "mapDoor":
                    self.triggerMapDoor(useable, sprite)  # assume usable has the properties required by a mapDoor trigger
            self.delSpriteAction(sprite)
        elif "actionText" not in sprite:
            sprite["actionText"] = f"Available Action: Use {useable['name']}"


    ########################################################
    # TRIGGER MAPDOOR
    ########################################################

    def triggerMapDoor(self, trigger, sprite):
        # Move sprite based on trigger. This may include moving to a new map.

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
    # TRIGGER POPUPTEXT
    ########################################################

    def triggerPopUpText(self, trigger, sprite):
        # add text to overlay layer.

        if sprite["type"] != "player":
            return  # only players can trigger pop up text.

        # find dest based on object named trigger["prop-destReference"] on layer"reference"
        dest = self.findObject(name=trigger["prop-textReference"], objectList=self.reference)
        if dest:
            popUpText = self.checkObject(
                {
                    "height": dest["height"],
                    "text": { "text": trigger["prop-text"] },
                    "type": "popUpText",
                    "width": dest["width"],
                    "x": dest["x"],
                    "y": dest["y"]
                    })
            
            for k,v in trigger.items():
                if k.startswith("prop-text-"):
                    textpropName = k[10:]
                    popUpText["text"][textpropName] = trigger[k]
            
            self.addObject(popUpText, objectList=self.overlay)
        else:
            log(f'Could not find name=f{trigger["prop-textReference"]} on reference layer.', "WARNING")

    def delPopUpText(self):
        # popUpText only lasts one step so it's to be added every step to be seen by player.
        # Remove all popUpText. It will get added in the triggers below. see triggerPopUpText()
        for popUpText in self.findObject(type="popUpText", objectList=self.overlay, returnAll=True):
            self.removeObject(popUpText, objectList=self.overlay)

    ########################################################
    # STEP MOVE
    ########################################################

    def stepMove(self, sprite):
        # Move sprite within this map while respecting inBounds and outOfBounds

        # if sprite is moving
        if "destX" in sprite and "destY" in sprite and "speed" in sprite:

            # convert pixels per second to pixels per step
            stepSpeed = sprite["speed"] / engine.server.SERVER.fps

            # compute a new angle in radians which moves directly towards destination
            # sprite["direction"] is stored and never removed so client will know the last
            # direction the sprite was facing.
            sprite["direction"] = geo.angle(sprite["anchorX"], sprite["anchorY"], sprite["destX"], sprite["destY"])

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
                if geo.distance(sprite["anchorX"], sprite["anchorY"], newAnchorX, newAnchorY) < 0.1:
                    # if sprite is only going to move less than 0.1 pixel then stop it.
                    self.delSpriteDest(sprite)
                elif geo.distance(newAnchorX, newAnchorY, sprite["destX"], sprite["destY"]) < stepSpeed:
                    # if sprite is close to destination then stop it.
                    self.delSpriteDest(sprite)

                # move sprite to new location
                self.setObjectLocationByAnchor(sprite, newAnchorX, newAnchorY)
            else:
                # sprite cannot move.
                self.delSpriteDest(sprite)

    def objectInBounds(self, object, x=False, y=False):
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
        if x == False:
            x = object["anchorX"]
        if y == False:
            y = object["anchorY"]
        if geo.objectContains({"x": 0, "y": 0, "width": self.pixelWidth, "height": self.pixelHeight}, x, y) and \
                (geo.objectsContains(self.inBounds, x, y) or (not geo.objectsContains(self.outOfBounds, x, y))):
            return True
        return False

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
        # del object from any object layers it is on if it's delAfter as expired.
        currentTime = time.perf_counter()
        for layer in self.layers:
            if layer["type"] == "objectgroup":
                for object in layer['objects']:
                    # del any objects on object layers that have expired "delAfter".
                    if "delAfter" in object and object["delAfter"] > currentTime:
                        # remove expired object
                        self.removeObject(object, objectList=layer["objects"])
    
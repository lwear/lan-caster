from engine.log import log
import engine.map
import engine.geometry as geo
import engine.time as time
import engine.server


class StepMap(engine.map.Map):
    '''
    The ServerMap class is responsible for implementing the game logic of "stepping" the map forward in time.
    '''

    def __init__(self, tilesets, mapDir):
        super().__init__(tilesets, mapDir)

        '''
        some step methods must be processed before others for a given part of the step
        lower number triggers will be processed before higher number triggers.
        '''
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
        self.stepMethodTypes = (
            "stepMapStart",
            "stepSpriteStart",
            "trigger",
            "stepMove",
            "stepSpriteEnd",
            "stepMapEnd")

        self.stepMethodPriority = {}
        for stepMethodType in self.stepMethodTypes:
            self.stepMethodPriority[stepMethodType] = {'default': 50}

        self.stepMethods = {}

        # Find init* methods in this instance (methods could be from this class or a subclass)
        # Note, one important job of init methods is to add to self.stepMethodPriority before the step methods are found and sorted below.
        initMethods = [func for func in dir(self) if callable(getattr(self, func)) and func.startswith("init") and len(func) > len("init")]
        initMethods.sort()
        methodsText = ""
        for methodName in initMethods:
            methodsText += f"{methodName} "
        log(f"Map {self.name}: Found init methods: {methodsText}")
        
        # call init methods.
        for initMethodName in initMethods:
            initMethod = getattr(self, initMethodName, None)
            initMethod()
        
        #find step methods in this instance
        for stepMethodType in self.stepMethodTypes:
            self.stepMethods[stepMethodType] = [func for func in dir(self) if callable(getattr(self, func)) and func.startswith(stepMethodType)]
            # if stepMethod is not in priority list then add it with the default priority
            for methodName in self.stepMethods[stepMethodType]:
                if methodName not in self.stepMethodPriority[stepMethodType]:
                    self.stepMethodPriority[stepMethodType][methodName] = self.stepMethodPriority[stepMethodType]["default"]
            self.stepMethods[stepMethodType].sort(key=lambda methodName: self.stepMethodPriority[stepMethodType][methodName])
            methodsText = ""
            for methodName in self.stepMethods[stepMethodType]:
                methodsText += f"{methodName}/{self.stepMethodPriority[stepMethodType][methodName]} "
            log(f"Map {self.name}: Found {stepMethodType} methods/priority: {methodsText}")

        '''
        # Find trigger* methods in this instance and ensure they are in priority list (methods could be from this class or a subclass)
        triggerMethods = [func for func in dir(self) if callable(getattr(self, func)) and func.startswith("trigger") and len(func) > len("init")]
        # if trigger Method is not in priority list then add it with the default priority
        for triggerName in triggerMethods:
            if triggerName not in self.stepMethodPriority['trigger']:
                self.stepMethodPriority['trigger'][triggerName] = self.stepMethodPriority['trigger']["default"]
        triggerMethods.sort(key=lambda triggerName: self.stepMethodPriority['trigger'][triggerName])
        log(f"Map {self.name}: Found trigger methods (in order): {triggerMethods}")
        '''

    def addStepMethodPriority(self, stepMethodType, stepMethodName, priority):
        # used by subclass init* methods to prioritize step methods before finding and sorting them.
        if stepMethodType not in self.stepMethodPriority:
            log(f"{stepMethodType} is not a valid stepMethodType.", "WARNING")
            return
        self.stepMethodPriority[stepMethodType][stepMethodName] = priority

    ########################################################
    # STEP DISPATCHER (Order of steps matters!)
    ########################################################

    def stepMap(self):
        # move the map forward one step in time by calling all step methods

        # call all self.stepMapStart*() methods
        for methodName in self.stepMethods["stepMapStart"]:
            method = getattr(self, methodName, None)
            method()

        # call all self.stepSpriteStart*(sprite) methods for each sprite
        for methodName in self.stepMethods["stepSpriteStart"]:
            method = getattr(self, methodName, None)
            for sprite in self.sprites:
                method(sprite)

        # call each trigger once for each sprite with an anchor point inside the trigger.
        # call will look like self.trigger*(trigger, sprite)
        for sprite in self.sprites:
            self.stepTriggers(sprite)

        # call all self.stepMove*(sprite) methods for each sprite
        for methodName in self.stepMethods["stepMove"]:
            method = getattr(self, methodName, None)
            for sprite in self.sprites:
                method(sprite)

        # call all self.stepSpriteEnd*(sprite) methods  for each sprite
        for methodName in self.stepMethods["stepSpriteEnd"]:
            method = getattr(self, methodName, None)
            for sprite in self.sprites:
                method(sprite)

        # call all self.stepMapEnd*() methods
        for methodName in self.stepMethods["stepMapEnd"]:
            method = getattr(self, methodName, None)
            method()

    def stepTriggers(self, sprite):
        # find all triggers that contain this sprite's anchor and process each one.
        # make sure to exclude sprite since objects may be on the sprite and trigger layer at the same time.
        triggers = self.findObject(
            x=sprite["anchorX"],
            y=sprite["anchorY"],
            objectList=self.triggers,
            returnAll=True,
            exclude=sprite)

        for trigger in triggers:
            triggerMehodName = self.getTriggerMethodName(trigger)
            # if trigger is not in priority list then log error and remove it
            if triggerMehodName not in self.stepMethodPriority['trigger']:
                log(f"ServerMap does not have method named {triggerMehodName} for trigger type {trigger['type']}.", "ERROR")
                triggers.remove(trigger)
        
        # sort triggers by priority (lower first)
        triggers.sort(key=lambda trigger: self.stepMethodPriority['trigger'][self.getTriggerMethodName(trigger)])
        
        # call each triggers method. e.g. trigger['type'] == 'mapDoor' will call triggerMapDoor(trigger, sprite)
        for trigger in triggers:
            triggerMethod = getattr(self, self.getTriggerMethodName(trigger), None)
            stopOtherTriggers = triggerMethod(trigger, sprite)
            if stopOtherTriggers:
                break # do not process any more triggers for this sprite on this step.

    def getTriggerMethodName(self, trigger):
        # Convert a trigger type (eg. trigger["type"] == "mapDoor") to method name (eg. "triggerMapDoor")
        return "trigger" + trigger['type'][:1].capitalize() + trigger['type'][1:]
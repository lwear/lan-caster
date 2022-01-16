from engine.log import log
import demo.servermap


class ServerMap(demo.servermap.ServerMap):
    '''
    This class implements the lockedMapDoor mechanic.
    '''

    ########################################################
    # TRIGGER LOCKED MAPDOOR
    ########################################################

    def triggerLockedMapDoor(self, trigger, sprite):
        # if the sprite is holding the correct thing to unlock the door.
        if "holding" in sprite and sprite["holding"]["name"] == trigger["prop-unlocks"]:

            # unlock door (change type to normal mapDoor)
            trigger["type"] = "mapDoor"

            # hide door layer and show unlocked door layer.
            self.setLayerVisablitybyName("doorClosed", False)
            self.setLayerVisablitybyName("doorOpen", True)
        elif sprite["type"] == "player":
            sprite["speachText"] = trigger["prop-lockedText"]

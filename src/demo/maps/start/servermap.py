from engine.log import log
import demo.servermap


class ServerMap(demo.servermap.ServerMap):
    '''
    This class implements the lockedMapDoor mechanic.
    '''

    ########################################################
    # TRIGGER LOCKED MAPDOOR (uses mapdoor)
    ########################################################

    def triggerLockedMapDoor(self, trigger, sprite):
        # if the sprite is holding the correct thing to unlock the door.

        # only prop-unlocks is required
        if not self.checkKeys(trigger, ("prop-unlocks")):
            log("Cannot process lockedMapDoor trigger.", "ERROR")
            return

        if "holding" in sprite and sprite["holding"]["name"] == trigger["prop-unlocks"]:

            # unlock door (change type to normal mapDoor)
            # sprite will most likely trigger the mapDoor on the next step.
            trigger["type"] = "mapDoor"

            # hide door locked layer and show unlocked door layer.
            if trigger["prop-hideLayer"]:
                self.setLayerVisablitybyName(trigger["prop-hideLayer"], False)
            if trigger["prop-showLayer"]:
                self.setLayerVisablitybyName(trigger["prop-showLayer"], True)
        elif sprite["type"] == "player":
            self.setSpriteSpeechText(sprite, trigger["prop-lockedText"])

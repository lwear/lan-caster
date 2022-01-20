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

        if not self.checkKeys(trigger, ["prop-unlocks", "prop-lockedText"]):
            log("Cannot process lockedMapDoor trigger.", "ERROR")
            return

        # if the sprite is holding the correct thing to unlock the door.
        if "holding" in sprite and sprite["holding"]["name"] == trigger["prop-unlocks"]:

            # unlock door (change type to normal mapDoor)
            # sprite will most likely trigger the mapDoor on the next step.
            trigger["type"] = "mapDoor"

            # hide door locked layer and show unlocked door layer.
            if "prop-hideLayer" in trigger:
                self.setLayerVisablitybyName(trigger["prop-hideLayer"], False)
            if "prop-showLayer" in trigger:
                self.setLayerVisablitybyName(trigger["prop-showLayer"], True)
        elif sprite["type"] == "player":
            self.setSpriteSpeechText(sprite, trigger["prop-lockedText"])

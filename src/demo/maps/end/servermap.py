from engine.log import log
import demo.servermap
import engine.server
import engine.geometry as geo


class ServerMap(demo.servermap.ServerMap):
    '''
    This class implements the Lever and Magic Wand mechanics.
    '''

    ########################################################
    # ACTION USE - LEVER
    ########################################################

    def triggerMagicArea(self, magicArea, sprite):
        if "holding" in sprite and sprite["holding"]["name"] == "magic wand":
            if "action" in sprite:
                self.triggerUseable(self.findObject(name="lever"), sprite)
            else:
                self.setSpriteActionText(sprite, f"Available Action: Cast spell with {sprite['holding']['name']}.")
        elif sprite["type"] == "player":
            self.setSpriteSpeechText(sprite, f"This place seems magical but I feel like I need something to help cast a spell.")


    def triggerUseable(self, useable, sprite):
        if useable["name"] == "lever" and "action" in sprite:
            start = engine.server.SERVER.maps["start"]

            # hard coding of gids is specific to this map and it's assignment of gids.
            # add 1 to levers gid and make sure it stays in range 381-382
            useable["gid"] += 1
            if useable["gid"] == 384:
                useable["gid"] = 381

            if useable["gid"] == 381:
                self.setLayerVisablitybyName("bridge1", True)
                start.setLayerVisablitybyName("bridge2", False)
                self.setLayerVisablitybyName("bridge3", False)
                self.removeObject(
                    self.findObject(name="bridge3InBounds", objectList=self.inBounds),
                    objectList=self.inBounds)
                self.addObject(
                    self.findObject(name="bridge1InBounds", objectList=self.reference),
                    objectList=self.inBounds)
            elif useable["gid"] == 382:
                self.setLayerVisablitybyName("bridge1", False)
                start.setLayerVisablitybyName("bridge2", True)
                self.setLayerVisablitybyName("bridge3", False)
                self.removeObject(
                    self.findObject(name="bridge1InBounds", objectList=self.inBounds),
                    objectList=self.inBounds)
                start.addObject(
                    start.findObject(name="bridge2InBounds", objectList=start.reference),
                    objectList=start.inBounds)
            elif useable["gid"] == 383:
                self.setLayerVisablitybyName("bridge1", False)
                start.setLayerVisablitybyName("bridge2", False)
                self.setLayerVisablitybyName("bridge3", True)
                # The very first time we use the lever there will not be bridge2InBounds in
                # the inBounds so we need to check to see if we found anything.
                b2ib = start.findObject(name="bridge2InBounds", objectList=start.inBounds)
                if b2ib:
                    start.removeObject(b2ib, objectList=start.inBounds)
                self.addObject(
                    self.findObject(name="bridge3InBounds", objectList=self.reference),
                    objectList=self.inBounds)

            self.delSpriteAction(sprite)
            
        super().triggerUseable(useable, sprite)
                
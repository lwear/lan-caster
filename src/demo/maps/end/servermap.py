from engine.log import log
import demo.servermap
import engine.server
import engine.geometry as geo


class ServerMap(demo.servermap.ServerMap):

    ########################################################
    # ACTION DISPATCHER
    ########################################################
    def stepAction(self, sprite):
        if "action" in sprite and "holding" in sprite:
            if sprite["holding"]["name"] == "magic wand" and self.findObject(
                    x=sprite["anchorX"], y=sprite["anchorY"], type="magicArea", objectList=self.reference):
                self.actionMagic(sprite)
                del sprite["action"]
                return

        super().stepAction(sprite)

    ########################################################
    # ACTION USE - LEVER
    ########################################################

    def actionUse(self, sprite, useable):
        # some hard coding specific to this map and it's assignment of gids.
        if useable["name"] == "lever":
            # add 1 to levers gid and make sure it stays in range 381-382
            start = engine.server.SERVER.maps["start"]
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
        else:
            super().actionUse(sprite, useable)

    ########################################################
    # ACTION MAGIC (trigger lever if use magic wand in magic area)
    ########################################################

    def actionMagic(self, sprite):
        # find the lever and use it.
        lever = self.findObject(name="lever")
        self.actionUse(sprite, lever)

    ########################################################
    # ACTIONTEXT (custom text for using magic wand in magic area)
    ########################################################

    def stepActionText(self, sprite):
        # order of action priority is always: pickup, use, drop.

        if sprite["type"] != "player":
            return  # only players can see their action text.

        if "holding" in sprite:
            if sprite["holding"]["name"] == "magic wand" and self.findObject(
                    x=sprite["anchorX"], y=sprite["anchorY"], type="magicArea", objectList=self.reference):
                sprite["actionText"] = f"Available Action: Cast spell with {sprite['holding']['name']}."
                return

        super().stepActionText(sprite)

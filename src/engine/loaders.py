import os
import importlib

from engine.log import log
import engine.tileset


def loadServer(game):
    '''
    Find the most specific server.py file for this game and load it.
    Look in the game folder first and then the engine folder.
    '''
    if os.path.isfile(f"src/{game}/server.py"):
        log(f"Importing {game}.server module")
        return importlib.import_module(f"{game}.server")
    else:
        log(f"Importing engine.server module")
        return importlib.import_module(f"engine.server")


def loadClient(game):
    '''
    Find the most specific client.py file for this game and load it.
    Look in the game folder first and then the engine folder.
    '''
    if os.path.isfile(f"src/{game}/client.py"):
        log(f"Importing {game}.client module")
        return importlib.import_module(f"{game}.client")
    else:
        log(f"Importing engine.client module")
        return importlib.import_module(f"engine.client")


def loadTilesets(game, loadImages):
    '''
    Return a dictionary of tileset objects, with the key being the tileset name:
    {'tileset1name': tileset1object, 'tileset2name': tileset2object, ....}
    '''
    tilesetsDir = f"src/{game}/tilesets"
    tilesets = {}
    listing = os.listdir(tilesetsDir)
    for tilesetFile in listing:
        ts = engine.tileset.Tileset(tilesetsDir, tilesetFile, loadImages)
        tilesets[ts.name] = ts
    return tilesets


def loadMaps(tilesets, game, maptype):
    '''
    Return a dictionary of map objects, with the key being the map name:
    {'map1name': map1object, 'map2name': map2object, ....}

    The map object is either a client or server map and the most specific version of
    each will be searched for by looking first in the map folder for servermap.py or 
    clientmap.py, then the game folder, and then the engine folder.
    '''
    if maptype == "ServerMap":
        filename = "servermap"
    elif maptype == "ClientMap":
        filename = "clientmap"
    else:
        log(f"maptype == {maptype} is not supported. maptype must be 'ServerMap' or 'ClientMap'.", "FAILURE")
        exit()

    mapsDir = f"src/{game}/maps"
    maps = {}
    listing = os.listdir(mapsDir)
    for mapDir in listing:
        if os.path.isfile(f"src/{game}/maps/{mapDir}/{filename}.py"):
            log(f"Importing {game}.maps.{mapDir}.{filename} module for map {mapDir}")
            module = importlib.import_module(f"{game}.maps.{mapDir}.{filename}")
        elif os.path.isfile(f"src/{game}/{filename}.py"):
            log(f"Importing {game}.{filename} module for map {mapDir}")
            module = importlib.import_module(f"{game}.{filename}")
        else:
            log(f"Importing engine.{filename} module for map {mapDir}")
            module = importlib.import_module(f"engine.{filename}")

        if maptype == "ServerMap":
            mapObj = module.ServerMap(tilesets, mapsDir + "/" + mapDir, game)
        else:
            mapObj = module.ClientMap(tilesets, mapsDir + "/" + mapDir, game)

        maps[mapObj.name] = mapObj

    return maps

import os
import importlib

from engine.log import log

def findModule(moduleName, game = False, map = False):
    '''
    Return module for moduleName based on searching maps, game, and engine folders, in that order. 
    Map and game will only be searched if provided.
    '''

    fortext = ""
    if game and map:
        fortext = f" for game {game} and map {map}"
    elif game:
        fortext = f" for game {game}"

    if game and map and os.path.isfile(f"src/{game}/maps/{map}/{moduleName}.py"):
        log(f"Importing {game}.maps.{map}.{moduleName} module{fortext}.")
        module = importlib.import_module(f"{game}.maps.{map}.{moduleName}")
    elif game and os.path.isfile(f"src/{game}/{moduleName}.py"):
        log(f"Importing {game}.{moduleName} module{fortext}.")
        module = importlib.import_module(f"{game}.{moduleName}")
    elif os.path.isfile(f"src/engine/{moduleName}.py"):
        log(f"Importing engine.{moduleName} module{fortext}.")
        module = importlib.import_module(f"engine.{moduleName}")
    else:
        log(f"Module name {moduleName} not found{fortext}.", "FAILURE")
        exit()

    return module


def loadTilesets(game, loadImages):
    '''
    Return a dictionary of tileset objects, with the key being the tileset name:
    {'tileset1name': tileset1object, 'tileset2name': tileset2object, ....}
    '''

    if loadImages:
        module = findModule("clienttileset", game = game)
    else:
        module = findModule("tileset", game = game)

    tilesetsDir = f"src/{game}/tilesets"
    tilesets = {}
    listing = os.listdir(tilesetsDir)
    for tilesetFile in listing:
        if loadImages:
            ts = module.ClientTileset(tilesetsDir, tilesetFile)
        else:
            ts = module.Tileset(tilesetsDir, tilesetFile)
        tilesets[ts.name] = ts
    return tilesets


def loadMaps(tilesets, game, maptype):
    '''
    Return a dictionary of map objects, with the key being the map name:
    {'map1name': map1object, 'map2name': map2object, ....}

    The map objects are either client or server maps and the most specific version of
    each will be searched for by looking first in the map folder for servermap.py or
    clientmap.py, then the game folder, and then the engine folder.
    '''
    if maptype == "ServerMap":
        moduleName = "servermap"
    elif maptype == "ClientMap":
        moduleName = "clientmap"
    else:
        log(f"maptype == {maptype} is not supported. maptype must be 'ServerMap' or 'ClientMap'.", "FAILURE")
        exit()

    mapsDir = f"src/{game}/maps"
    maps = {}
    listing = os.listdir(mapsDir)
    for map in listing:
        module = findModule(moduleName, game=game, map=map)

        if maptype == "ServerMap":
            mapObj = module.ServerMap(tilesets, mapsDir + "/" + map, game)
        else:
            mapObj = module.ClientMap(tilesets, mapsDir + "/" + map, game)

        maps[mapObj.name] = mapObj

    return maps

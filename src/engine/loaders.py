import os
import importlib

from engine.log import log


def loadModule(moduleName, game, mapName=False):
    '''
    Return module for moduleName based on searching maps, game, and engine folders, in that order.
    Map folder will only be search if mapName is provided.
    '''

    fortext = ""
    if mapName:
        fortext = f" for map {mapName}"

    if game and mapName and os.path.isfile(f"src/{game}/maps/{mapName}/{moduleName}.py"):
        log(f"Importing {game}.maps.{mapName}.{moduleName}{fortext}.")
        module = importlib.import_module(f"{game}.maps.{mapName}.{moduleName}")
    elif game and os.path.isfile(f"src/{game}/{moduleName}.py"):
        log(f"Importing {game}.{moduleName}{fortext}.")
        module = importlib.import_module(f"{game}.{moduleName}")
    elif os.path.isfile(f"src/engine/{moduleName}.py"):
        log(f"Importing engine.{moduleName}{fortext}.")
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
        module = loadModule("clienttileset", game=game)
    else:
        module = loadModule("tileset", game=game)

    tilesetsDir = f"src/{game}/tilesets"
    tilesets = {}
    listing = os.listdir(tilesetsDir)
    for tilesetFile in listing:
        if loadImages:
            ts = module.ClientTileset(tilesetsDir + "/" + tilesetFile)
        else:
            ts = module.Tileset(tilesetsDir + "/" + tilesetFile)
        tilesets[ts.name] = ts
    return tilesets


def loadMaps(tilesets, game, maptype):
    '''
    Return a dictionary of map objects, with the key being the map name:
    {'map1name': map1object, 'map2name': map2object, ....}

    All map objects will be either type ServerMap or ClientMap. For each map, the most specific
    module will be found for by looking first in the map folder for servermap.py or
    clientmap.py, then the game folder, and then the engine folder. Therefore, each map
    could use a differnt module.
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
    for mapName in listing:
        module = loadModule(moduleName, game=game, mapName=mapName)

        if maptype == "ServerMap":
            mapObj = module.ServerMap(tilesets, mapsDir + "/" + mapName)
        else:
            mapObj = module.ClientMap(tilesets, mapsDir + "/" + mapName)

        maps[mapObj.name] = mapObj

    return maps

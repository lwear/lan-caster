# LAN-Caster
Simple python 2D multiplayer online game engine for local area networks (LAN).

The goal of LAN-Caster is to provide an easy-to-use code base for developing 2D multiplayer online games. The networking component of Lancaster is specifically a design for local area networks.

# How To Run


## Prerequisites

The following items need to be installed to run LAN-Caster.

### Python 3.6 or higher

LAN-Caster uses Python 3.6 or higher (tested on python 3.7.3) which can be installed from [https://www.python.org/downloads/](https://www.python.org/downloads/).

> If multiple versions of python are installed, ensure you are running python 3.6+, not python 3.5 or python 2. The examples in this README use the "python" command assuming python 3.6+ is the default. The command "python3" (Linux) or "py -3" (Windows) may be required to force the correct version.

### Python Modules
LAN-Caster requires two added python moduels to be installed. If a computer is only running the LAN-Caster server then the pygame module is not required.
1) Pygame is used by the clients to open the game window, render graphics, and collect player input. 
2) Msgpack is used to encode and decode messages between the server and clients.

To install pygame and msgpack on Windows use:
```
py -3 -m pip install pygame msgpack-python
```

To install pygame and msgpack on Linux use:
```
pip3 install pygame msgpack-python
```

### LAN-Caster Code

The LAN-Caster code can be cloned with git from: [https://github.com/dbakewel/lan-caster.git](https://github.com/dbakewel/lan-caster.git) or downloaded in zip form from: [https://github.com/dbakewel/lan-caster/archive/master.zip](https://github.com/dbakewel/lan-caster/archive/master.zip)


## Running the Demo

On windows, **double click "run-demo.bat"** in the root of the LAN-Caster directory.

> If this does not work, open a command window (cmd), cd into the directory containing run-demo.bat and type "rundemo.bat".

The rundemo script will start 4 processes on the local computer: 1 server and 3 clients. Normally, each client would run on a different computer and used by a differnet user. The run-demo.bat allows one users to move back and forth between all 3 clients and play all the players at once.

## Running on Separate Computers

By default LAN-Caster only listens on localhost 127.0.0.1 which does not allow messages to be sent or received between computers. To listen on all network interfaces, and allow messages from other computers, use ```-ip 0.0.0.0``` on server and clients. 

> Note, if you want to run LAN-Caster across a network then the ports you choose must be open in the OS and network firewalls for two way UDP traffic. By default, these ports are in the range 20000 - 20020 range but any available UDP ports can be used.

For example:

Assuming:
*   computer 1 has IP address of 192.168.1.10
*   computer 2 has IP address of 192.168.1.11
*   computer 3 has IP address of 192.168.1.22
*   computer 4 has IP address of 192.168.1.33

The server can be run on computer 1 with: 

```
py -3 src/startserver.py -game "demo" -ip 0.0.0.0 -p 20000
```

The server will listen on 127.0.0.1 and 192.168.1.10

A client can be run on Computer 2, 3, and 4 with: 

```
pythoy -3 src/startclient.py -game "demo" -p 20010 -sip 192.168.1.10 -sp 20000
```

Even though the clients on computer 1, 3, and 4 use the same port (20010) they are on separate computers so it works. If you try running two robots on the same port on the same computer you will get an error.

## Command Line Help

The server and client allow some customization with command line switches. Use the **-h** switch to display help. For example:

```
D:\lan-caster>py src\startserver.py -h
pygame 2.1.0 (SDL 2.0.16, Python 3.8.3)
Hello from the pygame community. https://www.pygame.org/contribute.html
usage: startserver.py [-h] [-game [Game]] [-ip Server_IP] [-p Server_Port] [-fps fps] [-debug] [-verbose]

optional arguments:
  -h, --help      show this help message and exit
  -game [Game]    Game Folder (default: demo)
  -ip Server_IP   My IP Address (default: 127.0.0.1)
  -p Server_Port  My port number (default: 20000)
  -fps fps        Target frames (a.k.a. server steps) per second. (default: 30)
  -debug          Print DEBUG level log messages. (default: False)
  -verbose        Print VERBOSE level log messages. Note, -debug includes -verbose. (default: False)
```

```
D:\lan-caster>py src\startclient.py -h
pygame 2.1.0 (SDL 2.0.16, Python 3.8.3)
Hello from the pygame community. https://www.pygame.org/contribute.html
usage: startclient.py [-h] [-game [Game]] [-name [Name]] [-ip [My IP]] [-p [My Port]] [-sip [Server IP]]
                      [-sp [Server Port]] [-fps fps] [-debug] [-verbose]

optional arguments:
  -h, --help         show this help message and exit
  -game [Game]       Game Folder (default: demo)
  -name [Name]       Player's Name (default: anonymous)
  -ip [My IP]        My IP Address (default: 127.0.0.1)
  -p [My Port]       My port number (default: 20010)
  -sip [Server IP]   Server IP Address (default: 127.0.0.1)
  -sp [Server Port]  Server port number (default: 20000)
  -fps fps           Target frames per second. (default: 30)
  -debug             Print DEBUG level log messages. (default: False)
  -verbose           Print VERBOSE level log messages. Note, -debug includes -verbose. (default: False)
```

---


## Additional Information

The following videos provide an overview of how to use LAN-Caster to build your own game. Also, see comments in the
LAN-Caster code.

videos coming soon...

### Files to add comments to:

README.md
src/demo/servermap.py
src/demo/maps/end/servermap.py
src/demo/maps/under/servermap.py
src/demo/maps/under/clientmap.py

### Videos to add:

* Engine Overview
```
General purpose, enhancement, and limitations of the engine
What the engine can do (see test-engine)
How the engine can be expanded (see demo)
architecture: 
  Input data (Tiled): maps and tilesets
  server (game logic), 
  clients/players (input and display), 
  LAN networking
```

* How to write a game with LAN-Caster
```
Design
  Game Concept and Story
  Game Mechanics
  Engine Enhancements and Limitations
  Details: Game and Maps

Implementation
  file structure and loaders
  Maps and Tilesets
  launcher
  adding code
  build for testing (back doors and test suites)
  incremental improvement

Watch the other videos for detailed examples
```

* Engine Maps and Tilesets
```
Tiled
map requirements
layer types
tilesets
tile layers
object layers
well defined (known or spcial) layers
  sprites
layer order (using black layer to help)
```

* Engine Client
```
designed to be a single instance class
map and tileset and clienttileset classes
clientmap class (blitting and validUntil)
limitation (what parts of Tiled are not supported)
```

* Engine Server Class
```
designed to be a single instance class
init
main loop
  message processing
  step processing
  sending steps
  loop timing (fps)
```

* Engine game mechanics (ServerMap Class)
```
servermap class
  init
  step processing (start, sprites, end)
  testing game engine mechanics with test-engine
  engine mechanics
  ACTIONS
    client user input and action message, set action in sprite
    dispacther, 
    pickup, 
    use, 
    drop
  ACTIONTEXT 
    following through to display by client
  TRIGGERS
    dispacther
    mapDoor
    popUpText
  MOVE
    client user input, set dest message

LABELTEXT
SPEACHTEXT
```

* Demo overview
```
  file strucutre, subclassing and loaders review

  Maps and Tileset data

  Tangent: General vs. Hardcoded Design Decisions

  Demo Server
    stepEnd

  Demo Client
    open and ending text (user interface overlay)

```

* Demo game mechanics
```
  
  Making General vs. Hardcoded Design Decisions

  Demo ServerMap
    Chicken, 
    Throw, 
    SpeedMultiplier (mud), 
    Bomb,
    RespawnPoint mechanics (designed to work between maps but demo does not use that feature)

  Start Map ServerMap
    lockedMapDoor

  Under Map ServerMap
    Saw
    Use of Respawn points
    StopSaw

  Under Map ClientMap
    Darkness

  End Map ServerMap
    Lever
    Magic Wand


```

Add trigger for layerVisibleToggle (defalutVisible can be added else taken from file.)
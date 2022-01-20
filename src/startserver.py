import argparse
import os

from engine.log import log
from engine.log import setLogLevel

# only import msgpack here to make sure it is installed.
try:
    import msgpack
except BaseException:
    log("Python package missing. Install with something similar to:\n py -3 -m pip install msgpack-python", "FAILURE")
    exit()

import engine.network
import engine.loaders


def startServer():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-game', metavar='Game', dest='game', type=str, nargs='?',
                        default='demo', help="Game Folder")
    parser.add_argument('-ip', metavar='Server_IP', dest='serverIP', type=engine.network.argParseCheckIPFormat,
                        default='127.0.0.1', help='My IP Address')
    parser.add_argument('-p', metavar='Server_Port', dest='serverPort', type=int,
                        default=20000, help='My port number')
    parser.add_argument('-fps', metavar='fps', dest='fps', type=int,
                        default=30, help='Target frames (a.k.a. server steps) per second.')
    parser.add_argument('-debug', dest='debug', action='store_true',
                        default=False, help='Print DEBUG level log messages.')
    parser.add_argument('-verbose', dest='verbose', action='store_true',
                        default=False, help='Print VERBOSE level log messages. Note, -debug includes -verbose.')
    parser.add_argument('-test', dest='test', action='store_true',
                        default=False, help='Start server in test mode.')
    args = parser.parse_args()

    setLogLevel(args.debug, args.verbose)

    module = engine.loaders.loadModule("server", game=args.game)
    module.Server(args.game, args.fps, args.serverIP, args.serverPort, args.test).run()


if __name__ == "__main__":
    startServer()

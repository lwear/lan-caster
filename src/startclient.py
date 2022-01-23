import argparse
import os
import engine.time as time

from engine.log import log
from engine.log import setLogLevel

# only import msgpack and pygame here to make sure they are installed.
try:
    import pygame
    import msgpack
except BaseException:
    log("Python packages missing. Install with something similar to:\n py -3 -m pip install pygame msgpack-python", "FAILURE")
    exit()

import engine.network
import engine.loaders


def startClient():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-game', metavar='Game', dest='game', type=str, nargs='?',
                        default='demo', help="Game Folder")
    parser.add_argument('-name', metavar='Name', dest='playerDisplayName', type=str, nargs='?',
                        default='anonymous', help="Player's Name")
    parser.add_argument('-fps', metavar='fps', dest='fps', type=int,
                        default=30, help='Target frames per second.')
    parser.add_argument('-width', metavar='width', dest='width', type=int,
                        default=640, help='Window width.')
    parser.add_argument('-height', metavar='height', dest='height', type=int,
                        default=640, help='Window height.')


    parser.add_argument('-sname', metavar='Server_Name', dest='serverName', type=str,
                        default=False, help='Name to use when registering this server with connector.')
    parser.add_argument('-cname', metavar='Connector_Host_Name', dest='connectorHostName', type=str,
                        default='lan-caster.net', help='Hostname of connector.')
    parser.add_argument('-cport', metavar='Connector_Port', dest='connectorPort', type=str,
                        default=20000, help='Port of connector.')


    parser.add_argument('-ip', metavar='My IP', dest='myIP', type=engine.network.argParseCheckIPFormat, nargs='?',
                        default='127.0.0.1', help='My IP Address')
    parser.add_argument('-p', metavar='My Port', dest='myPort', type=int, nargs='?',
                        default=20010, help='My port number')
    parser.add_argument('-sip', metavar='Server IP', dest='serverIP', type=engine.network.argParseCheckIPFormat, nargs='?',
                        default='127.0.0.1', help='Server IP Address')
    parser.add_argument('-sp', metavar='Server Port', dest='serverPort', type=int, nargs='?',
                        default=20000, help='Server port number')

    parser.add_argument('-debug', dest='debug', action='store_true',
                        default=False, help='Print DEBUG level log messages.')
    parser.add_argument('-verbose', dest='verbose', action='store_true',
                        default=False, help='Print VERBOSE level log messages. Note, -debug includes -verbose.')
    parser.add_argument('-pause', metavar='secs', dest='pause', type=int,
                        default=0, help='Duration to pause in seconds before starting client (for testing).')
    args = parser.parse_args()

    setLogLevel(args.debug, args.verbose)

    log(f"Pausing for {args.pause} seconds before starting client.")
    time.sleep(args.pause)

    module = engine.loaders.loadModule("client", game=args.game)
    module.Client(args).run()


if __name__ == '__main__':
    startClient()

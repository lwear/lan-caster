import argparse
import os
import engine.time as time

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
    parser.add_argument('-fps', metavar='fps', dest='fps', type=int,
                        default=30, help='Target frames (a.k.a. server steps) per second.')

    parser.add_argument('-sname', metavar='Server_Name', dest='serverName', type=str,
                        default=False, help='Name to use when registering this server with connector.')
    parser.add_argument('-cname', metavar='Connector_Host_Name', dest='connectorHostName', type=str,
                        default='lan-caster.net', help='Hostname of connector.')
    parser.add_argument('-cport', metavar='Connector_Port', dest='connectorPort', type=int,
                        default=20000, help='Port of connector.')

    parser.add_argument('-ip', metavar='Server_IP', dest='serverIP', type=engine.network.argParseCheckIPFormat,
                        default='127.0.0.1', help='My IP Address')
    parser.add_argument('-p', metavar='Server_Port', dest='serverPort', type=int,
                        default=20000, help='My port number')
    
    parser.add_argument('-debug', dest='debug', action='store_true',
                        default=False, help='Print DEBUG level log messages.')
    parser.add_argument('-verbose', dest='verbose', action='store_true',
                        default=False, help='Print VERBOSE level log messages. Note, -debug includes -verbose.')
    parser.add_argument('-pause', metavar='secs', dest='pause', type=int,
                        default=0, help='Duration to pause in seconds before starting server (for testing).')
    parser.add_argument('-test', dest='testMode', action='store_true',
                        default=False, help='Start server in test mode.')
    args = parser.parse_args()

    setLogLevel(args.debug, args.verbose)

    log(f"Pausing for {args.pause} seconds before starting server.")
    time.sleep(args.pause)

    module = engine.loaders.loadModule("server", game=args.game)
    module.Server(args).run()


if __name__ == "__main__":
    startServer()

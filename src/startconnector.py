import argparse
import os
import engine.time as time

from engine.log import log
from engine.log import setLogLevel

import engine.connector

# only import msgpack here to make sure it is installed.
try:
    import msgpack
except BaseException:
    log("Python package missing. Install with something similar to:\n py -3 -m pip install msgpack-python", "FAILURE")
    exit()

import engine.network
import engine.loaders


def startConnector():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-ip', metavar='Connector_IP', dest='connectorIP', type=engine.network.argParseCheckIPFormat,
                        default='0.0.0.0', help='Connector IP Address')
    parser.add_argument('-p', metavar='Connector_Port', dest='connectorPort', type=int,
                        default=20000, help='Connector port number')
    parser.add_argument('-debug', dest='debug', action='store_true',
                        default=False, help='Print DEBUG level log messages.')
    parser.add_argument('-verbose', dest='verbose', action='store_true',
                        default=False, help='Print VERBOSE level log messages. Note, -debug includes -verbose.')
    args = parser.parse_args()

    setLogLevel(args.debug, args.verbose)

    engine.connector.Connector(args.connectorIP, args.connectorPort).run()


if __name__ == "__main__":
    startConnector()

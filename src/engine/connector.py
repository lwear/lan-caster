import signal
import engine.time as time
import random
import os

from engine.log import log
import engine.log
import engine.messages
import engine.network


def quit(signal=None, frame=None):
    log("Quiting", "INFO")
    exit()


class Connector:

    def __init__(self, connectorIP, connectorPort):
        self.MAX_SERVERS = 100
        self.SERVER_TIMEOUT = 300

        self.serverlist = {}

        messages=engine.messages.Messages()

        # set up networking
        try:
            self.socket = engine.network.Socket(
                messages,
                msgProcessor=self,
                sourceIP=connectorIP,
                sourcePort=connectorPort
                )

        except Exception as e:
            log(str(e), "FAILURE")
            quit()

    def __str__(self):
        return engine.log.objectToStr(self)

    ########################################################
    # MAIN LOOP
    ########################################################

    def run(self):
        '''
        Run the loop below once every  1/fps seconds.
        '''
        while True:
            # process messages from servers and clients (recvReplyMsgs calls msg<msgType> for each msg received)
            self.socket.recvReplyMsgs()
            self.checkTimeouts()
            time.sleep(1)

    def checkTimeouts(self):
        currentTime = time.perf_counter
        for serverName in self.serverlist:
            if self.serverlist[msg["serverName"]]["timeout"] < currentTime:
                del self.serverlist[msg["serverName"]]


    ########################################################
    # Network Message Processing
    ########################################################

    def msgAddServer(self, ip, port, ipport, msg):
        if msg["serverName"] not in self.serverlist:
            if self.MAX_SERVERS < len(self.serverlist):
                self.serverlist[msg["serverName"]] = {
                    'timeout': time.perf_counter + self.SERVER_TIMEOUT,
                    'serverPrivateIP': msg["serverPrivateIP"], 
                    'serverPrivatePort': msg["serverPrivatePort"],
                    'serverPublicIP': ip, 
                    'serverPublicPort': port,
                    }
                return {'type': 'serverAdded'}
            else:
                return {'type': 'Error', 'result': f"Max servers already registered."}

        else:
            return {'type': 'Error', 'result': f"A server with that name is already registered. Choose a different name."}

    def msgDelServer(self, ip, port, ipport, msg):
        if msg["serverName"] in self.serverlist:
            server = self.serverlist[msg["serverName"]]
            if server["serverPublicIP"] == ip and server["serverPublicPort"] == port:
                del self.serverlist[msg["serverName"]]
                return {'type': 'serverDeleted', 'result': f"Server is not registered."}
            else:
                return {'type': 'Error', 'result': f"Permission Denied."}
        else:
            return {'type': 'Error', 'result': f"Server is not registered."}

    def msgGetConnetInfo(self, ip, port, ipport, msg):
        if msg["serverName"] in self.serverlist:
            server = self.serverlist[msg["serverName"]]
            reply = {
                'type': 'connectInfo',
                'serverName': server["serverName"], 
                'clientPrivateIP': msg, 
                'clientPrivatePort': msg,
                'serverPrivateIP': server["serverPrivateIP"], 
                'serverPrivatePort': server["serverPrivatePort"],
                'clientPublicIP': ip, 
                'clientPublicPort': port,
                'serverPublicIP': server["serverPublicIP"], 
                'serverPublicPort': server["serverPublicPort"]
                }

            # send connectInfo to server.
            self.socket.sendMessage(
                reply,
                destinationIP=server["serverPublicIP"],
                destinationPort=server["serverPublicPort"]
                )

            # send connectInfo to client
            return reply
        else:
            return {'type': 'Error', 'result': f"Server is not registered."}
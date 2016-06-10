import asyncio
from autobahn.asyncio import wamp, websocket
import threading
import time
import socket


rsock, wsock = socket.socketpair()

class EyeComponent(wamp.ApplicationSession):
    def onConnect(self):
        self.join(u"realm1")

    @asyncio.coroutine
    def setup_socket(self):
        # Create a non-blocking socket
        self.sock = rsock
        self.sock.setblocking(0)
        loop = asyncio.get_event_loop()
        # Wait for connections to come in. When one arrives,
        # call the time service and disconnect immediately.
        while True:
            rcmd = yield from loop.sock_recv(rsock,80)
            yield from self.call_service(rcmd.decode())

    @asyncio.coroutine
    def onJoin(self, details):
        # Setup our socket server
        asyncio.async(self.setup_socket())


    @asyncio.coroutine
    def call_service(self,rcmd):
        print(rcmd)
        try:
           now = yield from self.call(rcmd)
        except Exception as e:
           print("Error: {}".format(e))
        else:
           print("Current time from time service: {}".format(now))



    def onLeave(self, details):
        self.disconnect()

    def onDisconnect(self):
        asyncio.get_event_loop().stop()
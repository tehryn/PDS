import socket
from threading import Thread, Condition
from Protokol import Protokol

class ConnectionKeeper( object ):
    def __init__( self, isNode ):
        self._isNode = isNode
        self._running = False
        self._cond = None
        self._thread = None

    def start( self, ip, port, helloPacket = None ):
        def _stillAlive( destIp, destPort, helloPacket ):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM )
            with self._cond:
                while self._running:
                    sock.sendto( Protokol.encode( str( helloPacket ) ), ( destIp, destPort ) )
                    self._cond.wait( 10 )

            sock.sendto( Protokol.encode( helloPacket.goodbye() ), ( destIp, destPort ) )
        if not self._running:
            self._running = True
            self._cond = Condition()
            self._thread = Thread( target = _stillAlive, args=( ip, port, helloPacket ) )
            self._thread.setDaemon( True )
            self._thread.start()

    def stop( self ):
        if self._running:
            self._running = False
            with self._cond:
                self._cond.notify()
            self._thread.join()

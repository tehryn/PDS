import socket
from threading import Thread

class Receiver( object ):
    def __init__( self, isNode ):
        self._supportedCommands = {
            'hello',
            'getlist',
            'list',
            'message',
            'update',
            'disconnect',
            'ack',
            'error'
        }
        self._noAck = { 'hello', 'update', 'error' }
        self._isNode = isNode
        self._running = False
        self._thread = None

    def start( self, ip, port ):
        def _listener( ip, port ):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM )
            sock.bind( (ip, port) )
            while self._running:
                data, addr = sock.recvfrom( 4096 )
                data = data.decode( 'utf-8' )
                print( 'Message from ' + addr[0] + ':' + str( addr[1] ) + ": " + data )

        if not self._running:
            self._running = True
            self._thread = Thread( target = _listener, args=( ip, port ) )
            self._thread.setDaemon( True )
            self._thread.start()

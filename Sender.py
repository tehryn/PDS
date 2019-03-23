import itertools
from time import sleep, time
from sys import stderr
from threading import Thread, Lock
from Protokol import Hello, Ack, Disconnect, Error, GetList, List, Message, Protokol, Update


class Sender( object ):
    def __init__( self, sock, lock ):
        self._sock = sock
        self._lock = lock
        self._running = True
        self._receivedAck = list()
        self._ackLock = Lock()
        self._ackTester = Thread( target = self._testAck, args=() )
        self._ackTester.setDaemon( True )
        self._ackTester.start()

    def _testAck( self ):
        while self._running:
            napTime = 2
            currTime = time()
            delete = list()
            for idx, item in enumerate( self._receivedAck ):
                if item[ 'received' ]:
                    delete.append( idx )
                elif item[ 'expires' ] <= currTime:
                    delete.append( idx )
                    message = 'Neobdrzel jsem ACK pro mou ' + item[ 'msgType' ].upper() + ' zpravu.'
                    errorPacket = Error( message )
                    self._send( Protokol.encode( errorPacket ), ( item[ 'addr' ][0], item[ 'addr' ][1] ) )
                    stderr.write( message + '\n' )
                else:
                    tmp = item[ 'expires' ] - currTime
                    if tmp < napTime:
                        napTime = tmp
            relative = 0
            for idx in delete:
                del self._receivedAck[ idx - relative ]
                relative += 1
            sleep( napTime )

    def _getAck( self, txid ):
        with self._lock:
            for idx, ack in enumerate( self._receivedAck ):
                if ( ack[ 'txid' ] == txid ):
                    return idx
        return None

    def ackExpected( self, txid, msgType, ip, port ):
        txid = str( txid )
        expires = time() + 2
        idx = self._getAck( txid )
        val = idx is None
        if val:
            with self._ackLock:
                self._receivedAck.append( { 'txid' : txid, 'received' : False, 'expires' : expires, 'msgType' : msgType, 'addr' : ( ip, port )  } )
        return val

    def ackReceived( self, txid ):
        txid = str( txid )
        idx = self._getAck( txid )
        if idx is not None:
            with self._ackLock:
                self._receivedAck[ idx ][ 'received' ] = True

    def hello( self, username, ipv4, port, destIp, destPort, goodbye = False ):
        packet = Hello( username, ipv4, str( port ) )
        if ( not goodbye ):
            self._send( Protokol.encode( packet ), (destIp, destPort) )
        else:
            self._send( Protokol.encode( packet.goodbye() ), (destIp, destPort) )
        return False

    def message( self, message, fr, to, destIp, destPort ):
        packet = Message(fr, to, message)
        self._send( Protokol.encode( packet ), (destIp, destPort) )
        return True

    def getlist( self, destIp, destPort ):
        packet = GetList()
        self._send( Protokol.encode( packet ), (destIp, destPort) )
        return True

    def list( self, peers, destIp, destPort ):
        packet = List( peers )
        self._send( Protokol.encode( packet ), (destIp, destPort) )
        return True

    def update( self, dbs, destIp, destPort ):
        packet = Update( dbs )
        self._send( Protokol.encode( packet ), (destIp, destPort) )
        return False

    def disconnect( self, destIp, destPort ):
        packet = Disconnect()
        self._send( Protokol.encode( packet ), (destIp, destPort) )
        return True

    def ack( self, txid, destIp, destPort ):
        packet = Ack( txid )
        self._send( Protokol.encode( packet ), (destIp, destPort) )
        return False

    def error( self, message, destIp, destPort ):
        packet = Error( message )
        self._send( Protokol.encode( packet ), (destIp, destPort) )
        return False

    def _bencode( self, obj ):
        if isinstance( obj, int ):
            return b"i" + str( obj ).encode( 'utf-8' ) + b"e"
        elif isinstance(obj, str):
            return self._bencode( obj.encode( "utf-8" ) )
        elif isinstance( obj, bytes ):
            return str( len( obj ) ).encode() + b":" + obj
        else:
            items = list( obj.items() )
            items.sort()
            data = b"d" + b"".join( map( self._bencode, itertools.chain(*items) ) ) + b"e"
        return data

    def _send( self, data, addr ):
        with self._lock:
            print( '>>>>>>' + str(addr) + ' ' + data )
            try:
                #obj = json.loads( data )
                #self._sock.sendto( b"i" + self._bencode( obj ) + b"e", addr )
                self._sock.sendto( data.encode( 'utf-8' ), addr )
            except:
                stderr.write( 'Unable to send message to ' + addr[0] + ': ' + str( addr[1] ) + '\n' )

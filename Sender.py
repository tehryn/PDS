"""
Author: Jiri Matejka -- xmatej52
Description: Sender sends messages to specified addresses and manage database of ack messages
"""
import json
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

    def hasAck( self, msgType, addr ):
        with self._ackLock:
            for ack in self._receivedAck:
                if ack[ 'msgType' ] == msgType and addr == ack[ 'addr' ] and ack[ 'received' ]:
                    return True
        return False

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

    def _send( self, data, addr ):
        with self._lock:
            #print( '>>>>>>' + str(addr) + ' ' + data )
            try:
                obj = json.loads( data )
                #print( self._bencode( obj ) )
                self._sock.sendto( Sender._bencode( obj ), addr )
                #self._sock.sendto( data.encode( 'utf-8' ), addr )
            except:
                stderr.write( 'Unable to send message to ' + addr[0] + ': ' + str( addr[1] ) + '\n' )

    @staticmethod
    def _bencode( obj ):
        items = list( obj.items() )
        items.sort()
        result = b'd'
        for key, value in items:
            if isinstance( value, int ):
                value = b'i' + str( value ).encode( 'utf-8' ) + b'e'
            elif isinstance( value, dict ):
                value = Sender._bencode( value )
            else:
                value = value.encode( 'utf-8' )
                value = str( len( value ) ).encode( 'utf-8' ) + b':' + value
            key = key.encode( 'utf-8' )
            key = str( len( key ) ).encode( 'utf-8' ) + b':' + key
            result += key + value
        return result + b'e'

    @staticmethod
    def decode( data ):
        obj, empty = Sender._decoder( data )
        if obj is None or empty:
            return None
        return obj

    @staticmethod
    def _decoder( data ):
        if isinstance( data, str ):
            data = data.encode( 'utf-8' )

        error = ( None, None )
        if not data or chr( data[0] ) != 'd' or chr( data[-1] ) != 'e':
            return error

        obj = dict()
        key = None
        data = data[1:]

        while chr( data[0] ) != 'e':
            if chr( data[ 0 ] ).isdigit():
                num = chr( data[0] )
                idx = 1
                while idx < len( data ) and chr( data[idx] ).isdigit():
                    num += chr( data[idx] )
                    idx += 1

                if idx == len( data ) or chr( data[ idx ] ) != ':':
                    return error

                data = data[idx:]
                num = int( num ) + 1

                if num == 0 or len( data ) < num:
                    return error

                if key is None:
                    key = data[1:num].decode( 'utf8' )
                else:
                    #obj[ key ] = json.loads( data[1:num].decode( 'utf8' ) )
                    obj[ key ] = data[1:num].decode( 'utf8' )
                    key = None
                data = data[num:]
            elif key is None:
                return error
            elif chr( data[0] ) == 'i':
                num = str()
                idx = 1
                while idx < len( data ) and chr( data[idx] ).isdigit():
                    num += chr( data[idx] )
                    idx += 1
                if idx == len( data ) or chr( data[ idx ] ) != 'e':
                    return error
                obj[ key ] = int( num )
                data = data[idx+1:]
                key = None
            elif chr( data[0] ) == 'd':
                value, data = Sender._decoder( data )

                if value is None:
                    return error

                obj[ key ] = value
                key = None
            else:
                return error
        return obj, data[1:]

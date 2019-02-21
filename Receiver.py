import socket
import json
import datetime
from threading import Thread
from Protokol import Hello, Ack, Disconnect, Error, GetList, List, Message, Protokol, Update
from Peer import Peer

class Receiver( object ):
    def __init__( self, isNode ):
        self._isNode = isNode
        self._running = False
        self._thread = None
        self._peers = list()
        self._db = list()
        self._mapper = dict()
        self._add2mapper = ( None, -1 )
        self._ackId = 0

    def start( self, sock, ip, port ):
        def _listener( sock, ip, port ):
            sock.bind( (ip, port) )
            noAck = { 'hello', 'update', 'error', '_unknown', 'ack' }
            while self._running:
                data, addr = sock.recvfrom( 4096 )
                mapperIdx = addr[0] + ':' + str( addr[1] )
                data = data.decode( 'utf-8' )
                print( str( datetime.datetime.now() ) + ': ' + str( addr ) + ": " + data )
                message = None
                try:
                    message = json.loads( data )
                except:
                    message = None

                isValid = False
                msgType = None
                answer  = ''
                if message is not None :
                    isValid, msgType = self.parseMessage( message )

                if msgType is None:
                    answer = "Invalid message format."
                    msgType = '_unknown'
                elif msgType == '_unknown':
                    answer = "Unknown type of message."
                elif not isValid:
                    answer = "Received '" + msgType +"' message with invalid syntax."
                elif msgType == 'hello' and self._add2mapper[0] is not None:
                    if self._add2mapper[1]:
                        self._mapper[ mapperIdx ] = ( self._peers[ -1 ].getIp(), self._peers[ -1 ].getPort() )
                    else:
                        if mapperIdx in self._mapper:
                            del self._mapper[ mapperIdx ]
                elif msgType == 'getlist':
                    answer = List().to_string( self._peers )
                else:
                    answer = "Received valid '" + msgType +"' message."

                if msgType not in noAck:
                    ackPacket = Ack( self._ackId )
                    sock.sendto( Protokol.encode( str( ackPacket ), False ), addr )

                if self._isNode:
                    if not isValid:
                        answer += " Received: " +'"' + data + '"'
                    if answer and mapperIdx in self._mapper:
                        sock.sendto( Protokol.encode( answer ), ( addr[0], int( self._mapper[ mapperIdx ][1] ) ) )

        if not self._running:
            self._running = True
            self._thread = Thread( target = _listener, args=( sock, ip, port ) )
            self._thread.setDaemon( True )
            self._thread.start()

    def parseMessage( self, message ):
        supportedCommands = {
            'hello' : self.hello,
            'getlist': self.getlist,
            'list' : self.list,
            'message' : self.message,
            'update' : self.update,
            'disconnect' : self.disconnect,
            'ack' : self.ack,
            'error' : self.error
        }
        if 'type' not in message:
            return False, None
        elif message[ 'type' ] not in supportedCommands:
            return False, '_unknown'
        else:
            return supportedCommands[ message[ 'type' ] ]( message ), message[ 'type' ]

    @staticmethod
    def _buildObj( message, keys ):
        for key, item in message.items():
            if key in keys and keys[ key ] is None:
                keys[ key ] = item
            else:
                return ( False, dict() )
        return ( True, keys )

    def getIdxOfUser( self, username ):
        for idx, peer in enumerate( self._peers ):
            if username == peer.getUsername():
                return idx
        return -1

    def getIdxOfNode( self, username ):
        for idx, peer in enumerate( self._db ):
            if username == peer.getUsername():
                return idx
        return -1

    def hello( self, message ):
        self._add2mapper = ( None, -1 )
        keys = { 'type' : None, 'username' : None, 'txid' : None, 'ipv4' : None, 'port' : None }
        valid, keys = Receiver._buildObj( message, keys )
        if not valid:
            return False
        self._ackId = keys[ 'txid' ]
        if self._isNode:
            idx = self.getIdxOfUser( keys[ 'username' ] )
            if keys[ 'ipv4' ] == '0.0.0.0' and keys[ 'port' ] == 0:
                if idx >= 0:
                    del self._peers[ idx ]
                    self._add2mapper = ( False, idx )
            else :
                peer = Peer( keys[ 'username' ], keys[ 'ipv4' ], str( keys[ 'port' ] ) )
                self._add2mapper = True
                if idx < 0:
                    self._peers.append( peer )
                    self._add2mapper = ( True, -1 )
                else:
                    self._peers[ idx ] = peer
                    self._add2mapper = ( True, idx )
        return True

    def message( self, message ):
        keys = { 'type' : None, 'txid' : None, 'from' : None,  'to' : None, 'message' : None }
        valid, keys = Receiver._buildObj( message, keys )
        if not valid:
            return False
        self._ackId = keys[ 'txid' ]
        if self._isNode:
            pass
        return True

    def getlist( self, message ):
        keys = { 'type' : None, 'txid' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._ackId = keys[ 'txid' ]
        return valid

    def list( self, message ):
        keys = { 'type' : None, 'txid' : None, 'peers' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._ackId = keys[ 'txid' ]
        if not valid:
            return False
        if self._isNode:
            pass
        return True

    def update( self, message ):
        keys = { 'type' : None, 'txid' : None, 'db' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._ackId = keys[ 'txid' ]
        if not valid:
            return False
        if self._isNode:
            pass
        return True

    def disconnect( self, message ):
        keys = { 'type' : None, 'txid' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._ackId = keys[ 'txid' ]
        if not valid:
            return False
        if self._isNode:
            pass
        return True

    def ack( self, message ):
        keys = { 'type' : None, 'txid' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._ackId = keys[ 'txid' ]
        if not valid:
            return False
        if self._isNode:
            pass
        return True

    def error( self, message ):
        keys = { 'type' : None, 'txid' : None, 'verbose' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._ackId = keys[ 'txid' ]
        if not valid:
            return False
        if self._isNode:
            pass
        return True

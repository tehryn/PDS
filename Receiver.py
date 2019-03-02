import json
import sys
from threading import Thread, Lock
from time import sleep, time
from Protokol import Protokol
from Peer import Peer

class Receiver( object ):
    def __init__( self, isNode, sender ):
        self._isNode = isNode
        self._running = False
        self._thread = None
        self._peers = list()
        self._db = list()
        self._obj = dict()
        self._kicker = None
        self._lock = Lock()
        self._sender = sender

    def start( self, sock, ip, port ):
        def _listener():
            self._running = True
            sock.bind( (ip, port) )
            while self._running:
                data, addr = sock.recvfrom( 4096 )
                data = data.decode( 'utf-8' )
                print( '<<<<<<' + str( addr ) + " " + data )
                message = None
                try:
                    message = json.loads( data )
                except:
                    message = None

                isValid = False
                msgType = None
                answer  = ''
                sendAck = False
                if message is not None :
                    isValid, msgType = self.parseMessage( message )
                if msgType is None:
                    answer = "Invalid message format."
                    msgType = '_unknown'
                if not isValid:
                    self._sender.error( 'Invalid syntax of received >' + msgType + '< message.', addr[0], addr[1] )
                elif msgType == '_unknown':
                    answer = "Unknown type of message."
                elif not isValid:
                    answer = "Received '" + msgType +"' message with invalid syntax."
                elif msgType == 'hello':
                    pass
                elif msgType == 'list':
                    if self._isNode:
                        self._sender.error( 'Command list is not supported on peer.', addr[0], addr[1] )
                    else:
                        sendAck = True
                elif msgType == 'getlist':
                    if self._isNode:
                        with self._lock:
                            self._sender.list( [ item[ 'peer' ] for item in self._peers ], addr[0], addr[1] )
                        self._sender.ackExpected( Protokol.getId(), 'getlist', addr[0], addr[1] ) #TODO zde je potreba zamek
                        sendAck = True
                    else:
                        self._sender.error( 'Command getList is not supported on peer.', addr[0], addr[1] )
                elif msgType == 'error':
                    sys.stderr.write( self._obj[ 'verbose' ] + '\n' )
                elif msgType == 'ack':
                    self._sender.ackReceived( self._obj[ 'txid' ] )
                else:
                    self._sender.error( 'Received valid message.', addr[0], addr[1] )

                if answer != '':
                    self._sender.error( answer, addr[0], addr[1] )

                if sendAck:
                    self._sender.ack( self._obj[ 'txid' ], addr[0], addr[1] )

        if not self._running:
            self._thread = Thread( target = _listener )
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
        for idx, item in enumerate( self._peers ):
            peer = item[ 'peer' ]
            if username == peer.getUsername():
                return idx
        return -1

    def getIdxOfNode( self, username ):
        for idx, peer in enumerate( self._db ):
            if username == peer.getUsername():
                return idx
        return -1

    def hello( self, message ):
        def _delete():
            napTime = 30
            self._lock.acquire()
            while self._peers:
                self._lock.release()
                print( 'Debug: Sleeping for ' + str( napTime ) )
                sleep( napTime )
                nextNap = 30
                self._lock.acquire()
                currTime = time()
                delete = list()
                for idx, item in enumerate( self._peers ):
                    if item[ 'expires' ] <= currTime:
                        delete.append( idx )
                    else:
                        tmp = item[ 'expires' ] - currTime
                        print( 'Debug: tmp=' + str( tmp ) )
                        if tmp < nextNap:
                            nextNap = tmp

                relative = 0
                for idx in delete:
                    print( 'Debug: Deleted ' + str( idx ) )
                    del self._peers[ idx - relative ]
                    relative += 1
                napTime = nextNap
                print( 'Debug: ' + str( [ str( x[ 'peer' ] ) for x in self._peers ] ) )
            self._kicker = None
            self._lock.release()

        keys = { 'type' : None, 'username' : None, 'txid' : None, 'ipv4' : None, 'port' : None }
        valid, keys = Receiver._buildObj( message, keys )
        if not valid:
            return False
        self._obj = keys
        if self._isNode:
            idx = self.getIdxOfUser( keys[ 'username' ] )
            if keys[ 'ipv4' ] == '0.0.0.0' and keys[ 'port' ] == 0:
                if idx >= 0:
                    del self._peers[ idx ]
            else :
                peer = Peer( keys[ 'username' ], keys[ 'ipv4' ], str( keys[ 'port' ] ) )
                expires = time() + 30
                with self._lock:
                    if idx < 0:
                        self._peers.append( { 'peer' : peer, 'expires':expires } )
                    else:
                        self._peers[ idx ] = { 'peer' : peer, 'expires':expires }
                    if self._kicker is None:
                        self._kicker = Thread( target = _delete )
                        self._kicker.setDaemon( True )
                        self._kicker.start()
        return True

    def message( self, message ):
        keys = { 'type' : None, 'txid' : None, 'from' : None,  'to' : None, 'message' : None }
        valid, keys = Receiver._buildObj( message, keys )
        if not valid:
            return False
        self._obj = keys
        if self._isNode:
            pass
        return True

    def getlist( self, message ):
        keys = { 'type' : None, 'txid' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._obj = keys
        return valid

    def list( self, message ):
        keys = { 'type' : None, 'txid' : None, 'peers' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._obj = keys
        if not valid:
            return False
        if not self._isNode:
            newDb = list()
            for _, peer in keys['peers'].items():
                peerKeys = { 'username' : None, 'ipv4' : None, 'port' : None }
                valid, peerKeys = Receiver._buildObj( peer, peerKeys )
                if valid:
                    newDb.append( Peer( peerKeys[ 'username' ], peerKeys[ 'ipv4' ], str( peerKeys[ 'port' ] ) ) )
                else:
                    return False
            self._db = newDb
        return True

    def update( self, message ):
        keys = { 'type' : None, 'txid' : None, 'db' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._obj = keys
        if not valid:
            return False
        if self._isNode:
            pass
        return True

    def disconnect( self, message ):
        keys = { 'type' : None, 'txid' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._obj = keys
        if not valid:
            return False
        if self._isNode:
            pass
        return True

    def ack( self, message ):
        keys = { 'type' : None, 'txid' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._obj = keys
        if not valid:
            return False
        if self._isNode:
            pass
        return True

    def error( self, message ):
        keys = { 'type' : None, 'txid' : None, 'verbose' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._obj = keys
        if not valid:
            return False
        if self._isNode:
            pass
        return True

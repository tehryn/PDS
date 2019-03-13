import json
import sys
from threading import Thread, Lock
from time import sleep, time
from Protokol import Protokol, Peer
from Functions import valid_ipv4, valid_port

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
        self._knownNodes = list()

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
                    print( "JSON error" )
                    message = None

                isValid = False
                msgType = None
                answer  = ''
                sendAck = False
                if message is not None :
                    isValid, msgType = self.parseMessage( message )
                if msgType is None:
                    answer = self._obj[ 'message' ]
                    msgType = '_unknown'
                elif not isValid:
                    answer = self._obj[ 'message' ]
                elif msgType == '_unknown':
                    answer = self._obj[ 'message' ]
                elif not isValid:
                    answer = self._obj[ 'message' ]
                elif msgType == 'hello':
                    pass
                elif msgType == 'list':
                    if self._isNode:
                        answer = 'Command list is not supported on Node.'
                    else:
                        sendAck = True
                elif msgType == 'getlist':
                    if self._isNode:
                        with self._lock:
                            self._sender.list( [ item[ 'peer' ] for item in self._peers ], addr[0], addr[1] )
                        self._sender.ackExpected( Protokol.getId(), 'getlist', addr[0], addr[1] ) #TODO zde je potreba zamek
                        sendAck = True
                    else:
                        answer = 'Command getList is not supported on peer.'
                elif msgType == 'error':
                    sys.stderr.write( self._obj[ 'verbose' ] + '\n' )
                elif msgType == 'ack':
                    self._sender.ackReceived( self._obj[ 'txid' ] )
                elif msgType == 'message':
                    if self._isNode:
                        answer = 'Command message is not supported on node.'
                    else:
                        sendAck = True
                elif msgType == 'update':
                    if self._isNode:
                        seek = addr[0] + ',' + str( addr[1] )
                        expires = time() + 12
                        for key, node in self._obj[ 'db' ].items():
                            srvIp, srvPort = key.split( ',', 2 )
                            if seek != key:
                                peers = node.getPeers()
                                for peer in peers:
                                    idx = self.getIdxOfUser( peer.getUsername )
                                    if idx < 0:
                                        self._peers.append( { 'peer' : peer, 'expires' : None, 'dbId' : key } )
                            else:
                                idx = self.getIdxOfNode( key )
                                if ( idx < 0 ):
                                    self._db.append( { 'db' : node, 'expires' : expires } )
                                    self._sender.update( [ x[ 'peer' ] for x in self._peers if x[ 'db' ] ], ip, port, srvIp, srvPort )
                                else:
                                    self._knownNodes[ idx ] = { 'ipv4' : srvIp, 'node' : node, }
                    else:
                        answer = 'Command update is not supported on peer'
                else:
                    answer = 'Received valid message.'

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
            self._obj = { 'message' : 'Type of message not specified.' }
            return False, None
        if isinstance( message[ 'type' ], str ) and message[ 'type' ] not in supportedCommands:
            self._obj = { 'message' : 'Unknown type of message.' }
            return False, '_unknown'

        return supportedCommands[ message[ 'type' ] ]( message ), message[ 'type' ]

    @staticmethod
    def _buildObj( message, keys ):
        for key, item in message.items():
            valid = True
            if key == 'txid':
                valid = isinstance( item, int ) and item >= 0
            elif key == 'port':
                valid = isinstance( item, int ) and valid_port( item )
            elif key == 'username':
                valid = bool( isinstance( item, str ) and item )
            elif key == 'ipv4':
                valid = isinstance( item, str ) and valid_ipv4( item )
            elif key == 'verbose':
                valid = bool( isinstance( item, str ) and item )
            elif key == 'from':
                valid = bool( isinstance( item, str ) and item )
            elif key == 'to':
                valid = bool( isinstance( item, str ) and item )
            if valid and ( key in keys ) and keys[ key ] is None:
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

    def getIdxOfNode( self, key ):
        for idx, node in enumerate( self._knownNodes ):
            node = node[ 'node' ]
            if key == node.getId():
                return idx
        return -1

    def hello( self, message ):
        def _delete():
            napTime = 30
            self._lock.acquire()
            while self._peers:
                self._lock.release()
                sleep( napTime )
                nextNap = 30
                self._lock.acquire()
                currTime = time()
                delete = list()
                for idx, item in enumerate( self._peers ):
                    if 'dbId' is not None:
                        if item[ 'expires' ] <= currTime:
                            delete.append( idx )
                        else:
                            tmp = item[ 'expires' ] - currTime
                            if tmp < nextNap:
                                nextNap = tmp

                relative = 0
                for idx in delete:
                    del self._peers[ idx - relative ]
                    relative += 1
                napTime = nextNap
            self._kicker = None
            self._lock.release()

        keys = { 'type' : None, 'username' : None, 'txid' : None, 'ipv4' : None, 'port' : None }
        valid, keys = Receiver._buildObj( message, keys )
        if not valid:
            self._obj = { 'message' : 'Invalid syntax of HELLO message.' }
            return False
        self._obj = keys
        if self._isNode:
            with self._lock:
                idx = self.getIdxOfUser( keys[ 'username' ] )
                if keys[ 'ipv4' ] == '0.0.0.0' and keys[ 'port' ] == 0:
                    if idx >= 0 and self._peers[ idx ][ 'dbId' ] is None:
                        del self._peers[ idx ]
                    else:
                        self._obj = { 'message' : 'Unauthorized use of HELLO message.' }
                        return False
                else :
                    peer = Peer( keys[ 'username' ], keys[ 'ipv4' ], str( keys[ 'port' ] ) )
                    expires = time() + 30
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
            self._obj = { 'message' : 'Invalid syntax of MESSAGE message.' }
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
            self._obj = { 'message' : 'Invalid syntax of LIST message.' }
            return False
        if not self._isNode:
            newDb = list()
            if not isinstance( keys[ 'peers' ], dict ):
                self._obj = { 'message' : 'Invalid syntax of LIST message (invalid peer record).' }
                return False
            for _, peer in keys['peers'].items():
                peerKeys = { 'username' : None, 'ipv4' : None, 'port' : None }
                valid, peerKeys = Receiver._buildObj( peer, peerKeys )
                if valid:
                    newDb.append( Peer( peerKeys[ 'username' ], peerKeys[ 'ipv4' ], str( peerKeys[ 'port' ] ) ) )
                else:
                    self._obj = { 'message' : 'Invalid syntax of LIST message (invalid peer record).' }
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
            if not isinstance( keys[ 'db' ], dict ):
                return False
            for key in keys[ 'db' ]:
                ip = port = None
                try:
                    ip, port = key.split( ',', 2 )
                except:
                    self._obj = { 'message' : 'Invalid syntax of UPDATE message (invalid db record).' }
                    return False

                if not valid_ipv4( ip ) or not valid_port( port ):
                    self._obj = { 'message' : 'Invalid syntax of UPDATE message (invalid ipv4 or port in db record).' }
                    return False

                if not isinstance( keys[ 'db' ][ key ], dict ):
                    self._obj = { 'message' : 'Invalid syntax of UPDATE message (invalid peer record in db record).' }
                    return False

                newDb = list()
                for _, peer in keys[ 'db' ][ key ].items():
                    peerKeys = { 'username' : None, 'ipv4' : None, 'port' : None }
                    valid, peerKeys = Receiver._buildObj( peer, peerKeys )
                    if valid:
                        newDb.append( Peer( peerKeys[ 'username' ], peerKeys[ 'ipv4' ], str( peerKeys[ 'port' ] ) ) )
                    else:
                        self._obj = { 'message' : 'Invalid syntax of UPDATE message (invalid peer record in db record).' }
                        return False
                self._obj[ 'db' ][ key] = newDb
                print( self._obj )
        return True

    def disconnect( self, message ):
        keys = { 'type' : None, 'txid' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._obj = keys
        if not valid:
            self._obj = { 'message' : 'Invalid syntax of DISCONNECT message.' }
            return False
        if self._isNode:
            pass
        return True

    def ack( self, message ):
        keys = { 'type' : None, 'txid' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._obj = keys
        if not valid:
            self._obj = { 'message' : 'Invalid syntax of ACK message.' }
            return False
        if self._isNode:
            pass
        return True

    def error( self, message ):
        keys = { 'type' : None, 'txid' : None, 'verbose' : None }
        valid, keys = Receiver._buildObj( message, keys )
        self._obj = keys
        if not valid:
            self._obj = { 'message' : 'Invalid syntax of ERROR message.' }
            return False
        if self._isNode:
            pass
        return True

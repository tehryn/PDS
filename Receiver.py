import json
import sys
from threading import Thread, Lock
from time import sleep, time
from Protokol import Protokol, Peer, Db
from Functions import valid_ipv4, valid_port
from Sender import Sender

class Receiver( object ):
    def __init__( self, ip, port, isNode, sender, username = None ):
        self._isNode = isNode
        self._thread = None
        self._peers = list()
        self._db = list()
        self._obj = dict()
        self._lock = Lock()
        self._sender = sender
        self._ip = ip
        self._port = port
        if self._isNode:
            self._bouncer = Thread( target = self._delete )
            self._bouncer.setDaemon( True )
            self._bouncer.start()
        self._username = username

    def procCommand( self, cmd, addr=(None, None) ):
        supportedCommands = dict()
        if self._isNode:
            supportedCommands = {
                'database' : { 'type' : None },
                'neighbors' : { 'type' : None },
                'connect' : { 'type' : None, 'ipv4' : None, 'port' : None },
                'disconnect' : { 'type' : None },
                'sync' : { 'type' : None }
            }
            if cmd[ 'type' ] not in supportedCommands:
                return None, None
            valid, cmd = self.buildObj( cmd, supportedCommands[ cmd[ 'type' ] ] )
            if not valid:
                return None, None
            if cmd[ 'type' ] == 'sync':
                with self._lock:
                    dbs = [ db[ 'node' ] for db in self._db ]
                    newDb = Db( self._ip, self._port )
                    newDb.update( [ x[ 'peer' ] for x in self._peers if x[ 'dbId' ] is None ] )
                    dbs.append( newDb )
                    for item in self._db:
                        ip, port = item[ 'node' ].getAddr()
                        self._sender.update( dbs, ip, port )
                return True, None
            if cmd[ 'type' ] == 'connect':
                with self._lock:
                    dbs = [ db[ 'node' ] for db in self._db ]
                    newDb = Db( self._ip, self._port )
                    newDb.update( [ x[ 'peer' ] for x in self._peers if x[ 'dbId' ] is None ] )
                    dbs.append( newDb )
                    self._sender.update( dbs, cmd[ 'ipv4' ], int( cmd[ 'port' ] ) )
                return True, None
            elif cmd[ 'type' ] == 'disconnect':
                with self._lock:
                    for item in self._db:
                        srvIp, srvPort = item[ 'node' ].getId().split( ',', 2 )
                        self._sender.disconnect( srvIp, int( srvPort ) )
                    self._db = list()
                    self._peers = [ peer for peer in self._peers if peer[ 'dbId' ] is None ]
                return True, None
            elif cmd[ 'type' ] == 'database':
                head = 'Uzivatele:\n'
                body = '  Registrovano na tomto uzlu:\n    '
                peers = [ peer[ 'peer' ].getUsername() for peer in self._peers if peer[ 'dbId' ] is None ]
                if peers:
                    body += '\n    '.join( peers ) + '\n'
                else:
                    body += 'Nejsou zde registrovani zadni uzivatele.\n'
                for db in self._db:
                    #peers = db[ 'node' ].getPeers()
                    #peers = [ x.getUsername() for x in peers  ]
                    addr  = db[ 'node' ].getAddr()
                    peers = [ peer[ 'peer' ].getUsername() for peer in self._peers if peer[ 'dbId' ] == db[ 'node' ].getId() ]
                    body += '  Registrovano na uzlu ' + addr[0] + ':' + str( addr[1] ) + '\n    '
                    if peers:
                        body += '\n    '.join( peers ) + '\n'
                    else:
                        body += 'Nejsou zde registrovani zadni uzivatele.\n'
                return True, head + body[:-1]
            elif cmd[ 'type' ] == 'neighbors':
                body = 'Uzly:\n  '
                nodes = [ node[ 'node' ].getId().replace( ',', ':' ) for node in self._db ]
                if nodes:
                    body += '\n  '.join( nodes ) + '\n'
                else:
                    body += '  Uzel nema zadne sousedy.\n'
                return True, body[:-1]

        else:
            supportedCommands = {
                'message' : { 'type' : None, 'from' : None, 'to' : None, 'message' : None },
                'getlist' : { 'type' : None },
                'peers' : { 'type' : None },
                'reconnect' : { 'type' : None, 'ipv4' : None, 'port' : None }
            }
            if cmd[ 'type' ] not in supportedCommands:
                return None, None
            valid, cmd = self.buildObj( cmd, supportedCommands[ cmd[ 'type' ] ] )
            if not valid:
                return None, None
            if cmd[ 'type' ] == 'message':
                with self._lock:
                    idx = self.getIdxOfUser( cmd[ 'to' ] )
                    if idx < 0:
                        return False, 'Nelze dorucit zpravu - neznamy uzivatel.'
                    self._sender.message( cmd['message'], cmd['from'], cmd['to'], self._peers[ idx ][ 'peer' ].getIp(), int(self._peers[ idx ][ 'peer' ].getPort()) )
                    self._sender.ackExpected( Protokol.getId(), 'message', addr[0], addr[1] )
                return True, None
            if cmd[ 'type' ] == 'getlist':
                with self._lock:
                    self._sender.getlist( addr[0], addr[1] )
                    self._sender.ackExpected( Protokol.getId(), 'getlist', addr[0], addr[1] )
                return True, None
            if cmd[ 'type' ] == 'peers':
                with self._lock:
                    if self._peers:
                        head = 'Uzivatele:\n  '
                        peers = [ x[ 'peer' ].getUsername() for x in self._peers ]
                        return True, head + '\n  '.join( peers )
                return True, 'V databazi se nenachazi jediny uzivatel, pro synchronizaci databaze pouzijte prikaz getlist.'
            if cmd[ 'type' ] == 'reconnect':
                return True, cmd
        return None, None

    def start( self, sock ):
        def _listener():
            # napojeni na port
            while True:
                data, addr = sock.recvfrom( 4096 )
                #data = data.decode( 'utf-8' )
                #print( b'<<<<<<' + str( addr ).encode( 'utf-8' ) + b" " + data )
                #message = json.loads( data )
                answer  = ''
                message = Sender.decode( data )
                if message is None:
                    answer = 'Zprava neni spravne zakodovana (chyba behem zpracovani BENCODE).'
                print( '<<<<<<' + str( addr ) + " " + str(message) )
                isValid = False
                msgType = None
                if message is not None :
                    isValid, msgType = self.parseMessage( message )
                if msgType is None:
                    if 'message' in self._db:
                        answer = self._obj[ 'message' ]
                    else:
                        answer = 'Neznamy typ zpravy.'
                    msgType = '_unknown'
                elif not isValid:
                    print( self._obj )
                    answer = self._obj[ 'message' ]
                elif msgType == '_unknown':
                    answer = self._obj[ 'message' ]
                elif not isValid:
                    answer = self._obj[ 'message' ]
                elif msgType == 'hello':
                    pass
                elif msgType == 'list':
                    if self._isNode:
                        answer = 'Prikaz LIST neni na uzlu podporovan'
                    else:
                        if self._sender.hasAck( 'getlist', addr ):
                            self._peers = [ { 'peer' : x  } for x in self._obj[ 'peers' ] ]
                            self._sender.ack( self._obj[ 'txid' ], addr[0], addr[1] )
                        else:
                            answer = 'Obdrzel jsem prikaz LIST, ale stale jsem neobdrzel ACK na muj prikaz GETLIST.'
                elif msgType == 'getlist':
                    if self._isNode:
                        with self._lock:
                            if ( self.getIdxOfUserByAddr( addr ) >= 0 ):
                                self._sender.ack( self._obj[ 'txid' ], addr[0], addr[1] )
                                self._sender.list( [ item[ 'peer' ] for item in self._peers[:] ], addr[0], addr[1] )
                                self._sender.ackExpected( Protokol.getId(), 'list', addr[0], addr[1] )
                            else:
                                answer = 'Pred prikazem GETLIST je treba se zaregistrovat pomoci HELLO zpravy.'
                    else:
                        answer = 'Prikaz GETLIST neni na peeru podporovan'
                elif msgType == 'error':
                    sys.stderr.write( self._obj[ 'verbose' ] + '\n' )
                elif msgType == 'ack':
                    self._sender.ackReceived( self._obj[ 'txid' ] )
                elif msgType == 'message':
                    if self._isNode:
                        answer = 'Prikaz MESSAGE neni na uzlu podporovan.'
                    else:
                        if self._username == self._obj[ 'to' ]:
                            self._sender.ack( self._obj[ 'txid' ], addr[0], addr[1] )
                            print( self._obj[ 'from' ] + ':' + self._obj[ 'message' ] )
                        else:
                            answer = 'Nelze zpracovat prikaz MESSAGE - nejsem adresatem.'
                elif msgType == 'update':
                    if self._isNode:
                        seek = addr[0] + ',' + str( addr[1] )
                        expires = time() + 12
                        with self._lock:
                            for key, node in self._obj[ 'db' ].items():
                                srvIp, srvPort = key.split( ',', 2 )
                                if seek == key:
                                    peers = node.getPeers()
                                    self._peers = [ x for x in self._peers if x[ 'dbId' ] is None or x[ 'dbId' ] != key ]
                                    for peer in peers:
                                        idx = self.getIdxOfUser( peer.getUsername() )
                                        if idx < 0:
                                            self._peers.append( { 'peer' : peer, 'expires' : None, 'dbId' : key } )
                                    idx = self.getIdxOfNode( key )
                                    if ( idx < 0 ):
                                        self._db.append( { 'ipv4' : srvIp, 'port' : srvPort, 'node' : node, 'expires' : expires } )
                                    else:
                                        self._db[idx] = { 'ipv4' : srvIp, 'port' : srvPort, 'node' : node, 'expires' : expires }
                                elif srvIp != self._ip or int( srvPort ) != self._port:
                                    idx = self.getIdxOfNode( key )
                                    if ( idx < 0 ):
                                        self._db.append( { 'ipv4' : srvIp, 'port' : srvPort, 'node' : node, 'expires' : expires } )
                    else:
                        answer = 'Prikaz UPDATE neni na peeru podporovan'
                elif msgType == 'disconnect':
                    with self._lock:
                        seek = addr[0] + ',' + str( addr[1] )
                        idx = self.getIdxOfNode( seek )
                        if idx < 0:
                            answer = 'Nelze se odhlasit - uzel neni registrovan v databazi.'
                        else:
                            self._peers = [ peer for peer in self._peers if peer[ 'dbId' ] is not None or peer[ 'dbId' ] != seek ]
                            del self._db[ idx ]
                else:
                    raise NotImplementedError( 'Prikaz ' + msgType + ' neni implementovan!' ) #TODO predelat na pass

                if answer != '':
                    self._sender.error( answer, addr[0], addr[1] )
        try:
            sock.bind( ( self._ip, self._port ) )
            self._thread = Thread( target = _listener)
            self._thread.setDaemon( True )
            self._thread.start()
            return True
        except:
            return False

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
            self._obj = { 'message' : 'Typ zpravy neni specifikovan.' }
            return False, None
        if isinstance( message[ 'type' ], str ) and message[ 'type' ] not in supportedCommands:
            self._obj = { 'message' : 'Neznamy typ zpravy.' }
            return False, '_unknown'
        return supportedCommands[ message[ 'type' ] ]( message ), message[ 'type' ]

    def _delete( self ):
        napTime = 12
        self._lock.acquire()
        while True:
            self._lock.release()
            sleep( napTime )
            nextNap = 30 if self._peers else 12
            self._lock.acquire()
            currTime = time()
            delete = list()
            for idx, item in enumerate( self._peers ):
                if item['dbId'] is None:
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

            delete = list()
            for idx, item in enumerate( self._db ):
                if item[ 'expires' ] <= currTime:
                    delete.append( idx )
                else:
                    tmp = item[ 'expires' ] - currTime
                    if tmp < nextNap:
                        nextNap = tmp

            keys2delte = set()
            relative = 0
            for idx in delete:
                keys2delte.add( self._db[ idx - relative ][ 'node' ].getId() )
                del self._db[ idx - relative ]
                relative += 1

            relative = 0
            for i, item in enumerate( self._peers ):
                if item[ 'dbId' ] is not None and item[ 'dbId' ] in keys2delte:
                    del self._peers[ i - relative ]
                    relative += 1

            napTime = nextNap

    @staticmethod
    def buildObj( message, keys ):
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

    def getIdxOfUserByAddr( self, addr ):
        for idx, item in enumerate( self._peers ):
            peer = item[ 'peer' ]
            if addr[0] == peer.getIp() and addr[1] == int( peer.getPort() ):
                return idx
        return -1

    def getIdxOfNode( self, key ):
        for idx, node in enumerate( self._db ):
            node = node[ 'node' ]
            if key == node.getId():
                return idx
        return -1

    def hello( self, message ):
        keys = { 'type' : None, 'username' : None, 'txid' : None, 'ipv4' : None, 'port' : None }
        valid, keys = Receiver.buildObj( message, keys )
        if not valid:
            self._obj = { 'message' : 'Neplatny syntax zpravy HELLO.' }
            return False
        self._obj = keys
        if self._isNode:
            with self._lock:
                idx = self.getIdxOfUser( keys[ 'username' ] )
                if keys[ 'ipv4' ] == '0.0.0.0' and keys[ 'port' ] == 0:
                    if idx >= 0 and self._peers[ idx ][ 'dbId' ] is None:
                        del self._peers[ idx ]
                    else:
                        self._obj = { 'message' : 'Nelze se odhlasit - uzivatel neni na uzlu prihlasen' }
                        return False
                else :
                    peer = Peer( keys[ 'username' ], keys[ 'ipv4' ], str( keys[ 'port' ] ) )
                    expires = time() + 30
                    if idx < 0:
                        self._peers.append( { 'peer' : peer, 'expires' : expires, 'dbId' : None } )
                    else:
                        self._peers[ idx ] = { 'peer' : peer, 'expires' : expires, 'dbId' : None }
        return True

    def message( self, message ):
        keys = { 'type' : None, 'txid' : None, 'from' : None,  'to' : None, 'message' : None }
        valid, keys = Receiver.buildObj( message, keys )
        if not valid:
            self._obj = { 'message' : 'Neplatny syntax zpravy MESSAGE.' }
            return False
        self._obj = keys
        if self._isNode:
            pass
        return True

    def getlist( self, message ):
        keys = { 'type' : None, 'txid' : None }
        valid, keys = Receiver.buildObj( message, keys )
        self._obj = keys
        return valid

    def list( self, message ):
        keys = { 'type' : None, 'txid' : None, 'peers' : None }
        valid, keys = Receiver.buildObj( message, keys )
        self._obj = keys
        if not valid:
            self._obj = { 'message' : 'Neplatny syntax zpravy LIST.' }
            return False
        if not self._isNode:
            newDb = list()
            if not isinstance( keys[ 'peers' ], dict ):
                self._obj = { 'message' : 'Neplatny syntax zpravy LIST (neplatny zaznam PEER RECORD).' }
                return False
            for _, peer in keys['peers'].items():
                peerKeys = { 'username' : None, 'ipv4' : None, 'port' : None }
                valid, peerKeys = Receiver.buildObj( peer, peerKeys )
                if valid:
                    newDb.append( Peer( peerKeys[ 'username' ], peerKeys[ 'ipv4' ], str( peerKeys[ 'port' ] ) ) )
                else:
                    self._obj = { 'message' : 'Neplatny syntax zpravy LIST (neplatny zaznam PEER RECORD).' }
                    return False
            self._obj[ 'peers' ] = newDb
        return True

    def update( self, message ):
        keys = { 'type' : None, 'txid' : None, 'db' : None }
        valid, keys = Receiver.buildObj( message, keys )
        self._obj = keys
        if not valid:
            self._obj = { 'message' : 'neplatny syntax zpravy UPDATE.' }
            return False
        if self._isNode:
            if not isinstance( keys[ 'db' ], dict ):
                return False
            for key in keys[ 'db' ]:
                ip = port = None
                try:
                    ip, port = key.split( ',', 2 )
                except:
                    self._obj = { 'message' : 'neplatny syntax zpravy UPDATE (neplatny zaznam DB RECORD).' }
                    return False

                if not valid_ipv4( ip ) or not valid_port( port ):
                    self._obj = { 'message' : 'neplatny syntax zpravy UPDATE (neplatny zaznam DB RECORD).' }
                    return False

                if not isinstance( keys[ 'db' ][ key ], dict ):
                    self._obj = { 'message' : 'neplatny syntax zpravy UPDATE (neplatny zaznam DB RECORD).' }
                    return False

                peers = list()
                for _, peer in keys[ 'db' ][ key ].items():
                    peerKeys = { 'username' : None, 'ipv4' : None, 'port' : None }
                    valid, peerKeys = Receiver.buildObj( peer, peerKeys )
                    if valid:
                        peers.append( Peer( peerKeys[ 'username' ], peerKeys[ 'ipv4' ], str( peerKeys[ 'port' ] ) ) )
                    else:
                        self._obj = { 'message' : 'neplatny syntax zpravy MESSAGE (neplatny zaznam PEER RECORD uvnitr zaznamu DB RECORD).' }
                        return False
                with self._lock:
                    self._obj[ 'db' ][ key ] = Db( ip, port )
                    self._obj[ 'db' ][ key ].update( peers )
        return True

    def disconnect( self, message ):
        keys = { 'type' : None, 'txid' : None }
        valid, keys = Receiver.buildObj( message, keys )
        self._obj = keys
        if not valid:
            self._obj = { 'message' : 'Neplatny syntax zpravy DISCONNECT.' }
            return False
        if self._isNode:
            pass
        return True

    def ack( self, message ):
        keys = { 'type' : None, 'txid' : None }
        valid, keys = Receiver.buildObj( message, keys )
        self._obj = keys
        if not valid:
            self._obj = { 'message' : 'Neplatny syntax zpravy ACK.' }
            return False
        if self._isNode:
            pass
        return True

    def error( self, message ):
        keys = { 'type' : None, 'txid' : None, 'verbose' : None }
        valid, keys = Receiver.buildObj( message, keys )
        self._obj = keys
        if not valid:
            self._obj = { 'message' : 'Neplatny syntax zpravy ERROR.' }
            return False
        if self._isNode:
            pass
        return True

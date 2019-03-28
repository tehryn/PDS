from threading import Lock
from json import dumps

class Protokol( object ):
    _id = 0
    _lock = Lock()

    def __init__( self ):
        pass

    def getObj( self ):
        pass

    @staticmethod
    def encode( packet, inc = True ):
        if inc:
            with Protokol._lock:
                if Protokol._id >= 65535:
                    Protokol._id = 0
                Protokol._id += 1
        #return str( packet ).encode( 'utf-8' )
        return str( packet )

    @staticmethod
    def getId():
        return Protokol._id

    def __str__( self ):
        pass

class Hello( Protokol ):
    def __init__( self, username, ip, port ):
        super().__init__()
        self._username = username
        self._ip = ip
        self._port = port

    def getObj( self ):
        return { 'username' : self._username, 'ip' : self._ip, 'port' : self._port }

    def goodbye( self ):
        return '{"type":"hello", "txid":' + str( Protokol._id ) + ', "username":' + dumps( self._username ) + ', "ipv4":"0.0.0.0", "port":0}'

    def __str__( self ):
        return '{"type":"hello", "txid":' + str( Protokol._id ) + ', "username":' + dumps( self._username ) + ', "ipv4":"' + self._ip + '", "port": ' + self._port + '}'

class GetList( Protokol ):
    def __str__( self ):
        return '{"type":"getlist", "txid":' + str( Protokol._id ) + '}'

class List( Protokol ):
    def __init__( self, peers ):
        super().__init__()
        self._peers = peers

    def __str__( self ):
        return '{"type":"list", "txid":'+ str( Protokol._id ) +', "peers":{' + Peer.peerRecord( self._peers ) + '}}'

class Message( Protokol ):
    def __init__( self, fr, to, msg ):
        super().__init__()
        self._from = fr
        self._to   = to
        self._message = msg

    def __str__( self ):
        return '{"type":"message", "txid":'+ str( Protokol._id ) +', "from":'+ dumps( self._from ) +', "to":'+ dumps( self._to ) +', "message":'+ dumps( self._message ) +'}'

class Update( Protokol ):
    def __init__( self, dbs ):
        super().__init__()
        self._dbs = dbs

    def __str__( self ):
        return '{"type":"update", "txid":'+ str( Protokol._id ) +', "db":{' + Db.DbRecord( self._dbs ) + '}}'

class Disconnect( Protokol ):
    def __str__( self ):
        return '{"type":"disconnect", "txid":'+ str( Protokol._id ) +'}'

class Ack( Protokol ):
    def __init__( self, txid ):
        super().__init__()
        self._txid = txid

    def __str__( self ):
        return '{"type":"ack", "txid":'+ str( self._txid ) +'}'

class Error( Protokol ):
    def __init__( self, verbose ):
        super().__init__()
        self._verbose = verbose

    def __str__( self ):
        return '{"type":"error", "txid":'+ str( Protokol._id ) +', "verbose":'+ dumps( self._verbose ) +'}'

class Peer( object ):
    def __init__( self, username, ip, port ):
        self._username = username
        self._ip = ip
        self._port = port

    def __str__( self ):
        return '{"username":' + dumps( self._username ) + ', "ipv4":"' + self._ip + '", "port":' + self._port + '}'

    def getUsername( self ):
        return self._username

    def getIp( self ):
        return self._ip

    def getPort( self ):
        return self._port

    @staticmethod
    def peerRecord( peers ):
        result = []
        idx   = 0
        for peer in peers:
            result.append( '"' + str( idx ) + '":' + str( peer ) )
            idx += 1
        return ', '.join( result )

class Db( object ):
    def __init__( self, ipv4, port ):
        self._ipv4 = ipv4
        self._port = str(port)
        self._peers = list()

    def update( self, peers ):
        self._peers = peers

    def getPeers( self ):
        return self._peers

    def getAddr( self ):
        return ( self._ipv4, int( self._port ) )

    def getId( self ):
        return self._ipv4 + ',' + self._port

    def __str__( self ):
        return '"' + self.getId() + '":{' + Peer.peerRecord( self._peers ) + '}'

    @staticmethod
    def DbRecord( dbs ):
        result = []
        for db in dbs:
            result.append( str( db ) )
        return ', '.join( result )

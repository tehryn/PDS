from threading import Lock

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
                Protokol._id += 1
        return str( packet ).encode( 'utf-8' )

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
        return '{"type":"hello", "txid":' + str( Protokol._id ) + ', "username":"' + self._username + '", "ipv4":"0.0.0.0", "port":0}'

    def __str__( self ):
        return '{"type":"hello", "txid":' + str( Protokol._id ) + ', "username":"' + self._username + '", "ipv4":"' + self._ip + '", "port": ' + self._port + '}'

class GetList( Protokol ):
    def __str__( self ):
        return '{"type":"getlist", "txid":' + str( Protokol._id ) + '}'

class List( Protokol ):
    def __init__( self, peers ):
        super().__init__()
        self._peers = peers

    def __str__( self ):
        peers = []
        idx   = 0
        for peer in self._peers:
            peers.append( '"' + str( idx ) + '":' + str( peer ) )
            idx += 1
        peers = ', '.join( peers )
        return '{"type":"list", "txid":'+ str( Protokol._id ) +', "peers":{' + peers + '}}'

class Message( Protokol ):
    def __init__( self, fr, to, msg ):
        super().__init__()
        self._from = fr
        self._to   = to
        self._message = msg

    def __str__( self ):
        return '{"type":"message", "txid":'+ str( Protokol._id ) +', "from":"'+ self._from +'", "to":"'+ self._to +'", "message":"'+ self._message +'"}'

class Update( Protokol ):
    def __init__( self, nodes ):
        super().__init__()
        self._nodes = nodes

    def __str__( self ):
        dbs = []
        idx   = 0
        for node in self._nodes:
            dbs.append( '"' + str( idx ) + '":' + str( node ) )
            idx += 1
        dbs = ', '.join( dbs )
        return '{"type":"update", "txid":'+ str( Protokol._id ) +', "db":{' + dbs + '}}'

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
        return '{"type":"error", "txid":'+ str( Protokol._id ) +', "verbose": "'+ self._verbose +'"}'

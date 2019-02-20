from threading import Lock

class Protokol( object ):
    _id = 0
    _lock = Lock()
    
    def __init__( self ):
        pass

    @staticmethod
    def encode( message, inc = True ):
        if inc:
            with Protokol._lock:
                Protokol._id += 1
        return message.encode( 'utf-8' )

    def __str__( self ):
        pass

class Hello( Protokol ):
    def __init__( self, username, ip, port ):
        super().__init__()
        self._username = username
        self._ip = ip
        self._port = port

    def goodbye( self ):
        return '{"type":"hello", "txid":' + str( Protokol._id ) + ', "username":"' + self._username + '", "ipv4":"0.0.0.0", "port": ' + self._port + '}'

    def __str__( self ):
        return '{"type":"hello", "txid":' + str( Protokol._id ) + ', "username":"' + self._username + '", "ipv4":"' + self._ip + '", "port": ' + self._port + '}'

class GetList( Protokol ):
    def __str__( self ):
        return '{"type":"getlist", "txid":' + str( Protokol._id ) + '}'

class List( Protokol ):
    def __init__( self ):
        super().__init__()
        self._peers = []

    def to_string( self, peers ):
        self._peers = peers
        return str( self )

    def __str__( self ):
        peers = []
        idx   = 0
        for peer in self._peers:
            peers.append( '"' + str( idx ) + '":' + str( peer ) )
            idx += 1
        peers = ', '.join( peers )
        return '{"type":"list", "txid":'+ str( Protokol._id ) +', "peers":{' + peers + '}}'

class Message( Protokol ):
    def __init__( self ):
        super().__init__()
        self._from = ""
        self._to   = ""
        self._message = ""

    def to_string( self, fr, to, message ):
        super().__init__()
        self._from = fr
        self._to   = to
        self._message = message
        return str( self )

    def __str__( self ):
        return '{"type":"message", "txid":'+ str( Protokol._id ) +', "from":"'+ self._from +'", "to":"'+ self._to +'", "message":"'+ self._message +'"}'

class Update( Protokol ):
    def __init__( self ):
        super().__init__()
        self._nodes = []

    def to_string( self, nodes ):
        self._nodes = nodes
        return str( self )

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
    def __str__( self ):
        return '{"type":"ack", "txid":'+ str( Protokol._id ) +'}'

class Error( Protokol ):
    def __init__( self ):
        super().__init__()
        self._verbose = ""

    def to_string( self, verbose ):
        self._verbose = verbose
        return str( self )

    def __str__( self ):
        return '{"type":"error", "txid":'+ str( Protokol._id ) +', "verbose": "'+ self._verbose +'"}'

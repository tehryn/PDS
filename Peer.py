class Peer( object ):
    def __init__( self, username, ip, port ):
        self._username = username
        self._ip = ip
        self._port = port

    def __str__( self ):
        return '{"username":"' + self._username + '", "ipv4": "' + self._ip + '", "port": ' + self._port + '}'

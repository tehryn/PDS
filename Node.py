import json

class Db( object ):
    def __init__( self, nodeIp, username, ip, port ):
        self._nodeIp = nodeIp
        self._username = username
        self._ip = ip
        self._port = port
    
    def __str__( self ):
        return '{"node":"' + self._nodeIp + '", "username":"' + self._username + '", "ipv4": "' + self._ip + '", "port": ' + self._port + '}'

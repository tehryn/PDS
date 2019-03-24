import os
import json
import sys
from time import sleep
from threading import Thread, Lock, Condition
from FileLock import FileLock
from Functions import find_nth, valid_ipv4, valid_port

class InputReader( object ):
    def __init__( self, filename, username = None ):
        self._lock = Lock()
        self._commands = list()
        self._fileReader = Thread( target = self._file, args=[ filename ] )
        if username is None:
            self._stdinReader = Thread( target = self._stdinNode )
        else:
            self._stdinReader = Thread( target = self._stdinPeer, args = [ username ] )
        self._stdinReader.setDaemon( True )
        self._fileReader.setDaemon( True )
        self._stdinReader.start()
        self._fileReader.start()
        self._cond = Condition()

    def _file( self, filename ):
        fLock = FileLock( filename )
        with fLock:
            if os.path.isfile( filename ):
                os.unlink( filename )
        while True:
            lines = list()
            with fLock:
                if os.path.isfile( filename ):
                    with open( filename, 'r' ) as file:
                        lines = file.readlines()
                    os.unlink( filename )
            for line in lines:
                cmd = None
                try:
                    cmd = json.loads( line )
                    if 'type' in cmd:
                        self._append( cmd )
                    else:
                        self._append( { 'type' : 'error', 'verbose' : 'Neplatny syntax prikazu - prikaz neobsahuje "type".' } )
                except:
                    self._append( { 'type' : 'error', 'verbose' : 'Neplatny syntax prikazu - prikaz neni ve formatu JSON.' } )
            sleep( 0.5 )

    def _stdinPeer( self, username ):
        while True:
            line = sys.stdin.readline().strip()
            if line.startswith( '\\' ):
                if line.startswith( '\\w' ): # message \ w _ c _
                    idx1 = find_nth( line, ' ', 1 )
                    idx2 = find_nth( line, ' ', 2 )
                    if idx1 < 0 or idx2 < 0 or idx2+1 >= len( line ):
                        self._append( { 'type' : 'error', 'verbose' : 'Neplatny syntax prikazu. Pouzijte "\\w username message"' } )
                    else:
                        to = line[idx1+1:idx2]
                        message = line[idx2+1:]
                        self._append( { 'type' : 'message', 'from' : username, 'to' : to, 'message' : message } )
                elif line.startswith( '\\r' ): # reconnect
                    idx1 = find_nth( line, ' ', 1 )
                    idx2 = find_nth( line, ' ', 2 )
                    if idx1 < 0 or idx2 < 0 or idx2+1 >= len( line ):
                        self._append( { 'type' : 'error', 'verbose' : 'Neplatny syntax prikazu. Pouzijte "\\r ipv4 port"' } )
                    else:
                        ipv4 = line[idx1+1:idx2]
                        port = line[idx2+1:]
                        if not valid_ipv4( ipv4 ) or not valid_port( port ):
                            self._append( { 'type' : 'error', 'verbose' : 'Neplatna ipv4 adresa nebo port."' } )
                        else:
                            self._append( { 'type' : 'reconnect', 'ipv4' : ipv4, 'port' : int( port ) } )
                elif line == '\\l': # peers
                    self._append( { 'type' : 'peers' } )
                elif line ==  '\\u': # getlist
                    self._append( { 'type' : 'getlist' } )
                elif line.startswith( '\\h' ): # help
                    self._append( { 'type' : 'print', 'verbose' : '[\\l] Vypise seznam znamych uzivatelu\n[\\u] Aktualizuje seznam uzivatelu\n[\\r ipv4 port] pripoji se na zadany uzel\n[\\w username message] odesle zpravu uzivateli' } )

    def _stdinNode( self ):
        while True:
            line = sys.stdin.readline().strip()
            if line.startswith( '\\' ):
                if line.startswith( '\\c' ): # connect
                    idx1 = find_nth( line, ' ', 1 )
                    idx2 = find_nth( line, ' ', 2 )
                    if idx1 < 0 or idx2 < 1 or idx2+1 >= len( line ):
                        self._append( { 'type' : 'error', 'verbose' : 'Neplatny syntax prikazu. Pouzijte "\\c ipv4 port"' } )
                    else:
                        ipv4 = line[idx1+1:idx2]
                        port = line[idx2+1:]
                        if not valid_ipv4( ipv4 ) or not valid_port( port ):
                            self._append( { 'type' : 'error', 'verbose' : 'Neplatna ipv4 adresa nebo port."' } )
                        else:
                            self._append( { 'type' : 'connect', 'ipv4' : ipv4, 'port' : int( port ) } )
                elif line == '\\s': # sync
                    self._append( { 'type' : 'sync' } )
                elif line.startswith( '\\l' ): # database
                    self._append( { 'type' : 'database' } )
                elif line.startswith( '\\n' ): # neighbors
                    self._append( { 'type' : 'neighbors' } )
                elif line.startswith( '\\h' ): # help
                    self._append( { 'type' : 'print', 'verbose' : '[\\c ipv4 port] Navaze spojeni se zadanym uzlem\n[\\s] Vynuti synchronizaci s ostatnimy uzly\n[\\l] Vypise aktualni databazi peeru a jejich uzlu\n[\\n] Vypise databazi znamych uzlu\n[\\d] Odpodi se od ostatnich uzlu' } )
                elif line.startswith( '\\d' ): # disconnect
                    self._append( { 'type' : 'disconnect' } )

    def __iter__( self ):
        with self._lock:
            while self._commands:
                yield self._commands.pop(0)

    def _append( self, cmd ):
        with self._lock:
            self._commands.append( cmd )
            with self._cond:
                self._cond.notify()

    def wait( self ):
        with self._cond:
            self._cond.wait()

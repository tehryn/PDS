"""
Author: Jiri Matejka -- xmatej52
Description: Keeps connecions between nodes and peers alive by sending hello and update messages
"""
from threading import Thread, Condition

class ConnectionKeeper( object ):
    def __init__( self ):
        self._hello  = False
        self._update = False
        self._cond = Condition()
        self._threads = list()

    # starts sending hello messages every 10 seconds to destIp and destPort
    def hello( self, sender, user, ip, port, destIp, destPort ):
        # loop for thread
        def _stillAlive():
            with self._cond:
                while self._hello:
                    sender.hello( user, ip, port, destIp, destPort )
                    self._cond.wait( 10 )
            sender.hello( user, ip, port, destIp, destPort, True )

        # starts the thread
        if not self._hello:
            self._hello = True
            th = Thread( target = _stillAlive, args=() )
            th.setDaemon( True )
            th.start()
            self._threads.append( th )

    # starts sending update messages every 4 seconds
    def update( self, receiver ):
        # loop for thread
        def _stillAlive():
            with self._cond:
                cmd = { 'type' : "sync" }
                while self._update:
                    receiver.procCommand( cmd )
                    self._cond.wait( 4 )
            receiver.procCommand( { 'type' : "disconnect" } )

        # starts the thread
        if not self._update:
            self._update = True
            th = Thread( target = _stillAlive, args=() )
            th.setDaemon( True )
            th.start()
            self._threads.append( th )

    # ends all threads
    def stop( self ):
        self._hello = False
        self._update = False
        with self._cond:
            self._cond.notifyAll()
        for th in self._threads:
            th.join()

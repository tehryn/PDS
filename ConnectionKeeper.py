from threading import Thread, Condition

class ConnectionKeeper( object ):
    def __init__( self, user, ip, port ):
        self._ip = ip
        self._port = port
        self._user = user
        self._running = False
        self._cond = None
        self._thread = None

    def start( self, sender, destIp, destPort ):
        def _stillAlive():
            with self._cond:
                while self._running:
                    sender.hello( self._user, self._ip, self._port, destIp, destPort )
                    self._cond.wait( 10 )
            sender.hello( self._user, self._ip, self._port, destIp, destPort, True )

        if not self._running:
            self._running = True
            self._cond = Condition()
            self._thread = Thread( target = _stillAlive, args=() )
            self._thread.setDaemon( True )
            self._thread.start()

    def stop( self ):
        if self._running:
            self._running = False
            with self._cond:
                self._cond.notify()
            self._thread.join()

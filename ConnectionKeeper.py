from threading import Thread, Condition

class ConnectionKeeper( object ):
    def __init__( self ):
        self._hello  = False
        self._update = False
        self._cond = Condition()
        self._threads = list()

    def hello( self, sender, user, ip, port, destIp, destPort ):
        def _stillAlive():
            with self._cond:
                while self._hello:
                    sender.hello( user, ip, port, destIp, destPort )
                    self._cond.wait( 10 )
            sender.hello( user, ip, port, destIp, destPort, True )

        if not self._hello:
            self._hello = True
            th = Thread( target = _stillAlive, args=() )
            th.setDaemon( True )
            th.start()
            self._threads.append( th )

    def update( self, receiver ):
        def _stillAlive():
            with self._cond:
                while self._update:
                    receiver.sendUpdate()
                    self._cond.wait( 4 )
            receiver.sendUpdate( True )

        if not self._update:
            self._update = True
            th = Thread( target = _stillAlive, args=() )
            th.setDaemon( True )
            th.start()
            self._threads.append( th )

    def stop( self ):
        self._hello = False
        self._update = False
        with self._cond:
            self._cond.notifyAll()
        for th in self._threads:
            th.join()

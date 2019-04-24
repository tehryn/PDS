"""
Author: Jiri Matejka -- xmatej52
Description: Locks file so only one process can access it.
"""
import os
from threading import Lock
from time import sleep

class FileLock( object ):
    def __init__( self, filename ):
        self._filename = filename
        self._locked   = False
        self._lock     = Lock()
        self._file     = None

    def __enter__( self ):
        # name of file representing lock
        lockName = self._filename + '.lock' if self._filename.startswith( '.' ) else '.' + self._filename + '.lock'
        cond = True
        # wait until I can access file
        while cond:
            try:
                # tries to create new file, throws exception if file exists
                self._file = os.open( lockName , os.O_CREAT | os.O_EXCL | os.O_RDWR )
                cond = False
            except:
                sleep( 0.01 )
        with self._lock:
            self._locked = True

    def __exit__( self, eType, eValue, eTrace ):
        self.__deleteFile()

    def __deleteFile( self ):
        # removes lock from file
        lockName = self._filename + '.lock' if self._filename.startswith( '.' ) else '.' + self._filename + '.lock'
        with self._lock:
            if self._locked:
                os.close( self._file )
                os.unlink( lockName )

    def __delete__( self, instance ):
        self.__deleteFile()

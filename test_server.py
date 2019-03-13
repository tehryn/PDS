#!/usr/bin/env python3
import socket
from time import sleep
from Receiver import Receiver
from Sender import Sender
from threading import Lock
sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
lock = Lock()
s = Sender( sock, lock )
receiver = Receiver( False, s )
receiver.start( sock, '0.0.0.0', 8888 )

while True:
    sleep( 3600 )
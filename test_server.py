#!/usr/bin/env python3
import socket
from time import sleep
from Receiver import Receiver
sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
receiver = Receiver( True )
receiver.start( sock, '0.0.0.0', 8888 )

while True:
    sleep( 3600 )
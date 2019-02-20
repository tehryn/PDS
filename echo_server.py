#!/usr/bin/env python3
import socket
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM )
sock.bind( ("0.0.0.0", 8888) )
while True:
    data, addr = sock.recvfrom( 4096 )
    data = data.decode( 'utf-8' )
    try:
        obj = json.loads( data )
        print( obj )
    except:
        print( "'" + data + "'" )
    msg = 'Received data of size: ' + str( len( data ) )
    sock.sendto( msg.encode( 'utf-8' ), ( addr[0], 8887 ) )

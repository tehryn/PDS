#!/usr/bin/env python3
"""
Author: Jiri Matejka -- xmatej52
Description: Implementation of node
"""
import sys
import socket
import signal
from threading import Lock
from Functions import get_setting, print_help
from ConnectionKeeper import ConnectionKeeper
from Sender import Sender
from Receiver import Receiver
from InputReader import InputReader

invalid_arguments = 1

author = "Author:\n" + \
         "  Jmeno: Jiri Matejka\n" + \
         "  login: xmatej52\n" + \
         "  Email: xmatej52@stud.fit.vutbr.cz" + \
         "  FIT VUT v Brne"

possible_arguments = [
    {
        'names'        : [ '--id' ],
        'optional'     : False,
        'has_tail'     : 1,
        'word_index'   : 'id',
        'prerequisite' : None,
        'description'  : 'Unikatni identifikator instance peera pro pripady, ' +
                         'kdy je potreba rozlisit mezi nimi v ramci jednoho hosta ' +
                         '(operacniho systemu), na kterem bezi.'
    },
    {
        'names'        : [ '--reg-ipv4' ],
        'optional'     : False,
        'has_tail'     : 1,
        'word_index'   : 'reg-ip',
        'prerequisite' : None,
        'description'  : 'IP adresa registracniho uzlu, na kterz peer bude peer pravidelne zasilat HELLO ' +
                         'zpravy a odesilat dotazy GETLIST k zjisteni aktualniho mapovani.'
    },
    {
        'names'        : [ '--reg-port' ],
        'optional'     : False,
        'has_tail'     : 1,
        'word_index'   : 'reg-port',
        'prerequisite' : None,
        'description'  : 'Port registracniho uzlu, na kterz peer bude peer pravidelne zasilat HELLO zpravy ' +
                         'a odesilat dotazy GETLIST k zjisteni aktualniho mapovani.'
    },
    {
        'names'        : [ '--help', '-h' ],
        'optional'     : True,
        'has_tail'     : 0,
        'word_index'   : 'help',
        'prerequisite' : None,
        'description'  : 'Vypise napovedu k programu.'
    },
]

# zpracovani argumentu
settings = dict()
try:
    settings = get_setting( possible_arguments, sys.argv[1:] )
except Exception as e:
    if ( len( sys.argv ) > 1 and ( sys.argv[1] == '-h' or sys.argv[1] == '--help' ) ):
        print_help( possible_arguments, sys.argv[0], sys.stdout, author )
        exit(0)
    else:
        sys.stderr.write( str( e ) + '\n' )
        exit( invalid_arguments )

regIp   = settings[ 'reg-ip' ][0]
try:
    regPort = int( settings[ 'reg-port' ][0] )
except:
    sys.stderr.write( 'Invalid port\n' )
    exit( invalid_arguments )

# Prijem a odesilani zprav
sock     = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
lock     = Lock()
sender   = Sender( sock, lock )
receiver = Receiver( regIp, regPort, True, sender )
if ( not receiver.start( sock ) ):
    sys.stderr.write( 'Unable to start node at adress ' + regIp + ' and port ' + str(regPort) + '\n' )
    exit( invalid_arguments )

# Pravidelne odesilani update
keeper = ConnectionKeeper()
keeper.update( receiver )

# Zpracovani prikazu od uzivatele a rpc
filename = '.' + settings[ 'id' ][0] + '.nodecommands'
reader   = InputReader( filename )

def thisIsTheEnd( _, __ ):
    keeper.stop()
    reader.stop()
    exit( 0 )

signal.signal( signal.SIGINT, thisIsTheEnd)
signal.signal( signal.SIGTERM, thisIsTheEnd)

while True:
    # cekam na prikazy
    reader.wait()
    # zpracovavam vsechny nove prikazy
    for cmd in reader:
        if cmd[ 'type' ] == 'error' and 'verbose' in cmd:
            sys.stderr.write( cmd[ 'verbose' ] + '\n' )
        elif cmd[ 'type' ] == 'print' and 'verbose' in cmd:
            sys.stdout.write( cmd[ 'verbose' ] + '\n' )
        elif cmd[ 'type' ] == 'exit':
            keeper.stop()
            exit( 0 )
        else:
            valid, message = receiver.procCommand( cmd, ( regIp, regPort ) )
            if valid:
                if isinstance( message, str ):
                    sys.stdout.write( message + '\n' )

            elif message:
                sys.stderr.write( 'Error: ' + message + '\n' )
            else:
                sys.stderr.write( 'Error: Invalid syntax of command.\n' )

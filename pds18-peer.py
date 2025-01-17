#!/usr/bin/env python3
"""
Author: Jiri Matejka -- xmatej52
Description: Implementace peeru
"""

import sys
import socket
import signal
from threading import Lock
from Functions import get_setting, print_help
from Sender import Sender
from ConnectionKeeper import ConnectionKeeper
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
        'names'        : [ '--username' ],
        'optional'     : False,
        'has_tail'     : 1,
        'word_index'   : 'username',
        'prerequisite' : None,
        'description'  : 'Unikatni uzivatelske jmeno identifikujici tohoto peera v ramci chatu.'
    },
    {
        'names'        : [ '--chat-ipv4' ],
        'optional'     : False,
        'has_tail'     : 1,
        'word_index'   : 'chat-ip',
        'prerequisite' : None,
        'description'  : 'IP adresa, na kterem peer nasloucha a prijima MESSAGE zpravy od ostatnich peeru.'
    },
    {
        'names'        : [ '--chat-port' ],
        'optional'     : False,
        'has_tail'     : 1,
        'word_index'   : 'chat-port',
        'prerequisite' : None,
        'description'  : 'Port, na kterem peer nasloucha a prijima MESSAGE zpravy od ostatnich peeru.'
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
    {
        'names'        : [ '--test', '-t' ],
        'optional'     : True,
        'has_tail'     : 0,
        'word_index'   : 'test',
        'prerequisite' : None,
        'description'  : 'Peer bude odesilat v cyklu nahodne dotazy na uzel'
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

regIp    = settings[ 'reg-ip' ][0]
chatIp   = settings[ 'chat-ip' ][0]
try:
    regPort = int( settings[ 'reg-port' ][0] )
except:
    sys.stderr.write( 'Invalid value of reg-port\n' )
    exit( invalid_arguments )
try:
    chatPort = int( settings[ 'chat-port' ][0] )
except:
    sys.stderr.write( 'Invalid value of chat-port\n' )
    exit( invalid_arguments )

# prijem zprav a odesilani odpovedi
sock     = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
sendLock = Lock()
inLonck  = Lock()
sender = Sender( sock, sendLock )
receiver = Receiver( chatIp, chatPort, False, sender, settings[ 'username' ][0] )
if ( not receiver.start( sock ) ):
    sys.stderr.write( 'Unable to start peer at adress ' + chatIp + ' and port ' + str(chatPort) + '\n' )
    exit( invalid_arguments )

# udrzeni spojeni s uzlem
keeper = ConnectionKeeper()
keeper.hello( sender, settings['username'][0], chatIp, chatPort , regIp, regPort )

# nacitani prikazu od rpc a uzivatele
filename = '.' + settings[ 'id' ][0] + '.peercommands'
reader = InputReader( filename, settings['username'][0] )

def thisIsTheEnd( _, __ ):
    keeper.stop()
    reader.stop()
    exit( 0 )

signal.signal( signal.SIGINT, thisIsTheEnd)
signal.signal( signal.SIGTERM, thisIsTheEnd)

while True:
    # ceka na prikazy
    reader.wait()
    # zpracovava jednotlive prikazy
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
                elif isinstance( message, dict ) and message[ 'type' ] == 'reconnect':
                    regIp = message[ 'ipv4' ]
                    regPort = int( message[ 'port' ] )
                    keeper.stop()
                    keeper.hello( sender, settings['username'][0], chatIp, chatPort , regIp, regPort )
            elif message:
                sys.stderr.write( 'Error: ' + message + '\n' )
            else:
                sys.stderr.write( 'Error: Invalid syntax of command.\n' )

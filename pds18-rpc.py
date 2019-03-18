#!/usr/bin/env python3
import socket
import sys
from time import sleep
from Receiver import Receiver
from Sender import Sender
from threading import Lock
from random import randint
from Functions import get_setting, print_help, get_exception_info
invalid_arguments = 1

author = "Author:\n" + \
         "  Jmeno: Jiri Matejka\n" + \
         "  login: xmatej52\n" + \
         "  Email: xmatej52@stud.fit.vutbr.cz" + \
         "  FIT VUT v Brne"

possible_arguments = [
    {
        'names'        : [ '--peer' ],
        'optional'     : True,
        'has_tail'     : 0,
        'word_index'   : 'peer',
        'prerequisite' : None,
        'description'  : 'Prikaz je urcen pro peer.'
    },
    {
        'names'        : [ '--node' ],
        'optional'     : True,
        'has_tail'     : 0,
        'word_index'   : 'node',
        'prerequisite' : None,
        'description'  : 'Prikaz je urcen pro node.'
    },
    {
        'names'        : [ '--command' ],
        'optional'     : False,
        'has_tail'     : 1,
        'word_index'   : 'cmd',
        'prerequisite' : None,
        'description'  : 'Identifikator prikazu.'
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
        'names'        : [ '--from' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'from',
        'prerequisite' : 'to',
        'description'  : 'Parametr prikazu message. Urcuje odesilatele zpravy.'
    },
    {
        'names'        : [ '--to' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'to',
        'prerequisite' : 'message',
        'description'  : 'Parametr prikazu message. Urcuje prijemce zpravy.'
    },
    {
        'names'        : [ '--message' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'message',
        'prerequisite' : 'from',
        'description'  : 'Parametr prikazu message. Urcuje telo zpravy.'
    },
    {
        'names'        : [ '--reg-ipv4' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'ip',
        'prerequisite' : 'port',
        'description'  : 'Parametr prikazu reconnect a connect. Urcuje ipv4 adresu serveru.'
    },
    {
        'names'        : [ '--port' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'port',
        'prerequisite' : 'ip',
        'description'  : 'Parametr prikazu reconnect a connect. Urcuje port serveru.'
    },
]

settings = dict()
try:
    settings = get_setting( possible_arguments, sys.argv[1:] )
except Exception as e:
    print( get_exception_info(e) )
    if ( len( sys.argv ) > 1 and ( sys.argv[1] == '-h' or sys.argv[1] == '--help' ) ):
        print_help( possible_arguments, sys.argv[0], sys.stdout, author )
        exit(0)
    else:
        sys.stderr.write( str( e ) + '\n' )
        exit( invalid_arguments )

if 'node' in settings and 'peer' in settings:
    sys.stderr.write( 'Nelze spustit program se zadanymi parametry --node a --peer, zadejte pouze jeden z nich.\n' )
    exit( invalid_arguments )
elif 'node' not in settings and 'peer' not in settings:
    sys.stderr.write( 'Nelze spustit program bez zadanych parametru --node nebo --peer.\n' )
    exit( invalid_arguments )

if settings[ 'cmd' ][0] == 'message':
    if 'to' not in settings:
        sys.stderr.write( 'Prikaz message vyzaduje parametry --from, --to a --message\n' )
        exit( invalid_arguments )
elif settings[ 'cmd' ][0] == 'connect':
    if 'ip' not in settings:
        sys.stderr.write( 'Prikaz connect vyzaduje parametry --ipv4 --port\n' )
        exit( invalid_arguments )
elif settings[ 'cmd' ][0] == 'reconnect':
    if 'ip' not in settings:
        sys.stderr.write( 'Prikaz reconnect vyzaduje parametry --ipv4 --port\n' )
        exit( invalid_arguments )

sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
lock = Lock()
s = Sender( sock, lock )
receiver = Receiver( True, s )
receiver.start( sock, '0.0.0.0', 8887 )
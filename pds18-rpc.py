#!/usr/bin/env python3
"""
Author: Jiri Matejka -- xmatej52
Description: Implementace RPC
"""
import sys
from json import dumps
from FileLock import FileLock
from Functions import get_setting, print_help, get_exception_info, valid_ipv4, valid_port
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
        'description'  : 'ID uzlu nebo peeru.'
    },
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
        'names'        : [ '--ipv4' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'ipv4',
        'prerequisite' : 'port',
        'description'  : 'Parametr prikazu reconnect a connect. Urcuje ipv4 adresu serveru.'
    },
    {
        'names'        : [ '--port' ],
        'optional'     : True,
        'has_tail'     : 1,
        'word_index'   : 'port',
        'prerequisite' : 'ipv4',
        'description'  : 'Parametr prikazu reconnect a connect. Urcuje port serveru.'
    },
]
# zpracovani argumentu
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

# kontrola ze nezadal --peer a --node
if 'node' in settings and 'peer' in settings:
    sys.stderr.write( 'Nelze spustit program se zadanymi parametry --node a --peer, zadejte pouze jeden z nich.\n' )
    exit( invalid_arguments )

# zpracovani prikazu pro peer
if 'peer' in settings:
    filename = '.' + settings['id'][0] + '.peercommands'
    # zamek na soubor
    lock = FileLock( filename )
    if settings[ 'cmd' ][0] == 'message':
        if 'to' not in settings:
            sys.stderr.write( 'Prikaz message vyzaduje parametry --from, --to a --message\n' )
            exit( invalid_arguments )
        with lock:
            with open( filename, 'a' ) as file:
                file.write( '{ "type" : "message", "from": ' + dumps( settings['from'][0] ) + ', "to": ' + dumps( settings[ 'to' ][0] ) +  ', "message": ' + dumps( settings[ 'message' ][0] ) + ' }\n' )

    elif settings[ 'cmd' ][0] == 'reconnect':
        if 'ipv4' not in settings:
            sys.stderr.write( 'Prikaz reconnect vyzaduje parametry --ipv4 --port\n' )
            exit( invalid_arguments )
        elif not( valid_ipv4( settings['ipv4'][0] ) and valid_port( settings[ 'port' ][0] ) ):
            sys.stderr.write( 'Neplatna ip adresa nebo port.\n' )
            exit( invalid_arguments )
        with lock:
            with open( filename, 'a' ) as file:
                file.write( '{ "type" : "reconnect", "ipv4": "' + settings['ipv4'][0] + '", "port": ' + settings[ 'port' ][0] + ' }\n' )

    elif settings[ 'cmd' ][0] == 'getlist':
        with lock:
            with open( filename, 'a' ) as file:
                file.write( '{ "type" : "getlist" }\n' )

    elif settings[ 'cmd' ][0] == 'peers':
        with lock:
            with open( filename, 'a' ) as file:
                file.write( '{ "type" : "getlist" }\n' )
                file.write( '{ "type" : "peers" }\n' )
    else:
        sys.stderr.write( 'Prikaz ' + settings['cmd'][0] + ' neni na peeru podporovan.\n' )
        exit( invalid_arguments )

# zpracovani prikazu pro uzel
elif 'node' in settings:
    filename = '.' + settings['id'][0] + '.nodecommands'
    lock = FileLock( filename ) # zamek
    if settings[ 'cmd' ][0] == 'connect':
        if 'ipv4' not in settings:
            sys.stderr.write( 'Prikaz connect vyzaduje parametry --ipv4 a --port\n' )
            exit( invalid_arguments )
        elif not( valid_ipv4( settings['ipv4'][0] ) and valid_port( settings[ 'port' ][0] ) ):
            sys.stderr.write( 'Neplatna ip adresa nebo port.\n' )
            exit( invalid_arguments )
        with lock:
            with open( filename, 'a' ) as file:
                file.write( '{ "type" : "connect", "ipv4": "' + settings['ipv4'][0] + '", "port": ' + settings[ 'port' ][0] + ' }\n' )
    elif settings[ 'cmd' ][0] == 'disconnect':
        with lock:
            with open( filename, 'a' ) as file:
                file.write( '{ "type" : "disconnect" }\n' )
    elif settings[ 'cmd' ][0] == 'sync':
        with lock:
            with open( filename, 'a' ) as file:
                file.write( '{ "type" : "sync" }\n' )
    elif settings[ 'cmd' ][0] == 'sync':
        with lock:
            with open( filename, 'a' ) as file:
                file.write( '{ "type" : "sync" }\n' )
    elif settings[ 'cmd' ][0] == 'database':
        with lock:
            with open( filename, 'a' ) as file:
                file.write( '{ "type" : "database" }\n' )
    elif settings[ 'cmd' ][0] == 'neighbors':
        with lock:
            with open( filename, 'a' ) as file:
                file.write( '{ "type" : "neighbors" }\n' )
    else:
        sys.stderr.write( 'Prikaz ' + settings['cmd'][0] + ' neni na uzlu podporovan.\n' )
        exit( invalid_arguments )
else:
    sys.stderr.write( 'Nelze spustit program bez zadanych parametru --node nebo --peer.\n' )
    exit( invalid_arguments )

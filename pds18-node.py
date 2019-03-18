#!/usr/bin/env python3
"""
Tento skript slouzi ke kolekci odkazu.
Autor: Jiri Matejka
Verze: 2.002 (2018-04-10)
"""

import sys
import socket
from threading import Lock
from Functions import get_setting, print_help
from ConnectionKeeper import ConnectionKeeper
from time import sleep
from Sender import Sender
from Receiver import Receiver
from Protokol import Db
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

sock    = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
regIp   = settings[ 'reg-ip' ][0]
regPort = int( settings[ 'reg-port' ][0] )

lock = Lock()
sender = Sender( sock, lock )
receiver = Receiver( regIp, regPort, True, sender )
receiver.start( sock )
keeper = ConnectionKeeper()
keeper.update( receiver )

dbs = [ db[ 'node' ] for db in receiver._db ]
newDb = Db( regIp, regPort )
newDb.update( [ x['peer'] for x in receiver._peers if x[ 'dbId' ] is None ] )
dbs.append( newDb )
sender.update( dbs ,'147.229.206.30', 7777 if regPort == 8888 else 8888 )
sleep(3600)

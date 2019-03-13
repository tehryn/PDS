#!/usr/bin/env python3
import sys
import socket
from threading import Lock
from random import randint
from time import sleep
from Functions import get_setting, print_help
from Sender import Sender
from ConnectionKeeper import ConnectionKeeper
from Receiver import Receiver
from Protokol import Protokol
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
        'has_tail'     : 1,
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

sock        = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
sock_sender = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )

regIp    = settings[ 'reg-ip' ][0]
regPort  = int( settings[ 'reg-port' ][0] )
chatIp   = settings[ 'chat-ip' ][0]
chatPort = int( settings[ 'chat-port' ][0] )

lock = Lock()
sender = Sender( sock, lock )
receiver = Receiver( False, sender )
receiver.start( sock, chatIp, chatPort )

keeper = ConnectionKeeper( settings['username'][0], chatIp, chatPort )
keeper.start( sender, regIp, regPort )

i=0
while True:
    #r = randint(0,4)
    r = 1
    sender.hello( str(i), '198.5.4.5', i, regIp, regPort  )
    i+=1
    if r == 0:
        sender.error( 'Error message', regIp, regPort )
    elif r == 1:
        sender.getlist( regIp, regPort )
        sender.ackExpected( Protokol.getId(), 'getlist', regIp, regPort )
    elif r == 2:
        sender.list( receiver._db, regIp, regPort )
        sender.ackExpected( Protokol.getId(), 'list', regIp, regPort )
    elif r == 3:
        sender.message( 'You shall not pass!!!', 'Gandalf', 'Balrog', regIp, regPort )
        sender.ackExpected( Protokol.getId(), 'message', regIp, regPort )
    elif r == 4:
        sender.disconnect( regIp, regPort )
    elif r == 5:
        maxx = randint( 10, 40 )
        idx = 0
        while idx < maxx:
            sender.ack( idx, regIp, regPort )
            sleep( 0.1 )
            idx += 1
    s = randint( 3,6 )
    sleep( s )

keeper.stop()

#!/usr/bin/env python3
"""
Tento skript slouzi ke kolekci odkazu.
Autor: Jiri Matejka
Verze: 2.002 (2018-04-10)
"""

import sys
import socket
from threading import Thread
from time import sleep
from Functions import get_setting, print_help
from Protokol import Hello, Ack, Disconnect, Error, GetList, List, Message, Protokol, Update
from Node import Db
from Peer import Peer
from ConnectionKeeper import ConnectionKeeper
from Receiver import Receiver

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

sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )

regIp    = settings[ 'reg-ip' ][0]
regPort  = int( settings[ 'reg-port' ][0] )
chatIp   = settings[ 'chat-ip' ][0]
chatPort = int( settings[ 'chat-port' ][0] )

hello_packet   = Hello( settings['username'][0], settings['chat-ip'][0], settings['chat-port'][0] )
getList_packet = GetList()
ack_packet     = Ack()
list_packet    = List()
message_packet = Message()
update_packet  = Update()
disconn_packet = Disconnect()
error_packet   = Error()
#sock.sendto( Protokol.encode( '===================' ), ( regIp, regPort ) )
#sock.sendto( Protokol.encode( str( hello_packet ) ), ( regIp, regPort ) )
#sock.sendto( Protokol.encode( str( getList_packet ) ), ( regIp, regPort ) )
#sock.sendto( Protokol.encode( str( ack_packet ) ), ( regIp, regPort ) )
#sock.sendto( Protokol.encode( list_packet.to_string( [ Peer('xlogin00', '0.0.0.0', '0'), Peer('xlogin01', '0.0.0.1', '1') ] ) ), ( regIp, regPort ) )
#sock.sendto( Protokol.encode( message_packet.to_string( 'xlogin00', 'xlogin01', 'Hello world' ) ), ( regIp, regPort ) )
#sock.sendto( Protokol.encode( update_packet.to_string( [ Db( '1.1.1.0', 'xlogin00', '0.0.0.0', '0' ), Db( '1.1.1.1', 'xlogin01', '0.0.0.1', '1' )  ] ) ), ( regIp, regPort ) )
#sock.sendto( Protokol.encode( error_packet.to_string( 'Testing' ) ), ( regIp, regPort ) )
#sock.sendto( Protokol.encode( str( disconn_packet ) ), ( regIp, regPort ) )
#sock.sendto( Protokol.encode( '===================' ), ( regIp, regPort ) )

receiver = Receiver( False )
receiver.start( chatIp, chatPort )

keeper = ConnectionKeeper( False )
keeper.start( regIp, regPort, hello_packet )


sleep(21)
keeper.stop()

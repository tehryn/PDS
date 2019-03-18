"""
Author: Jiri Matejka (xmatej52)

V tomto modulu jsou implementovany společné funkce.
"""
import sys
import traceback
import ipaddress

#Exception unsave
def get_setting ( possible_arguments, list_of_arguments ):
    """
    Funkce zpracuje argumenty programu. Parametr possible arguments je pole se slovniky, list_of_arguments
    je seznam argumentu.
    Klice jednotlivych slovniku:
        names        - seznam jmen, pomocí kterých lze argument zadat
        optional     - urcuje, zda je argument volitelny nebo ne
        has_tail     - urcuje zda ma argument 0, 1 nebo N parametru
        word_index   - index, pod kterym lze zadane hodny zpristupni v hashi vracenem funkci
        prerequisite - prerekvizity nebo podminky, za kterych je mozne tento argument zadat
        description  - popis zadaneho argumentu, ktery bude pouzit pro automaticke generovani napovedy
    """
    def find_tag( argument ):
        """
        Funkce nalezne zadany argument
        """
        found_tag = None
        for tag in possible_arguments:
            if ( argument in tag[ 'names' ] ):
                found_tag = tag
                break
        return found_tag

    current_tag      = None
    current_tag_name = None
    current_tag_int  = None
    tail             = list()
    settings         = { '__alone__' : True }
    defined_counter  = 0
    # zjistime si vsechny mozne argumenty
    possible_tags    = [ y for x in possible_arguments for y in x['names'] ]
    # A pak zpracujeme zadane argumenty
    for arg in list_of_arguments:
        defined_counter += 1
        # Pomlckou zacinaji argumenty
        if arg.startswith( '-' ):
            # Zjistime, zda je zadany argument podporovan
            if ( ( arg in possible_tags ) ):
                # Narazili jsme na dalsi argument, predchozi jeste nebyl ale zpracovan
                if ( isinstance( current_tag, dict ) ):
                    # zjistile pocet zadanych parametru k argumentu
                    tail_len = len( tail )
                    # A pokud je vse cajk, tak pokracujeme
                    if ( ( current_tag_int == tail_len  ) or ( current_tag_int == 2 and tail_len > 0 ) ):
                        # do navratobe hodnoty ulozime parametry, aby se mohli zpristupnit
                        # Pozor! Pylint zde hlasi chybu, ale Pylint se v tomto pripade zatracene zmylil.
                        settings[ current_tag[ 'word_index' ] ] = tail
                        # zpracujeme nove parametry zadane k novemu argumentu
                        current_tag      = find_tag( arg )
                        # pokud je argument zadan znovu, tak vyhodime vyjimku
                        if ( current_tag[ 'word_index' ] in settings ):
                            error_str  = ', '.join( current_tag[ 'names' ] )
                            if ( len( current_tag[ 'names' ] ) > 1 ):
                                raise Exception( 'Argumenty "' + error_str + '" znamenaji to same a jsou zadany vicekrat nez jednou.'  )
                            else:
                                raise Exception( 'Argument ' + error_str + ' je zadan vicekrat nez jednou.'  )

                        # pokud je to pouze argument bez parametru, nastavime jeho hodnotu na True
                        current_tag_int  = int( current_tag[ 'has_tail' ] )
                        if ( current_tag_int == 0 ):
                            settings[ current_tag[ 'word_index' ] ] = True

                        # aktualizujeme jmeno aktualne zpracovaneho argumentu
                        current_tag_name = arg
                        tail             = []

                    elif ( current_tag_int == 1):
                        # Zadal spatny pocet parametru
                        raise Exception( 'Argument "' + current_tag_name +'" vyzaduje prave jeden dalsi parametr, zadano ' + str( tail_len ) + '.'  )
                    else:
                        # Zadal spatny pocet parametru
                        raise Exception( 'Argument "' + current_tag_name +'" vyzaduje alespon jeden dalsi parametr.'  )
                else:
                    current_tag      = find_tag( arg )
                    current_tag_int  = int( current_tag[ 'has_tail' ] )
                    current_tag_name = arg
            else:
                # Argument neni podporovan
                raise Exception( 'Nepodporovany argument "' + arg +'".' )
        # zaradime parametr g argumentu
        elif ( isinstance( current_tag, dict ) ):
            if ( current_tag_int != 0 ):
                if ( arg not in tail ):
                    tail.append( arg )
                else:
                    raise Exception( 'Parametr "' + arg + '"  pro argument "' + current_tag_name + '" je zadan vicekrat.' )
            else:
                raise Exception( 'Argument "' + current_tag_name +'" neocekava zadny dalsi parametr, zadal/a jste "' + arg + '".' )
        else:
            raise Exception( 'Spatne vstupni argumenty, spuste s argumentem "--help" pro ziskani napovedy.' )

    # Musime zpracovat jeste posledni argument, stejne jako je zpracovan uvnitr cyklu
    if ( current_tag_int is not None ):
        if ( current_tag_int > 0 ):
            tail_len = len( tail )
            if ( ( current_tag_int == tail_len  ) or ( current_tag_int == 2 and tail_len > 0 ) ):
                settings[ current_tag[ 'word_index' ] ] = tail
            elif ( current_tag_int == 1):
                raise Exception( 'Argument "' + current_tag_name +'" vyzaduje prave jeden dalsi parametr, zadano ' + str( tail_len ) + '.'  )
            else:
                raise Exception( 'Argument "' + current_tag_name +'" vyzaduje alespon jeden dalsi parametr.'  )
        else:
            settings[ current_tag[ 'word_index' ] ] = True

    # Zkontrolujeme zadane povinne argumenty a zda jsou splneny prerekvizity
    error_list = list()
    for item in possible_arguments:
        # Kontrola, zda jsou zadane povinne argumenty
        if ( not item[ 'optional' ] ):
            if ( item[ 'word_index' ] not in settings ):
                error_list.append( item[ 'names' ][0] )

        # Kontrola prerekvizit
        if ( ( item[ 'prerequisite' ] is not None ) and ( item[ 'word_index' ] in settings ) ):
            # kontrola zvlastnich prerekvizit
            if ( item[ 'prerequisite' ] == '__alone__' and defined_counter > 1 ):
                raise Exception( 'Argument "' + item[ 'names' ][0] + '" musi byt zadan samostatne' )
            # kontrola, zda je zadan argument ktery vyzaduje aktualne zpracovany argument
            elif ( item[ 'prerequisite' ] not in settings ):
                error_list = [ y for x in possible_arguments for y in x[ 'names' ] if x[ 'word_index' ] == item[ 'prerequisite' ] ]
                error_str = ', '.join ( error_list )
                if ( len( error_list ) > 1 ):
                    raise Exception( 'Argument "' + item[ 'names' ][0] + '" lze spustit pouze s argumenty "' + error_str + '".' )
                else:
                    raise Exception( 'Argument "' + item[ 'names' ][0] + '" lze spustit pouze s argumentem "' + error_str + '".' )

    # Vypis vsech nalezenych chyb
    if error_list:
        error_str  = ', '.join( error_list )
        raise Exception( 'Argumenty: "' + error_str +'" jsou povinne. Spuste s argumentem "--help" pro ziskani napovedy.' )
    return settings

#Exception save on correct use
def get_exception_info( custom_info='' ):
    """Metoda vrati veskere informace o aktualnim miste v kodu. Vhodne pro vypis chyb."""
    type_, value_, traceback_ = sys.exc_info()
    error = traceback.format_exception( type_, value_, traceback_ )
    return str( custom_info ) + '\n' + ''.join( error )

#Exception save on correct use
def print_help( possible_arguments, file_name, output=sys.stdout, author='Vyzkumna skupina KNOT@FIT' ):
    """
    Funkce vygeneruje napovedu programu. Parametr possible_arguments je seznamem slovniku.
    Klice jednotlivych slovniku:
        names        - seznam jmen, pomocí kterých lze argument zadat
        optional     - urcuje, zda je argument volitelny nebo ne
        has_tail     - urcuje zda ma argument 0, 1 nebo N parametru
        word_index   - index, pod kterym lze zadane hodny zpristupni v hashi vracenem funkci
        prerequisite - prerekvizity nebo podminky, za kterych je mozne tento argument zadat
        description  - popis zadaneho argumentu, ktery bude pouzit pro automaticke generovani napovedy
    """
    optional       = [ arg for arg in possible_arguments if arg[ 'optional' ] ]
    optional_str   = [ '[' + ', '.join( arg[ 'names' ] ) + ']' for arg in optional ]
    obligatory     = [ arg for arg in possible_arguments if not arg[ 'optional' ] ]
    obligatory_str = [ '(' + ', '.join( arg[ 'names' ] ) + ')' for arg in obligatory ]
    help_str       = file_name + ' '
    help_str      += ' '.join( obligatory_str ) + ' '
    help_str      += ' '.join( optional_str ) + '\n'
    output.write( help_str )
    for arg in obligatory:
        help_str = ', '.join( arg[ 'names' ] )
        output.write( help_str + ' - ' + arg[ 'description' ] + '\n\n' )
    for arg in optional:
        help_str = ', '.join( arg[ 'names' ] )
        output.write( help_str + ' - ' + arg[ 'description' ] + '\n\n' )
    output.write( author + '\n' )

def find_nth( string, substr, n ):
    """Funkce najde N-ty prvek v retezci. Pokud je prvek nalezen, je vracen jeho index, jinak je vracena -1"""
    start = string.find( substr )
    while start >= 0 and n > 1:
        start = string.find( substr, start + len( substr ) )
        n -= 1
    return start

def valid_ipv4( ip ):
    try:
        ip = ipaddress.ip_address(ip)
        return ip.version == 4
    except:
        return False

def valid_port( port ):
    if isinstance( port, str ):
        return port.isdigit() and ( 1 <= int( port ) <= 65535 )
    return 1 <= port <= 65535

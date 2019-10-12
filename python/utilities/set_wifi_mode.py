from sys import exc_info

from python.logger import get_sub_logger 

logger = get_sub_logger(__name__)

interface_l1_res = r'(^[#]*[ ]*interface[ |\t]*)([a-zA-Z0-9]+)'
interface_l2_res = r'(^[#]*)([ |\t]*static[ |\t]+[\.0-9]+[.]*\n)'
interface_l3_res = r'(^[#]*)([ |\t]*nohook[ |\t]+wpa_supplicant[.]*\n)'

def set_wifi_mode(args):
    """ Decide whether to enter hotspot mode or wifi mode and then
        do so"""
    pass
    """+

    try:
        if args['mode'] == 'hotspot':
            logger.info('will enter hotspot mode')
            #TODO - Need to capture the line that contains interface [some lan id] and uncomment it.
            change_file_line(path.join('/etc', 'dhcpcd.conf'), 
                             interface_l1_res, 'interface {}\n'.format()
             


            return True if args['silent'] else 'Ok'
        if args['mode'] == 'wi-fi':
            logger.info('will enter wi-fi  mode')




            return True if args['silent'] else 'Ok'
        else:
            logger.error('Unknown wi-fi mode: {}'.format(args['mode']))
            return False if args['silent'] else 'ERROR'
            
    except:
        logger.error('Exception in set_wifi_mode: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return False if args['silent'] else 'ERROR'
    """
  

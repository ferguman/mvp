import re

from python.logger import get_sub_logger 

logger = get_sub_logger(__name__)

def change_file_line(fp, line_search_re_str, new_line):

    try:
        line_search_re = re.compile(line_search_re_str)

        changed = False

        logger.info('opening {}'.format(fp))
        with open(fp, mode='r+') as f:
            lines = f.readlines()
            f.seek(0)

            for line in lines:
                if line_search_re.search(line):
                    f.write(new_line)
                    changed = True
                else:
                    # Not the target line so write it back.
                    f.write(line)

            f.truncate()

        return changed
    except:
        logger.error('change_file_line error {}'.format(exc_info()[0], exc_info()[1]))
        return False

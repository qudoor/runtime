import logging
import os


def get_logger(name=''):
    if '/' in name:
        name = os.path.basename(name).replace('.py', '')
    return logging.getLogger('qupot.%s' % name)

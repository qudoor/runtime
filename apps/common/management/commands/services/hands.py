import os
import sys
import logging
from django.conf import settings


try:
    __version__ = '1.0.0'
except ImportError as e:
    print("Not found __version__: {}".format(e))
    print("Python is: ")
    logging.info(sys.executable)
    __version__ = 'Unknown'
    sys.exit(1)


HTTP_HOST = settings.HTTP_HOST or '127.0.0.1'
HTTP_PORT = settings.HTTP_PORT or 9001
WS_PORT = settings.WS_PORT or 9002
FLOWER_PORT = settings.FLOWER_PORT or 9003
DEBUG = settings.DEBUG or False
BASE_DIR = settings.BASE_DIR
LOG_DIR = os.path.join(BASE_DIR, 'logs')
APPS_DIR = os.path.join(BASE_DIR, 'apps')


import os
from .. import const
from ..const import CONFIG

BASE_DIR = const.BASE_DIR
LOG_DIR = const.LOG_DIR
QUPOT_LOG_FILE = os.path.join(LOG_DIR, 'qupot.log')
ANSIBLE_LOG_FILE = os.path.join(LOG_DIR, 'ansible.log')
CELERY_LOG_FILE = os.path.join(LOG_DIR, 'celery.log')
GUNICORN_LOG_FILE = os.path.join(LOG_DIR, 'gunicorn.log')
LOG_LEVEL = CONFIG.LOG_LEVEL


def skip_health_check(record):
    try:
        if '/health_check/' in record.getMessage():
            return False
    except:
        return True
    return True


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(astime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'main': {
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'format': '%(asctime)s [%(module)s %(levelname)s] %(message)s',
        },
        'exception': {
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'format': '\n%(asctime)s [%(levelname)s] %(message)s',
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'syslog': {
            'format': 'QuPot: %(message)s'
        },
        'msg': {
            'format': '%(message)s'
        }
    },
    'filters': {
        'skip_health_check': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_health_check,
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'main',
            'filters': ['skip_health_check'],
        },
        'file': {
            'encoding': 'utf8',
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024 * 1024 * 100,
            'backupCount': 7,
            'formatter': 'main',
            'filename': QUPOT_LOG_FILE,
            'filters': ['skip_health_check'],
        },
        'celery': {
            'encoding': 'utf8',
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'main',
            'maxBytes': 1024 * 1024 * 100,
            'backupCount': 7,
            'filename': CELERY_LOG_FILE,
        },
        'gunicorn': {
            'encoding': 'utf8',
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'main',
            'maxBytes': 1024 * 1024 * 100,
            'backupCount': 7,
            'filename': GUNICORN_LOG_FILE,
            'filters': ['skip_health_check'],
        },
    },
    # 日志对象
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'propagate': False,
            'level': LOG_LEVEL,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,

        },
        'django.server': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'qupot': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,

        },
        'celery': {
            'handlers': ['console', 'celery'],
            'level': LOG_LEVEL,
        },
        'gunicorn': {
            'handlers': ['console', 'gunicorn'],
            'level': LOG_LEVEL,
        }

    }
}

if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR)

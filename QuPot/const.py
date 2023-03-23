# -*- coding: utf-8 -*-
#
import os

from .conf import ConfigManager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
CONFIG = ConfigManager.load_user_config()

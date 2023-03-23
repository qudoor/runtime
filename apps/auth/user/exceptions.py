#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : chengshuang
@Contact : chengshuang@qudoor.cn
@File    : exceptions.py
@Software: PyCharm
@Time    : 2023/2/24 17:41
"""

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework import status


class BadRequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'bad_request'
    default_detail = _('Bad Request (400)')


class ServerError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = 'server_error'
    default_detail = _('Server error')

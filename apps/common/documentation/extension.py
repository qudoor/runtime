#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author  : chengshuang
# @Contact : chengshuang@qudoor.cn
# @File    : extension.py
# @Software: PyCharm
# @Time    : 2022/12/6 09:57


from drf_spectacular.extensions import OpenApiAuthenticationExtension


class JwtAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = 'apps.auth.user.JwtAuthentication'
    name = 'JwtAuthentication'
    match_subclasses = True
    priority = 10

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'in': 'header',
            'scheme': 'bearer',
            'name': 'Authorization',
            'description': 'Json web token authentication',
            'bearerFormat': 'Bearer'
        }

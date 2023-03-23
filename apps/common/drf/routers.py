#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : chengshuang
@Contact : chengshuang@qudoor.cn
@File    : r.py
@Software: PyCharm
@Time    : 2023/3/2 15:29
"""

import inspect

from django.urls import path, include
from rest_framework.routers import BaseRouter
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ViewSet


def append_trailing_slash(s: str) -> str:
    return s if not s == "" and s.endswith("/") else f"{s}/"


def escape_trailing_slash(s: str) -> str:
    return s[1:] if s.endswith("/") else s


class ViewSetRouter(DefaultRouter):

    @classmethod
    def match(cls, source) -> bool:
        return inspect.isclass(source) and issubclass(source, (GenericViewSet, ViewSet))


class ViewRouter(BaseRouter):
    # Todo: APIRootView ?

    def get_default_basename(self, view):
        pass

    def get_urls(self):
        ret = []
        for prefix, view_class, basename in self.registry:
            prefix = append_trailing_slash(prefix)
            ret.append(
                path(prefix, view_class.as_view(), name=basename)
            )
        return ret

    @classmethod
    def match(cls, source) -> bool:
        return inspect.isclass(source) and issubclass(source, APIView)


class ApiRouter(BaseRouter):

    def __init__(self, basename: str = None, trailing_slash=True):
        super().__init__()
        self.basename = basename
        self.trailing_slash = trailing_slash,
        self._routers = [
            ViewSetRouter(trailing_slash=trailing_slash),
            ViewRouter(),
        ]

    def register(self, prefix: str, source, basename: str = None):
        if basename is None:
            basename = self.get_default_basename(source)

        for router in self._routers:
            if router.match(source):
                return router.register(prefix, source, basename=basename)

        if isinstance(source, BaseRouter):
            prefix = append_trailing_slash(prefix)
            self.registry.append((prefix, source, basename))

        # invalidate the urls cache
        if hasattr(self, '_urls'):
            del self._urls

    def get_default_basename(self, source):
        return self.basename

    def get_urls(self):
        ret = []
        for prefix, source, basename in self.registry:
            ret.append(
                path(prefix, include(source.urls), name=basename)
            )

        for router in self._routers:
            ret += router.urls
        return ret


APIRouter = ApiRouter

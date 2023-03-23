#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author  : chengshuang
# @Contact : chengshuang@qudoor.cn
# @File    : utils.py
# @Software: PyCharm
# @Time    : 2023/2/8 16:15

from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view


class schema:

    def __init__(self, data: dict):
        self.data = data

    def __call__(self, view):
        kwargs = self.get_kwargs()
        return extend_schema_view(**kwargs)(view)

    def get_kwargs(self):
        kwargs = {}
        for method, method_data in self.data.items():
            kwargs[method] = extend_schema(**method_data)

        return kwargs


class ModelSchema(schema):
    summary_format = "%s%s - %s"
    default_mapping = {
        "list": "列表",
        "retrieve": "详情",
        "create": "创建",
        "update": "更新",
        "partial_update": "更新部分",
        "destroy": "删除",
    }

    def __init__(self, name, data=None, tags=None, prefix=None, actions: dict = None):
        # self.arg = arg
        self.name = name
        self.tags = tags
        self.prefix = prefix + '-' if prefix else ''
        self.actions_mapping = actions if actions else {}
        self.actions_mapping.update(self.default_mapping)
        if not data:
            data = {}
        data.update(self.model_data)
        self.set_tags(data)

        super().__init__(data)

    def set_tags(self, data):
        if self.tags:
            for k in data.keys():
                data[k]['tags'] = self.tags

    @property
    def model_data(self):
        return {
            k: {
                "summary": self.summary_format % (self.prefix, self.name, v),
            }
            for k, v in self.actions_mapping.items()
        }


def model_schema(arg, *args, **kwargs):
    # @model_schema
    if callable(arg):
        queryset = getattr(arg, "queryset")
        verbose_name = queryset.model._meta.verbose_name
        app_label = queryset.model._meta.app_label
        tags_mapping = getattr(settings, "DOCUMENTATION_TAGS_MAPPING", {})
        tag = tags_mapping.get(app_label, None)
        if tag:
            tag = [f"{tag}/{verbose_name}"]
        return ModelSchema(verbose_name, tags=tag)(arg)

    # @model_schema()
    return ModelSchema(arg, *args, **kwargs)

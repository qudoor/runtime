#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author  : chengshuang
# @Contact : chengshuang@qudoor.cn
# @File    : schema.py
# @Software: PyCharm
# @Time    : 2022/11/30 15:21
import typing
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework.generics import GenericAPIView
from drf_spectacular.openapi import AutoSchema as DefaultAutoSchema


class AutoSchema(DefaultAutoSchema):
    action_mapping = {
        'list': _('list'),
        'retrieve': _('retrieve'),
        'create': _('create'),
        'update': _('update'),
        'partial_update': _('partial update'),
        'destroy': _('destroy'),
    }

    def _get_serializer_field_meta(self, field, direction):
        """
        重写：
        * 如help_text不存在，以verbose_name作为description
        * models.Field  help_text    ->  help_text
        *               verbose_name ->  label
        """
        meta = super()._get_serializer_field_meta(field, direction)
        if 'description' not in meta and not field.help_text and field.label:
            meta['description'] = str(field.label)

        return meta

    def get_tags(self) -> typing.List[str]:
        """
        重写
        """
        mapping = getattr(settings, "DOCUMENTATION_TAGS_MAPPING", None)
        if mapping and isinstance(mapping, dict):
            tags = []
            for tag in super().get_tags():
                tags.append(mapping.get(tag, tag))
            return tags

        return super().get_tags()

    def get_action(self):
        if self.method == 'GET' and self._is_list_view():
            action = 'list'
        else:
            action = self.method_mapping[self.method.lower()]

        return action

    def get_summary(self):
        if bool(isinstance(self.view, GenericAPIView) and
                hasattr(self.view, "queryset") and
                self.view.queryset):
            action = self.get_action()
            action_name = self.action_mapping[action]
            model_name = self.view.queryset.model._meta.verbose_name
            return f'{model_name}-{action_name}'

        return super().get_summary()

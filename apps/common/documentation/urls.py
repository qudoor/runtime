#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author  : chengshuang
# @Contact : chengshuang@qudoor.cn
# @File    : urls.py
# @Software: PyCharm
# @Time    : 2022/12/6 10:02

from django.urls import path
from drf_spectacular.views import SpectacularAPIView as SchemaView
from drf_spectacular.views import SpectacularJSONAPIView as SchemaJsonView
from drf_spectacular.views import SpectacularYAMLAPIView as SchemaYamlView
from drf_spectacular.views import SpectacularSwaggerView as SwaggerView
from .views import ElementsView

urlpatterns = [
    path('schema/', SchemaView.as_view(), name='schema'),
    path('schema.json/', SchemaJsonView.as_view(), name='schema-json'),
    path('schema.yaml/', SchemaYamlView.as_view(), name='schema-yaml'),
    path('swagger/', SwaggerView.as_view(), name='swagger'),
    path('elements/', ElementsView.as_view(), name='docs'),
    path('', SwaggerView.as_view(), name='swagger'),
]

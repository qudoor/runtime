#!/usr/bin/env python

import json
import time
import logging
from django.urls import resolve
from django.utils import timezone

from .worker import logger_worker

logger = logging.getLogger(__name__)


class ApiTrackingMiddleware:
    allowed_methods = ['POST', 'PUT', 'PATCH', 'DELETE', ]
    allowed_status = "__all__"
    allowed_response_content_types = ['application/json', 'application/vnd.api+json', 'application/gzip']

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        resolver = resolve(request.path_info)
        url_name = resolver.url_name
        namespace = resolver.namespace

        if not url_name:
            paths = request.path.split("/")
            if paths[-1] == "":
                url_name = paths[-2]
            else:
                url_name = paths[-1]

        action_name = url_name.title()
        logger.info(f"Action: {action_name}")

        # Always skip Admin panel
        if namespace == 'admin':
            return self.get_response(request)

        start_time = time.time()

        try:
            request_data = json.loads(request.body) if request.body else ''
        except:
            request_data = ''

        # Code to be executed for each request before
        # the view (and later middleware) are called.
        response = self.get_response(request)

        # 只记录允许的状态码
        if self.allowed_status != "__all__":
            return response

        # 只记录允许的请求方法
        if request.method not in self.allowed_methods:
            return response

        content_type = response.get('content-type', None)
        if content_type in self.allowed_response_content_types:

            if content_type == 'application/gzip':
                response_body = '** GZIP Archive **'
            elif getattr(response, 'streaming', False):
                response_body = '** Streaming **'
            else:
                if type(response.content) == bytes:
                    response_body = json.loads(response.content.decode())
                else:
                    response_body = json.loads(response.content)

            api = request.build_absolute_uri()

            data = dict(
                api=api,
                headers=self.get_headers(request=request),
                body=request_data,
                method=request.method,
                client_ip_address=self.get_client_ip(request),
                response=response_body,
                status_code=response.status_code,
                execution_time=self.get_execution_time(time.time() - start_time),
                user_id=request.user.id if (request.user and request.user.is_authenticated) else None,
                added_on=timezone.now(),
                action=action_name
            )

            if logger_worker:
                logger_worker.push(data)

        return response

    @staticmethod
    def get_execution_time(t):
        return str(int(t * 1000)) + 'ms'

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', None)
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]

        return request.META.get('REMOTE_ADDR', None)

    @staticmethod
    def get_headers(request=None):
        h = {}
        for header, value in request.META.items():
            if header.startswith('HTTP_'):
                h[header[5:].replace('_', '-')] = value
        return h

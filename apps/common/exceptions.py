import logging

from django.db import DatabaseError
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger('django')


def custom_exception_handler(exc, context):
    """
    自定义异常处理
    :param exc: 异常类
    :param context: 抛出异常的上下文
    :return: Response响应对象
    """
    # 调用drf框架原生的异常处理方法
    response = exception_handler(exc, context)

    if response is None:
        view = context['view']
        if isinstance(exc, DatabaseError):
            # 数据库异常
            logger.error('[%s] %s' % (view, exc))
            response = Response({'message': '服务器内部错误'}, status=status.HTTP_507_INSUFFICIENT_STORAGE)

    return response


def proxy_exception_handler(response_from_proxy):
    res = response_from_proxy.args[0]
    response = Response({'message': '代理服务器出错'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if res.status_code == 401:
        print("code: ", res)
        response = Response({'message': res.text}, status=status.HTTP_401_UNAUTHORIZED)

    return response


def is_exception_status_code(status_code):
    return str(status_code).startswith('4') or str(status_code).startswith('5')


class ConfigNotFoundException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "找不到配置文件，请检查集群是否存在"
    default_code = 'error'


class K8SException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "k8s 错误"
    default_code = 'error'


class NexusException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "未接入Nexus仓库"
    default_code = 'error'


class MyBaseException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Base Exception"
    default_code = 'error'

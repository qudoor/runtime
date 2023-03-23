from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from django.conf import settings

# 为celery程序设置默认的Django设置模块。
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'QuPot.settings')

# 注册Celery的APP
app = Celery('QuPot')


class Config:
    timezone = "Asia/Shanghai"
    enable_utc = False
    # 保存任务执行返回结果保存到Redis
    result_backend = 'redis://{0}:{1}/2'.format(settings.REDIS_SETTING['host'], settings.REDIS_SETTING['port'])
    # celery 配置 redis
    broker_url = 'redis://{0}:{1}/7'.format(settings.REDIS_SETTING['host'], settings.REDIS_SETTING['port'])

    # CELERY_BEAT_REDIS_SCHEDULER_KEY = 'qupot:celery:beat:tasks'
    accept_content = ['json']
    # or the actual content-type (MIME)
    accept_content = ['application/json']
    # using serializer name
    result_accept_content = ['json']
    # or the actual content-type (MIME)
    result_accept_content = ['application/json']
    # 任务超时
    task_time_limit = 3000
    # redis 连接超时时间
    redis_socket_timeout = 60
    # 禁用默认日志
    worker_hijack_root_logger = False


# 绑定配置文件
# app.config_from_object('django.conf.settings', namespace='CELERY')
app.config_from_object(Config)
# 自动发现各个app下的tasks.py文件
app.autodiscover_tasks()

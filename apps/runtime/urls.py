from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.common.utils.webssh.channel import websocket, tasklog_ws
from .views.app import RuntimeAppModelViewSet
from .views.celery_task import CeleryTaskViewSet
from .views.credentials import CredentialsViewSet
from .views.hosts import HostsModelViewSet
from .views.ko import KoModelViewSet
from .views.registry import TaskRegistryModelViewSet
from .views.task import TaskModelViewSet
from .websocket_layer import Playbook

router = DefaultRouter()
router.register(r'credentials', CredentialsViewSet)
router.register(r'hosts', HostsModelViewSet)
router.register(r'task', TaskModelViewSet)
router.register(r'registry', TaskRegistryModelViewSet)
router.register(r'ko', KoModelViewSet)
router.register(r'app', RuntimeAppModelViewSet)
# 原 router.register(r'quantumappenv', QuantumAppEnvViewSet, 'quantumappenv')
router.register(r'celery', CeleryTaskViewSet, 'celery')

urlpatterns = [path('', include(router.urls)), ] + router.urls

websocket_url = [
    path("ws/playbook/", Playbook.as_asgi()),
    path("ws/webssh/", websocket.WebSSH.as_asgi()),
    path("ws/readlog/", tasklog_ws.TaskLogWebsocket.as_asgi()),
]

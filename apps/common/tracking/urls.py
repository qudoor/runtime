#!/usr/bin/env python

from apps.common.drf.routers import ApiRouter
from .views import ApiRecordViewSet

router = ApiRouter()
router.register(r'record', ApiRecordViewSet, basename='api-record')

urlpatterns = router.urls

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    @author  : chengshuang
    @contact : chengshuang@qudoor.cn
    @File    : urls.py
    @Software: PyCharm
    @Time    : 2023/2/23 09:14
"""

from apps.common.drf.routers import ApiRouter

from .user import views as user_views

router = ApiRouter()
router.register("login", user_views.LoginView)
router.register("info", user_views.UserInfoView)
router.register("change-password", user_views.PasswordChangeView)
router.register("user", user_views.UserModelViewSet)

urlpatterns = router.urls

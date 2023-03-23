"""QuPot URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include, re_path
from django.contrib.staticfiles.views import serve


def return_static(request, path, insecure=True, **kwargs):
    return serve(request, path, insecure, **kwargs)


app_view_patterns = [
    path('ops/', include("apps.ops.urls")),
    path('runtime/', include("apps.runtime.urls")),
    path('appstore/', include("apps.appstore.urls")),
    path('auth/', include("apps.auth.urls")),
    path('docs/', include("apps.common.documentation.urls")),
    path('tracking/', include("apps.common.tracking.urls")),
]

urlpatterns = [
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include(app_view_patterns)),
    path('health_check/', include('health_check.urls')),
    re_path(r'^static/(?P<path>.*)$', return_static, name='static'),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AppStoreViewSet


router = DefaultRouter()
router.register(r'', AppStoreViewSet,basename='appstore')


urlpatterns = [
    path('', include(router.urls)),
]+router.urls
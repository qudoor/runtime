from django.urls import path, include
from rest_framework.routers import DefaultRouter

# from .views import AdhocViewSet, PlaybookViewSet
from .views import AdhocViewSet, KoViewSet

router = DefaultRouter()
router.register(r'adhoc', AdhocViewSet)
router.register(r'ko', KoViewSet, basename="ko")


urlpatterns = [
                  path('', include(router.urls)),
              ] + router.urls

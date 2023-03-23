from typing import Dict

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.parsers import JSONParser, FormParser

from apps.runtime.models import RuntimeAppModel
from apps.runtime.serializer import RuntimeAppModelSerializer


def create_runtime_app(name: str, spec: Dict) -> None:
    from uuid import uuid4
    app = RuntimeAppModel(id=uuid4(), name=name, spec=spec)
    app.save()


def delete_runtime_app(name: str) -> None:
    app = RuntimeAppModel.objects.get(name=name)
    app.delete()


class RuntimeAppModelViewSet(mixins.CreateModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.ListModelMixin,
                             mixins.DestroyModelMixin,
                             mixins.UpdateModelMixin,
                             GenericViewSet):
    queryset = RuntimeAppModel.objects.all()
    serializer_class = RuntimeAppModelSerializer
    lookup_field = 'name'
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    parser_classes = (JSONParser, FormParser)


from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from apps.common.mixins.viewset import PartialUpdateModelMixin
from apps.ops.third_party.ko import check_ko_auth
from ..models import KoModel
from ..serializer import KoSerializer
from ...common.utils.response_data_format import get_response


class KoModelViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     mixins.DestroyModelMixin,
                     PartialUpdateModelMixin,
                     GenericViewSet):
    queryset = KoModel.objects.all()
    serializer_class = KoSerializer

    @action(methods=['post'], detail=False, url_path="check/conn")
    def check_ko_auth_api(self, request):
        req_data = request.data
        check_res = check_ko_auth(req_data)
        return get_response(check_res, no_data=True)

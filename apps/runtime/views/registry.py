from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.common.constant.index import StatusFailed
# 每种架构只有一个仓库
from apps.common.constant.index import StatusSuccess
# from libs.mixins import PartialUpdateModelMixin
from apps.common.mixins.viewset import PartialUpdateModelMixin
from apps.common.utils.response_data_format import get_response
from apps.ops.third_party import nexus
from ..models import TaskRegistryModel
from ..serializer import TaskRegistrySerializer


class TaskRegistryModelViewSet(mixins.CreateModelMixin,
                                 mixins.RetrieveModelMixin,
                                 mixins.ListModelMixin,
                                 mixins.DestroyModelMixin,
                                 PartialUpdateModelMixin,
                                 GenericViewSet):
    queryset = TaskRegistryModel.objects.all()
    serializer_class = TaskRegistrySerializer
    lookup_field = 'architecture'

    @action(methods=['post'], detail=False)
    def search(self, request):
        # TODO: 快速 和 高级搜索
        # 重写 list
        queryset = self.filter_queryset(self.get_queryset())

        # queryset = self.set_status_on_list(queryset)

        page = self.paginate_queryset(queryset.order_by('created_at'))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            res_data = self.set_status_on_list(serializer.data)
            return self.get_paginated_response(res_data)

        serializer = self.get_serializer(queryset, many=True)
        res_data = self.set_status_on_list(serializer.data)

        return Response(res_data)

    @action(methods=['post'], detail=False, url_path="check/conn")
    def conn(self, request):
        req_data = request.data
        check_res = nexus.check_conn(req_data)
        # logger.info('check_res :'{}.format(check_res))
        return get_response(check_res, no_data=True)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset.order_by('created_at'))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            res_data = self.set_status_on_list(serializer.data)
            return self.get_paginated_response(res_data)

        serializer = self.get_serializer(queryset, many=True)
        res_data = self.set_status_on_list(serializer.data)
        return Response(res_data)

    def set_status_on_list(self, registry_list):
        for item in registry_list:
            check_res = nexus.check_conn(item)
            if check_res.status_code == status.HTTP_200_OK:
                item['status'] = StatusSuccess
            else:
                item['status'] = StatusFailed
        return registry_list

    def get_lookup_field_by_action(self):
        if self.action == 'retrieve' or self.action == 'destroy':
            return 'id'
        return self.lookup_field

    def get_object(self):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
        )

        # 根据不同action ，修改为不同的lookup_field
        # filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        filter_kwargs = {self.get_lookup_field_by_action(): self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

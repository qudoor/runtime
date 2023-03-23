from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.common.mixins.viewset import PartialUpdateModelMixin
from ..models import CredentialModel
from ..serializer import CredentialModelSerializer
from ..utils import input_filter, date_filter


class CredentialsViewSet(mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         mixins.DestroyModelMixin,
                         PartialUpdateModelMixin,
                         GenericViewSet):
    queryset = CredentialModel.objects.all()
    serializer_class = CredentialModelSerializer
    # permission_classes = [IsLoginPermission]
    permission_classes = []
    lookup_field = 'name'

    @action(methods=['post'], detail=False)
    def search(self, request):
        res = self.queryset
        total = len(res)

        # 1. 快速查询，查询的字段涉及多个
        quick = request.data.get('quick')
        if quick is not None:
            quickValue = quick.get('value')
            # logger.info('quick.value: {}'.format(quickValue))
            res = self.queryset.filter(name__icontains=quickValue)
            res = res | self.queryset.filter(username__icontains=quickValue)  # 合并 queryset
            res = res | self.queryset.filter(private_key__icontains=quickValue)
            res = res | self.queryset.filter(type__icontains=quickValue)
            res = res | self.queryset.filter(created_at__icontains=quickValue)

        name = request.data.get('name')
        if name is not None:
            res = input_filter(res, name)

        username = request.data.get('username')
        if username is not None:
            res = input_filter(res, username)

        typeres = request.data.get('type')
        if typeres is not None:
            res = input_filter(res, typeres)

        created_at_obj = request.data.get('created_at')
        if created_at_obj is not None:
            res = date_filter(res, created_at_obj)

        res = res.order_by('name')
        # 沿用分页功能: https://q1mi.github.io/Django-REST-framework-documentation/api-guide/viewsets/#viewset-actions
        page = self.paginate_queryset(res)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(res, many=True)
        # 统一分页格式
        return Response({
            'items': serializer.data,
            'total': total
        })

from django.db import transaction
from rest_framework import status, serializers, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.common.constant.cluster import ClusterInitializing, ClusterCreating, ClusterSynchronizing
from apps.common.constant.credential import Password
from apps.common.constant.index import CREDENTIAL_ID, CREDENTIAL
from apps.common.mixins.viewset import PartialUpdateModelMixin
from apps.common.utils.aes import aesDecrypt
from apps.common.utils.common import merge_two_dicts, is_has_key, is_ip
from apps.common.utils.logger import get_logger
from ..custom_celery_tasks import task_get_host_info
from ..models import HostModel, CredentialModel, TaskNodeModel, TaskModel
from ..serializer import HostsSerializer, CredentialModelSerializer
from ..utils import gen_host_data_for_ansible

logger = get_logger(__file__)


class HostsModelViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        mixins.DestroyModelMixin,
                        PartialUpdateModelMixin,
                        GenericViewSet):
    """
    主机功能: 添加 删除 修改 批量导入 授权 同步
    """
    permission_classes = []
    queryset = HostModel.objects.all()
    serializer_class = HostsSerializer
    lookup_field = 'name'

    @action(methods=['post'], detail=False)
    def search(self, request):
        # TODO: 快速 和 高级搜索
        # 重写 list
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset.order_by('created_at'))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # 调用 task 获取主机其他信息
        host = request.data
        self.validator_before_celery(host)

        host_with_credential = self.get_host_with_credential(host, ClusterInitializing)

        host = merge_two_dicts(host, host_with_credential)
        task_get_host_info.delay(hosts_for_ansible=gen_host_data_for_ansible([host]))  # 异步执行

        serializer = self.get_serializer(data=host)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=['post'], detail=False)
    def sync(self, request):
        hosts = request.data
        logger.info(f'sync hosts: {hosts}')

        for host_item in hosts:
            if host_item['host_status'] == ClusterCreating or host_item['host_status'] == ClusterInitializing or \
                    host_item['host_status'] == ClusterSynchronizing:
                continue
            host_update = dict()
            host_update["status"] = ClusterSynchronizing
            instance = self.queryset.get(name=host_item['host_name'])
            serializer = self.get_serializer(instance, data=host_update, partial=True)
            serializer.is_valid()
            self.perform_update(serializer)
            self.sync_by_name(host_item['host_name'])

        return Response(status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='quproduct/(?P<quproduct>[^/.]+)')
    def get_host_by_quproduct(self, request, quproduct):
        tasks = TaskModel.objects.filter(quproduct=quproduct)
        host_ids = []
        for task in tasks:
            spec = task.spec
            if spec is not None:
                if spec.master_host_ids is not None:
                    host_ids.extend(spec.master_host_ids)
                if spec.slave_host_ids is not None:
                    host_ids.extend(spec.slave_host_ids)

        hosts = HostModel.objects.exclude(id__in=host_ids)

        page = self.paginate_queryset(hosts)
        if page is not None:
            return self.get_paginated_response(HostsSerializer(hosts, many=True).data)

        return Response(status=status.HTTP_200_OK, data=HostsSerializer(hosts, many=True).data)

    def sync_by_name(self, host_name):
        host = self.queryset.get(name=host_name).__dict__
        del host['_state']
        host_with_credential = self.get_host_with_credential(host, ClusterInitializing)
        task_get_host_info.delay(hosts_for_ansible=gen_host_data_for_ansible([host_with_credential]))

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        host = request.data
        self.validator_before_celery(host)
        host_with_credential = self.get_host_with_credential(host, ClusterInitializing)
        host = merge_two_dicts(host, host_with_credential)

        task_get_host_info.delay(hosts_for_ansible=gen_host_data_for_ansible([host]))  # 异步执行
        instance = self.get_object()
        if host.get('name') is not None:
            del host['name']  # 名称（name）不可修改，但可新增
        serializer = self.get_serializer(instance, data=host, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    # 删除时，查看是否有关联集群，如果关联集群，则返回 400 : {msg : "删除失败！该主机已经关联集群"}
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        task_node = TaskNodeModel.objects.filter(host=instance.id)
        if len(task_node) > 0:
            res_data = dict()
            res_data['msg'] = "删除失败！该主机已经关联集群"
            return Response(status=status.HTTP_400_BAD_REQUEST, data=res_data)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def get_credential(host):
        if is_has_key(host, CREDENTIAL_ID) and host[CREDENTIAL_ID] != '':
            credential = CredentialModel.objects.filter(id=host[CREDENTIAL_ID]).first()
            credential = credential.__dict__
        elif is_has_key(host, CREDENTIAL):
            credential = host[CREDENTIAL]
            logger.info('创建 credential:{}'.format(credential))
            serializer = CredentialModelSerializer(data=credential)
            serializer.is_valid(raise_exception=True)
            credential = serializer.save().__dict__

        else:
            raise serializers.ValidationError("凭据无效")

        credential[CREDENTIAL_ID] = str(credential['id'])
        credential['id'] = str(credential['id'])
        credential[Password] = aesDecrypt(credential['password'])
        return credential

    @staticmethod
    def validator_before_celery(host):
        if not is_ip(host['ip']):
            raise serializers.ValidationError("ip 格式不正确")
        # elif not is_ip(host['flex_ip']):
        #     raise serializers.ValidationError("flex_ip 格式不正确")

        try:
            if not isinstance(int(host['port']), int):
                raise serializers.ValidationError("port 不是整数")
        except Exception as e:
            raise serializers.ValidationError("port 不是整数")

    def get_host_with_credential(self, host, host_status):
        credential = self.get_credential(host)
        del credential['_state']
        host_with_credential = {
            'name': host['name'],
            'ip': host['ip'],
            'port': host['port'],
            'user': credential['username'],
            'password': credential[Password],
            'private_key': credential['private_key'],
            'groups': ['all'],
            'status': host_status,
            'credential_id': credential['id'],
            'credential': credential,
        }
        return host_with_credential

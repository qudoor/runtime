from rest_framework import mixins, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ViewSet

from apps.common.constant.credential import Password
from .models import AdHocModel
from .serializer import AdhocSerializer
from .third_party.ko import Ko
from .utils import update_or_create_ansible_adhoc, get_host_info
from ..common.constant.cluster import ClusterInitializing
from ..common.constant.index import CREDENTIAL, CREDENTIAL_ID
from ..common.utils.common import merge_two_dicts, is_has_key
from apps.common.utils.logger import get_logger
from apps.common.utils.aes import aesDecrypt
from ..common.utils.format_data import gen_response_data
from ..runtime.models import CredentialModel
from ..runtime.serializer import CredentialModelSerializer
from ..runtime.utils import gen_host_data_for_ansible, updated_failed_status, sync_host_info_with_db

logger = get_logger(__name__)


class AdhocViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):
    queryset = AdHocModel.objects.all()
    serializer_class = AdhocSerializer

    def create(self, request, *args, **kwargs):
        # 调用 task 获取主机其他信息
        host = request.data
        host_with_credential = self.get_host_with_credential(host, ClusterInitializing)
        host = merge_two_dicts(host, host_with_credential)
        task_name = "task_get_host_info"
        tasks = [{"name": "setup", "action": {"module": "setup"}}]
        raw, summary = update_or_create_ansible_adhoc(task_name=task_name, host_data=gen_host_data_for_ansible([host]),
                                                      tasks=tasks,
                                                      celery_task_id="b6ba0101-2c75-4149-8e97-a5058d533ddf")
        hosts_from_call = gen_host_data_for_ansible([host]).get("hosts")
        host_list_info_res = get_host_info(raw, celery_task_id=self.request.id)
        host_list = host_list_info_res['infos'][0]['hosts']
        if host_list_info_res['failed']:
            logger.info("task_get_host_info res: {}".format(host_list_info_res))
            updated_failed_status(host_list)
        else:
            host_all_info_list = sync_host_info_with_db(hosts_from_call, host_list, summary)
            logger.info(host_all_info_list)

        serializer = self.get_serializer(data=host)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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

    def get_credential(self, host):
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


class KoViewSet(ViewSet):

    # pageSize and page
    @action(methods=['post'], detail=False, url_path="clusters/search")
    def clusters_search(self, request):
        logger.info(f'request: {request}')
        try:
            ko = Ko()
            return Response(ko.get_clusters())
        except Exception as e:
            return Response(gen_response_data(msg=e.__str__()))

    @action(methods=['get'], detail=False, url_path="clusters/(?P<name>[^/.]+)")
    def get_cluster_by_name(self, request, name):
        # logger.info(f'request: {request}')
        try:
            ko = Ko()
            return Response(ko.get_cluster_by_name(name))
        except Exception as e:
            return Response(gen_response_data(msg=e.__str__()))

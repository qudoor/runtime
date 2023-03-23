# Create your views here.

from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.appstore.utils import get_chart_url, get_app_list
from apps.common.utils.logger import get_logger
from apps.common.utils.format_data import gen_response_data

logger = get_logger(__file__)


def get_default_ansible_host_data_options():
    local_host_data = {
        "hosts": [
            {
                "name": "localhost",
                "vars": {
                    "ansible_connection": "local",
                    "ansible_become": "no"
                }
            }
        ],
        "groups": [],
    }
    return dict(local_host_data)


def update_host_data(var_data):
    _host_data = get_default_ansible_host_data_options()
    if var_data and isinstance(var_data, dict):
        _host_data.update(var_data)
    return _host_data


def gen_deploy_host_data(app_var_data=None):
    host_data = update_host_data(app_var_data)
    return host_data


class AppStoreViewSet(mixins.ListModelMixin, GenericViewSet):
    permission_classes = []

    def get_serializer(self):  # 解决没定义 serializer 抛出异常
        pass

    @action(methods=['get'], detail=False, url_path="(?P<cluster>[^/.]+)/app_list")
    def app_list(self, request, cluster):
        # 获取nexus仓库信息，默认取第一条
        chart_url = get_chart_url()
        chart_list = get_app_list(chart_url=chart_url, cluster_name=cluster)
        return Response(gen_response_data(success=True, msg='', data=chart_list))

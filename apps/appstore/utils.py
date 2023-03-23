from django.conf import settings

from apps.common.constant.index import StatusWaiting, StatusString
from apps.common.exceptions import NexusException, MyBaseException
from apps.common.utils.logger import get_logger
from apps.ops.kubernetes.apis import get_app_info_by_k8s
from apps.ops.third_party.nexus import get_chart_list
from apps.runtime.models import TaskRegistryModel

logger = get_logger(__file__)


def get_chart_url():
    # todo 按架构划分筛选
    try:
        nexus_repo = TaskRegistryModel.objects.order_by('created_at').first()
    except TaskRegistryModel.DoesNotExist:
        logger.error("未接入Nexus仓库")
        raise NexusException()
    except Exception as err:
        raise MyBaseException(detail=str(err))
    # 拼接nexus 地址
    app_repo_name = "appstore"
    chart_url = "http://{}:{}/repository/{}".format(nexus_repo.hostname, nexus_repo.repo_port,
                                                    app_repo_name)
    return chart_url


def get_app_list(chart_url, cluster_name):
    chart_list = get_chart_list(chart_url)
    app_info_list = get_app_info_by_k8s(chart_url=chart_url, cluster_name=cluster_name,
                                        namespace=settings.APPSTORE_NAMESPACE)
    set_app_status_and_url(chart_list=chart_list, app_info_list=app_info_list, cluster_name=cluster_name)
    return chart_list


# 通过 k8s 判断是否运行中(Running) 或 未安装（Waitting）
def set_app_status_and_url(chart_list, app_info_list, cluster_name):
    for chart_item in chart_list:
        chart_item[StatusString] = StatusWaiting
        for app_item in app_info_list:
            if app_item.get('name') == chart_item.get('name'):
                if app_item.get(StatusString):
                    chart_item[StatusString] = app_item.get(StatusString)
                if app_item.get('qudomain'):
                    chart_item['url'] = 'http://' + app_item.get('qudomain')
                if app_item.get('type'):
                    chart_item['proxyType'] = app_item.get('type').lower()
                # TODO: 优化, 引用类型无法更新 chart_item = merge_two_dicts(chart_item, app_item)
                # print("chart_item: ", chart_item)

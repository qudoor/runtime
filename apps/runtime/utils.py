import random

from apps.common.constant.cluster import ClusterFailed, ClusterRunning
from apps.common.constant.health_check import CheckHostSSHConnection, StatusSuccess, StatusWarning
from apps.common.utils.check_condition import is_failed_status_by_summary
from apps.common.utils.common import merge_two_dicts
from apps.common.utils.logger import get_logger
from .models import HostModel
from .serializer import HostsSerializer

logger = get_logger(__file__)


class HooksCreated:
    def __init__(self, ansible_response_summary):
        self.ansible_response_summary = ansible_response_summary

    @property
    def msg(self) -> dict:
        msg = self.get_msg()
        return msg

    def get_msg(self) -> dict:
        res = {
            "name": CheckHostSSHConnection,
            "level": StatusSuccess,
            "msg": "",
            "adjustValue": "",
        }
        if is_failed_status_by_summary(self.ansible_response_summary):
            res['level'] = StatusWarning
            if self.ansible_response_summary['unreachable']:
                res['msg'] = "Ping unreachable: " + str(self.ansible_response_summary['unreachable'])
            if self.ansible_response_summary['failed']:
                res['msg'] += "Ping failed: " + str(self.ansible_response_summary['failed'])
        return res


class HealthCheck:
    # TODO: gen hooks
    def __init__(self, hooks):
        self.hooks = hooks

    @property
    def health_check_response(self) -> dict:
        res = {
            "hooks": self.hooks,
            "level": StatusSuccess,
        }
        return res


def gen_host_data_for_ansible(hosts):
    return {
        "hosts": hosts,
        "groups": [],
        "vars": []
    }


def get_arch(arch, is_ansible=False):
    if arch == 'amd64' or arch == 'x86_64':
        if is_ansible:
            return 'amd64'
        return 'x86_64'
    elif arch == 'arm64' or arch == 'aarch64':
        if is_ansible:
            return 'arm64'
        return 'aarch64'
    return arch


def updated_failed_status(hosts):
    logger.info("updated_failed_status: {}".format(hosts))
    for host_item in hosts:
        logger.info("updated_failed_status host_item: {}".format(host_item))
        host_dict = dict()
        host_dict['status'] = ClusterFailed
        host_dict['message'] = str(host_item)
        instance = HostModel.objects.get(name=host_item['name'])
        logger.info('updated_failed_status host_item:{}'.format(host_item))

        # 传入instance实例时调用update方法,无实例传入时调用的是create()方法
        serializer = HostsSerializer(instance, data=host_dict, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()


def sync_host_info_with_db(hosts, host_list, summary):
    host_all_info_list = []
    if not host_list or len(host_list) == 0:
        return []
    for host_item in host_list:
        pre_host = (x for x in hosts if x['name'] == host_item['name'])
        pre_host = list(pre_host)[0]
        task_res_host = merge_two_dicts(host_item, pre_host)
        if is_failed_status_by_summary(summary):
            task_res_host['status'] = ClusterFailed
            task_res_host['message'] = task_res_host['msg']
        else:
            task_res_host['status'] = ClusterRunning

        # task_res_host['has_gpu'] = False
        instance = HostModel.objects.get(name=task_res_host['name'])
        host_all_info_list.append(task_res_host)

        # 传入instance实例时调用update方法,无实例传入时调用的是create()方法
        serializer = HostsSerializer(instance, data=task_res_host, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    return host_all_info_list


def input_filter(res, obj):
    operator = obj.get('operator')
    field = obj.get('field')
    value = obj.get('value')
    if operator == 'like':
        res = res.filter(**{field + '__' + 'icontains': value})
    elif operator == 'not like':
        res = res.exclude(**{field + '__' + 'icontains': value})
    elif operator == 'eq':
        res = res.filter(**{field + '__' + 'exact': value})
    elif operator == 'ne':
        res = res.exclude(**{field + '__' + 'exact': value})
    elif operator == 'in':
        res = res.filter(**{field + '__' + 'in': value})
    elif operator == 'not in':
        res = res.exclude(**{field + '__' + 'in': value})

    return res


# https://docs.djangoproject.com/zh-hans/4.0/ref/models/querysets/#id4
def date_filter(res, obj):
    operator = obj.get('operator')
    field = obj.get('field')
    value = obj.get('value')

    if operator == 'between':
        start_date = value[0]
        end_date = value[1]
        res = res.filter(**{field + '__range': (start_date, end_date)})
    elif operator == 'eq':
        res = res.filter(**{field + '__date': value})
    elif operator == 'gt':
        res = res.filter(**{field + '__date__gt': value})
    elif operator == 'ge':
        res = res.filter(**{field + '__date__gte': value})
    elif operator == 'lt':
        res = res.filter(**{field + '__date__lt': value})
    elif operator == 'le':
        res = res.filter(**{field + '__date__lte': value})

    return res


def gen_rand_char(length=16, chars='0123456789zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA'):
    return ''.join(random.sample(chars, length))

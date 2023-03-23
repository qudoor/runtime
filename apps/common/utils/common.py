import json
import os
import uuid
from datetime import datetime

import IPy
import yaml
from ansible.errors import AnsibleError
from django.conf import settings

from QuPot.settings import K8S_CONFIG
from apps.common.exceptions import MyBaseException
from apps.ops.third_party.ko import Ko


# 解决json自动dumps 含有datetime问题
class DTEncoder(json.JSONEncoder):
    def default(self, obj):
        # if passed in object is datetime object
        # convert it to a string
        if isinstance(obj, datetime):
            return str(obj)
        # otherwise use the default behavior
        return json.JSONEncoder.default(self, obj)


def yaml_to_json(yaml_file):
    if not os.path.exists(yaml_file):
        raise MyBaseException(detail="文件不存在：" + yaml_file)

    with open(yaml_file, 'r') as file:
        data = file.read()
    res = yaml.load(data, Loader=yaml.FullLoader)
    json_out = json.dumps(res, cls=DTEncoder)
    json_data = json.loads(json_out)
    return json_data


def merge_two_dicts(dict1, dict2):
    """
    Merge two dicts into one and return.
    result = {**dict1, **dict2} only works in py3.5+.
    """
    # dict2 会覆盖 dict1
    result = dict1.copy()
    result.update(dict2)
    return result


def is_ip(address):
    try:
        IPy.IP(address)
        return True
    except Exception as e:
        return False


def is_has_key(n_dict, key):
    '''
    判断地点是否含有key
    '''
    assert isinstance(n_dict, dict)
    # for k in n_dict.keys():
    #     if k == key:
    #         return True
    # return False
    return key in n_dict.keys()


def get_task_log_path(base_path, task_id):
    task_id = str(task_id)
    try:
        uuid.UUID(task_id)
    except:
        return os.path.join(settings.BASE_DIR, 'logs', 'caution.txt')

    rel_path = os.path.join(task_id + '.log')
    path = os.path.join(base_path, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def get_celery_task_log_path(task_id):
    celery_path = os.path.join(settings.BASE_DIR, "logs", "celery")
    return get_task_log_path(celery_path, task_id)


def get_ansible_task_log_path(task_id, log_type):
    log_type_choices = ('adhoc', 'celery', 'playbook')
    if log_type not in log_type_choices:
        raise AnsibleError("log_type type error")
    ansible_path = os.path.join(settings.BASE_DIR, "data", "ansible", log_type)
    return get_task_log_path(ansible_path, task_id)


# 判断字符串是否为数字
# Python isdigit() 方法检测字符串是否只由数字组成。
# Python isnumeric() 方法检测字符串是否只由数字组成。这种方法是只针对unicode对象。
# https://blog.csdn.net/m0_37622530/article/details/81289520
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


def str_to_number(value):
    if float(value).is_integer():
        return int(value)
    else:
        return float(value)


# K，M，G，T，P，E #通常是以1000为换算标准的。
# Ki，Mi，Gi，Ti，Pi，Ei #通常是以1024为换算标准的
def convert_memory_unit_to_Mi(value):
    if value is None:
        return None
    value = str(value)

    if value.endswith("Ki"):
        res = round((str_to_number(value.replace('Ki', '')) / 1024), 2)
    elif value.endswith("Mi"):
        res = round(str_to_number(value.replace('Mi', '')), 2)
    elif value.endswith("Gi"):
        res = str_to_number(value.replace('Gi', '')) * 1024
    else:
        res = str_to_number(value)
    return res


def convert_cpu_unit_to_m(value):
    if value is None:
        return None
    value = str(value)

    if value.endswith("u"):
        res = round((str_to_number(value.replace('u', '')) / 1000000000), 2)
    elif value.endswith("n"):
        res = round((str_to_number(value.replace('n', '')) / 1000000), 2)
    elif value.endswith("m"):
        res = str_to_number(value.replace('m', ''))
    else:
        res = str_to_number(value) * 1000
    return res


def get_k8s_config_file(cluster_name):
    config_file = K8S_CONFIG + "/" + cluster_name
    if not os.path.exists(config_file):
        ko = Ko()
        ko.download_all_cluster_config_by_session()
    return config_file

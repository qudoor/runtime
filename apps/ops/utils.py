import math

from apps.common.utils.common import merge_two_dicts
from apps.common.utils.logger import get_logger
from .models import AdHocModel, PlayBookModel

logger = get_logger(__file__)

DEFAULT_TASK_OPTIONS = {
    '''
    timeout：超时10秒
    forks: 线程数10
    '''
    'timeout': 10,
    'forks': 10,
    'become': True,
    'become_method': "sudo",
    'become_user': "root",
}


def update_or_create_ansible_adhoc(
        task_name, host_data, tasks, options=None,
        celery_task_id=None):
    '''
    :param task_name:
    :param host_data:
    :param tasks:
    :param options:
    :param celery_task_id:
    :return:
    '''
    if not host_data or not tasks or not task_name:
        return None, None
    if options is None:
        options = DEFAULT_TASK_OPTIONS

    adhoc = AdHocModel(tasks=tasks, task_name=task_name,
                       options=options,
                       celery_task_id=celery_task_id, host_data=host_data)
    adhoc.save()
    raw, summary = adhoc.start()
    return raw, summary


def get_host_info(raw, celery_task_id):
    "获取主机info"
    host_var = dict()
    success_result = raw.get('ok', {})
    unreachable_result = raw.get('unreachable', {})
    failed_result = raw.get('failed', {})
    infos = []
    info = dict()
    info['task_id'] = celery_task_id
    info['hosts'] = []
    res = dict()
    res['failed'] = False

    # 存在报错则返回
    if unreachable_result:
        res['failed'] = True
        for k, v in unreachable_result.items():
            host_var['name'] = k
            host_var = merge_two_dicts(host_var, v)
        info['hosts'].append(host_var)
        infos.append(info)
        logger.error("unreachable_result {}".format(infos))
        res['infos'] = infos
        return res
    if failed_result:
        res['failed'] = True
        for k, v in failed_result.items():
            host_var['name'] = k
            host_var = merge_two_dicts(host_var, v)
        info['hosts'].append(host_var)
        infos.append(info)
        logger.error("failed_result {}".format(infos))
        res['infos'] = infos
        return res

    for k, v in success_result.items():
        '''
        k 是主机host,v是主机值
        '''
        host_var['name'] = k
        host_var['memory'] = math.ceil(int(v['setup']['ansible_facts']['ansible_memtotal_mb']) / 1024)
        host_var['cpu_core'] = int(v['setup']['ansible_facts']['ansible_processor_vcpus'])
        host_var['os'] = v['setup']['ansible_facts']['ansible_distribution']
        host_var['os_version'] = v['setup']['ansible_facts']['ansible_distribution_version']
        host_var['architecture'] = v['setup']['ansible_facts']['ansible_architecture']
    info['hosts'].append(host_var)
    infos.append(info)
    res['infos'] = infos
    logger.info(f'task_id:{celery_task_id},get hosts info success')
    return res


def update_or_create_ansible_playbook(
        playbook_name, hosts_data, options=None,
        celery_task_id=None):
    '''
    :param playbook_name:
    :param hosts_data:
    :param options:
    :param celery_task_id:
    :return:
    '''
    if not hosts_data or not playbook_name:
        return None, None
    if options is None:
        options = DEFAULT_TASK_OPTIONS

    pb = PlayBookModel(playbook_name=playbook_name,
                       options=options,
                       celery_task_id=celery_task_id, hosts_data=hosts_data)
    pb.save()
    raw, summary = pb.start()
    return raw, summary

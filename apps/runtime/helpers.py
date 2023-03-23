#!/usr/bin/env python
import logging
from typing import List, Tuple, Dict, Any
from django.core.exceptions import FieldError
from celery import chain
from apps.common.utils.aes import aesDecrypt
from apps.common.constant.index import CREDENTIAL_ID

from .custom_celery_tasks import task_run_playbook
from .custom_celery_tasks import task_set_task_condition
from .custom_celery_tasks import task_change_task_status
from .utils import get_arch
from .models import TaskModel
from .models import TaskRegistryModel
from .models import TaskSpecModel
from .models import HostModel
from .models import CredentialModel
from .models import RuntimeAppModel

logger = logging.getLogger(__name__)


class RuntimeTaskHelper:

    def __init__(self, task: TaskModel, playbook_list: List[str] = None):
        self._task = task
        self.ansible_data = self.prepare_ansible_data(task.spec)
        self.playbook_list = playbook_list if playbook_list else task.get_playbook_list()

    @staticmethod
    def generate_ansible_host(registers: Dict[str, Any], id_set: list) -> Tuple[list, list]:
        hosts = []
        group_hosts = []
        for host in HostModel.objects.filter(id__in=id_set):
            credential_id = getattr(host, CREDENTIAL_ID)
            try:
                credential = CredentialModel.objects.get(id=credential_id)
            except CredentialModel.DoesNotExist:
                raise RuntimeError(f'credential {credential_id} not found')

            register = registers[get_arch(host.architecture)]

            _host = {
                "ip": host.ip,
                "name": host.name,
                "port": host.port,
                "user": credential.username,
                "password": aesDecrypt(credential.password),
                "vars": {
                    "architectures": get_arch(host.architecture, True),
                    "has_gpu": host.has_gpu,
                    "registry_hosted_port": register['registry_hosted_port'],
                    "registry_hostname": register['hostname'],
                    "registry_port": register['registry_port'],
                    "registry_protocol": register['protocol'],
                    "repo_port": register['repo_port']
                }
            }
            hosts.append(_host)
            group_hosts.append(host.name)

        return hosts, group_hosts

    def prepare_ansible_data(self, spec: TaskSpecModel) -> Dict[str, Any]:
        logger.info(f'received spec data: {spec}')

        arch = get_arch(spec.architectures)
        register_all = dict()
        if arch == 'all':
            register_all["x86_64"] = TaskRegistryModel.objects.filter(architecture="x86_64").first().__dict__
            register_all["aarch64"] = TaskRegistryModel.objects.filter(architecture="aarch64").first().__dict__
        else:
            register_all[arch] = TaskRegistryModel.objects.filter(architecture=arch).first().__dict__

        master_hosts, master_group_hosts = self.generate_ansible_host(register_all, spec.master_host_ids)
        slave_hosts, slave_group_hosts = self.generate_ansible_host(register_all, spec.slave_host_ids)
        data = {
            "hosts": master_hosts + slave_hosts,
            "groups": [
                {"name": "qupot-master", "hosts": master_group_hosts},
                {"name": "qupot-worker", "hosts": slave_group_hosts, "children": ["qupot-master"]},
                {"name": "new-worker", "hosts": []},
                {"name": "chrony", "hosts": []},
            ],
            "vars": {
                "yum_operate": spec.yum_operate,
            }
        }
        # 依赖包 设置变量
        for dependent in spec.dependents:
            data['vars'].update(dependent)

        if spec.processing_unit:
            data['vars'].update({'processing_unit': spec.processing_unit})

        logger.info(f'gen_host_data res: {data}')
        return data

    def generate_task(self, playbook_name, playbook):
        """
        summary将作为参数传递到task_set_task_condition中。
        根据代码task_run_playbook.si(...) 的返回值，task_set_task_condition将作为管道的下一个任务，接受task_run_playbook的返回值作为参数。
        """
        return (
                task_run_playbook.si(
                    hosts_data=self.ansible_data,
                    playbook=playbook,
                    task_name=self._task.name
                ) |
                task_set_task_condition.s(
                    task_name=self._task.name,
                    playbook_name=playbook_name
                )
        )

    def generate_task_list(self):
        if len(self.playbook_list) == 0:
            raise FieldError("playbook_file_list is empty")

        logger.info(f"playbook_file_list :{self.playbook_list}")
        task_list = []
        for file_name in self.playbook_list:
            # TODO: 配置名字: playbook_name, 配合作为前端显示的文字
            task = self.generate_task(file_name, file_name + '.yml')
            task_list.append(task)

        task_list.append(task_change_task_status.s(task_name=self._task.name))
        logger.info(f"task_name: {self._task.name}, generate_task_list :{task_list}")
        return task_list

    def generate_task_chain(self) -> chain:
        task_list = self.generate_task_list()
        return chain(*task_list)

    def generate_retry_task_chain(self) -> chain:
        task_list = self.generate_task_list()
        return chain(*task_list)

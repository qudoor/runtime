import datetime
import json

from QuPot.settings._celery import app
from QuPot.settings.base import PlayBOOK_OPTIONS
from apps.common.constant.cluster import ClusterFailed, ClusterRunning, ConditionTrue, ConditionFalse
from apps.common.utils.check_condition import is_failed_status_by_summary
from apps.common.utils.logger import get_logger
from apps.ops.ansible.display import get_ansible_task_log_path
from .models import TaskModel, TaskStatusModel
from .models import TaskStatusConditionModel
from .models import TaskCondition
from .serializer import TaskStatusSerializer, TaskStatusConditionSerializer
from .utils import updated_failed_status, sync_host_info_with_db
from ..ops.utils import update_or_create_ansible_adhoc, get_host_info, update_or_create_ansible_playbook

logger = get_logger(__file__)


@app.task(serializer='json', bind=True)
def task_get_host_info(self, hosts_for_ansible):
    try:
        task_name = "task_get_host_info"
        tasks = [{"name": "setup", "action": {"module": "setup"}}]
        logger.info(f'task_id: {self.request.id},ready to run ansible')
        raw, summary = update_or_create_ansible_adhoc(task_name=task_name, host_data=hosts_for_ansible, tasks=tasks,
                                                      celery_task_id=self.request.id)
        hosts_from_call = hosts_for_ansible.get("hosts")
        host_list_info_res = get_host_info(raw, celery_task_id=self.request.id)
        host_list = host_list_info_res['infos'][0]['hosts']
        if host_list_info_res['failed']:
            logger.error(f'task_id: {self.request.id} task_get_host_info res: {host_list_info_res}')
            updated_failed_status(host_list)
        else:
            sync_host_info_with_db(hosts_from_call, host_list, summary)
            logger.info(f'task_id: {self.request.id},sync success')
        # return host_all_info_list
    except Exception as e:
        logger.error(e)


@app.task(serializer='json', bind=True)
def task_run_playbook(self, hosts_data, playbook, task_name=None):
    logger.info("task_run_playbook playbook: {}".format(playbook))
    try:
        if task_name:
            task_from_db = TaskModel.objects.filter(name=task_name)
            task_from_db.update(log_id=self.request.id)
        raw, summary = update_or_create_ansible_playbook(playbook_name=playbook, hosts_data=hosts_data,
                                                         options=PlayBOOK_OPTIONS, celery_task_id=self.request.id)
        return summary
    except Exception as e:
        logger.error(e)


@app.task(serializer='json', bind=True)
def task_run_playbook_without_db(self, host_data, playbook):
    logger.info("task_run_playbook_without_db playbook: {}".format(playbook))
    try:
        raw, summary = update_or_create_ansible_playbook(playbook_name=playbook, hosts_data=host_data,
                                                         options=PlayBOOK_OPTIONS, celery_task_id=self.request.id)
        return raw, summary
    except Exception as e:
        logger.error(e)


@app.task(serializer='json', bind=True)
def task_set_task_condition(self, summary, task_name, playbook_name):
    try:
        task_from_db = TaskModel.objects.get(name=task_name)
        task_condition = TaskStatusConditionModel.objects.get(task_id=task_from_db.id, name=playbook_name)

    except TaskModel.DoesNotExist:
        logger.error(f"TaskModel not exist: task_name {task_name}")
        raise RuntimeError

    except TaskStatusConditionModel.DoesNotExist:
        logger.error(f"TaskStatusConditionModel not exist: "
                     f"task_name: {task_name} playbook_name: {playbook_name}")
        raise RuntimeError

    logger.info(f"summary: {summary}, "
                f"task_set_task_condition task_name: {task_name}, "
                f"task_from_db: {task_from_db}")
    logger.info(f"status_id: {task_from_db.status.id}")

    if is_failed_status_by_summary(summary):
        logger.warning("task_set_task_condition success false")
        task_condition.message = json.dumps(summary.get("dark", ""))
        task_condition.status = TaskCondition.FAILED.value
        task_condition.save()

        change_task_status(summary, task_name)

        self.request.chain = None
        # self.request.callbacks = None
        # 失败后，中断 celery 链 https://stackoverflow.com/questions/17461374/celery-stop-execution-of-a-chain
    else:
        logger.info("task_set_task_condition success")
        task_condition.status = TaskCondition.SUCCESS.value
        task_condition.save()

    return summary


@app.task(serializer='json', bind=True)
def task_change_task_status(self, summary, task_name):
    change_task_status(summary, task_name)


def change_task_status(summary, task_name):
    try:
        logger.info(f"task_change_task_status task summary: {summary}, task_name: {task_name}")
        task_status = dict()
        # summary success 为 True，而且 dark 为空，才是正常
        if is_failed_status_by_summary(summary):
            logger.info("success false")
            task_status['status'] = ClusterFailed
            task_status['message'] = json.dumps(summary.get("dark"))
        else:
            task_status['status'] = ClusterRunning

        task_from_db = TaskModel.objects.get(name=task_name)
        logger.info(f"task_from_db : {task_from_db}")
        instance = getattr(task_from_db, "status", None)
        logger.info(f"instance : {instance}")

        # 传入instance实例时调用update方法,无实例传入时调用的是create()方法
        serializer = TaskStatusSerializer(instance, data=task_status, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
    except Exception as e:
        logger.error(e)


@app.task(serializer='json', bind=True)
def task_tail_ansible_log(self, task_name):
    try:
        task = TaskModel.objects.get(name=task_name)
        task_logid = task.log_id
        if task_logid:
            log_type = "playbook"
            log_path = get_ansible_task_log_path(task_logid, log_type)

            log_content = []
            log_content += [line for line in open(log_path, 'r', encoding='UTF-8')]
        res = {
            "msg": "".join(log_content)
        }
        return res
    except Exception as e:
        logger.error(f"get_logger error: {e}")


@app.task(serializer='json', bind=True)
def task_ping_host(self, hosts):
    try:
        task_name = "task_ping_host"
        tasks = [{"name": "ping", "action": {"module": "ping"}}]
        raw, summary = update_or_create_ansible_adhoc(
            task_name=task_name,
            host_data=hosts,
            tasks=tasks,
            celery_task_id=self.request.id
        )
        return summary
    except Exception as e:
        logger.error(e)

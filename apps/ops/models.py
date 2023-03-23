# Create your models here.

import uuid
import time
import os

from ansible.errors import AnsibleError

from django.db import models
from django.conf import settings
from django.utils import timezone

from .ansible.runner import AdHocRunner, PlayBookRunner
from .ansible.inventory import BaseInventory
from apps.common.utils.logger import get_logger

from apps.common.db.fields import (
    JsonDictTextField, JsonListTextField, JsonDictCharField
)

logger = get_logger(__file__)


class AdHocModel(models.Model):
    """
    AdHoc running history.
    """
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    task_name = models.CharField(max_length=128, blank=True, default='', verbose_name="Task display")
    tasks = JsonListTextField(verbose_name='Tasks')
    options = JsonDictCharField(max_length=1024, default='', verbose_name='Options')
    celery_task_id = models.UUIDField(default=None, null=True)
    date_start = models.DateTimeField(auto_now_add=True, verbose_name='Start time')
    date_finished = models.DateTimeField(blank=True, null=True, verbose_name='End time')
    timedelta = models.FloatField(default=0.0, verbose_name='Time', null=True)
    is_finished = models.BooleanField(default=False, verbose_name='Is finished')
    is_success = models.BooleanField(default=False, verbose_name='Is success')
    result = JsonDictTextField(blank=True, null=True, verbose_name='Adhoc raw result')
    summary = JsonDictTextField(blank=True, null=True, verbose_name='Adhoc result summary')
    host_data = JsonDictTextField(blank=True, null=True, verbose_name='hostdata')

    @property
    def short_id(self):
        return str(self.id).split('-')[-1]

    @property
    def inventory(self):
        return BaseInventory(self.host_data)

    def start_runner(self):
        runner = AdHocRunner(self.inventory, options=self.options)

        try:
            result = runner.run(
                tasks=self.tasks,
                execution_id=self.celery_task_id
            )
            return result.results_raw, result.results_summary
        except Exception as e:
            logger.error(f'task_id:{self.celery_task_id},RUN_ANSIBLE_ERROR:{e}')
            return {}, {}

    def start(self):
        summary = {}
        raw = ''
        time_start = time.time()
        try:
            raw, summary = self.start_runner()
        except Exception as e:
            print(e, exc_info=True)
            raw = {"dark": {"all": str(e)}, "contacted": []}
        finally:
            self.add_record(raw, summary, time_start)
            return raw, summary

    def add_record(self, raw, summary, time_start):
        is_success = summary.get('success', False)
        AdHocModel.objects.filter(id=self.id).update(
            is_finished=True,
            is_success=is_success,
            date_finished=timezone.now(),
            timedelta=time.time() - time_start,
            summary=summary,
            result=raw
        )

    @property
    def success_hosts(self):
        return self.summary.get('contacted', [])

    @property
    def failed_hosts(self):
        return self.summary.get('dark', {})

    def __str__(self):
        return self.short_id

    class Meta:
        db_table = "qupot_ops_adhoc"
        get_latest_by = 'date_start'
        verbose_name = "AdHoc execution"


class PlayBookModel(models.Model):
    """
    AdHoc running history.
    """
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    playbook_name = models.CharField(max_length=128, blank=True, default='', verbose_name="playbook_name")
    options = JsonDictCharField(max_length=1024, default='', verbose_name='Options')
    celery_task_id = models.UUIDField(default=None, null=True)
    date_start = models.DateTimeField(auto_now_add=True, verbose_name='Start time')
    date_finished = models.DateTimeField(blank=True, null=True, verbose_name='End time')
    timedelta = models.FloatField(default=0.0, verbose_name='Time', null=True)
    is_finished = models.BooleanField(default=False, verbose_name='Is finished')
    is_success = models.BooleanField(default=False, verbose_name='Is success')
    result = JsonDictTextField(blank=True, null=True, verbose_name='Playbook raw result')
    summary = JsonDictTextField(blank=True, null=True, verbose_name='Playbook result summary')
    hosts_data = JsonDictTextField(blank=True, null=True, verbose_name='hostdata')

    @property
    def short_id(self):
        return str(self.id).split('-')[-1]

    @property
    def inventory(self):
        return BaseInventory(self.hosts_data)

    @property
    def playbook(self):
        return os.path.join(settings.PLAYBOOK_ROOT, self.playbook_name)

    @property
    def variables_yml(self):
        return os.path.join(settings.PLAYBOOK_ROOT, "variables.yml")

    @property
    def playbook(self):
        return os.path.join(settings.PLAYBOOK_ROOT, self.playbook_name)

    def start_runner(self):
        runner = PlayBookRunner(self.inventory, options=self.options, playbook=self.playbook)
        result = runner.run(
            execution_id=self.celery_task_id,
            extra_vars_opt=self.variables_yml
        )
        return result.results_raw, result.results_summary

    def start(self):
        summary = {}
        raw = ''
        time_start = time.time()
        try:
            raw, summary = self.start_runner()
        except AnsibleError as e:
            logger.error("Failed ansible error {}, {}".format(self.playbook, e))
            raw = {"dark": {"all": str(e)}, "contacted": []}
        except Exception as e:
            logger.error("Failed run playbook {}, {}".format(self.playbook, e))
            raw = {"dark": {"all": str(e)}, "contacted": []}
        finally:
            self.add_record(raw, summary, time_start)
            return raw, summary

    def add_record(self, raw, summary, time_start):
        is_success = summary.get('success', False)
        PlayBookModel.objects.filter(id=self.id).update(
            is_finished=True,
            is_success=is_success,
            date_finished=timezone.now(),
            timedelta=time.time() - time_start,
            summary=summary,
            result=raw
        )

    @property
    def success_hosts(self):
        return self.summary.get('contacted', [])

    @property
    def failed_hosts(self):
        return self.summary.get('dark', {})

    def __str__(self):
        return self.short_id

    class Meta:
        db_table = "qupot_ops_playbook"
        get_latest_by = 'date_start'
        verbose_name = "playbook execution"

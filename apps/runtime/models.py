# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
# https://blog.csdn.net/Victor2code/article/details/105303686
# 所以对于managed=False的表，想要改变表结构，只有两种方法：
# 直接在数据库中修改表结构，然后还是利用inspectdb的方法反向生成模型类来使用
# 这种方法值得推荐，也是官方推荐的方法
import uuid
import copy
import logging
from typing import List
from django.core.exceptions import ValidationError
from django.db import models
from django.dispatch import receiver

from apps.common.db.basemodel import BaseModel
from apps.common.utils.aes import aesEncrypt, aesDecrypt
from apps.common.constant.cluster import ClusterInitializing
from apps.common.constant.cluster import NodeRoleNameMaster, NodeRoleNameWorker

logger = logging.getLogger(__name__)


class ProcessingUnit(models.TextChoices):
    CPU = 'CPU', 'CPU'
    GPU = 'GPU', 'GPU'


class TaskCondition(models.TextChoices):
    """
    任务状态
    """
    PENDING = 'pending', 'Pending'
    RUNNING = 'running', 'Running'
    SUCCESS = 'success', 'Success'
    FAILED = 'failed', 'Failed'


class TaskModel(BaseModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="自定义id")
    name = models.CharField(unique=True, max_length=255, null=True)
    quproduct = models.CharField(max_length=255, null=True)
    # runtime_app_id = models.CharField(max_length=255, blank=True, null=True) # 通过 nexus 获取 ip 所以没有
    source = models.CharField(max_length=255, blank=True, null=True)

    plan_id = models.CharField(max_length=255, blank=True, null=True)
    log_id = models.CharField(max_length=255, blank=True, null=True)
    dirty = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"TaskModel<name={self.name}, product={self.quproduct}>"

    def get_playbook_list(self) -> List[str]:
        """
        获取任务的 playbook filename 列表
        """
        try:
            prod = RuntimeAppModel.objects.get(name=self.quproduct)
        except RuntimeAppModel.DoesNotExist:
            logger.warning(f"QuProduct not found: {self.quproduct}.")
            return []
        out = prod.playbooks(processing_unit=self.spec.processing_unit)
        logger.debug(f"{self} Playbook list: {out}")
        return out

    class Meta:
        db_table = 'qupot_runtime_task'


class TaskSpecModel(BaseModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="自定义id")
    version = models.CharField(max_length=255, blank=True, null=True)
    architectures = models.CharField(max_length=255, blank=True, null=True)
    master_host_ids = models.JSONField(max_length=255, blank=True, null=True)
    slave_host_ids = models.JSONField(max_length=255, blank=True, null=True)
    # registry_id = models.IntegerField(blank=True, null=True)
    max_node_num = models.IntegerField(blank=True, null=True)
    upgrade_version = models.CharField(max_length=255, blank=True, null=True)
    yum_operate = models.CharField(max_length=255, blank=True, null=True)

    dependents = models.JSONField(default=list)

    processing_unit = models.CharField(
        max_length=32,
        choices=ProcessingUnit.choices,
        default=ProcessingUnit.CPU.value
    )

    task = models.OneToOneField(
        TaskModel, related_name='spec', on_delete=models.CASCADE, null=True
    )

    class Meta:
        db_table = 'qupot_runtime_task_spec'


class TaskStatusModel(BaseModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="自定义id")
    message = models.TextField(blank=True, null=True, verbose_name="信息")
    node_cluster_id = models.CharField(max_length=64, blank=True, null=True)
    status = models.CharField(max_length=255, default=ClusterInitializing)  # 对应 ko 项目中的 phase
    pre_status = models.CharField(max_length=255, blank=True, null=True)  # 对应 ko 项目中的 pre_phase

    task = models.OneToOneField(
        TaskModel, related_name='status', on_delete=models.CASCADE, null=True
    )

    class Meta:
        db_table = 'qupot_runtime_task_status'


class TaskStatusConditionModel(BaseModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="自定义id")
    name = models.CharField(max_length=255, blank=True, null=True)
    task_status_id = models.CharField(max_length=64, blank=True, null=True)
    task_id = models.CharField(max_length=64, blank=True, null=True, verbose_name="所属taskmodel的id")

    status = models.CharField(
        max_length=32,
        choices=TaskCondition.choices,
        default=TaskCondition.PENDING.value
    )

    message = models.TextField(blank=True, null=True)
    order_num = models.IntegerField(blank=True, null=True)
    last_probe_time = models.DateTimeField(blank=True, null=True, verbose_name="上次查看时间")

    class Meta:
        db_table = 'qupot_runtime_task_status_conditions'


class CredentialModel(BaseModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="自定义id")
    name = models.CharField(unique=True, max_length=255)
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    private_key = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=255, blank=False, null=True)  # password or private_key

    # 重写 save ，加密密码
    def save(self, *args, **kwargs):
        _m = aesEncrypt(self.password)
        self.password = _m
        super(CredentialModel, self).save(*args, **kwargs)

    class Meta:
        db_table = 'qupot_runtime_credential'


class HostModel(BaseModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="自定义id")
    name = models.CharField(unique=True, max_length=255, verbose_name="主机名称")
    memory = models.IntegerField(blank=True, null=True, verbose_name="内存值")
    cpu_core = models.IntegerField(blank=True, null=True, verbose_name="cpu数量")
    os = models.CharField(max_length=64, blank=True, null=True, verbose_name="操作系统")
    os_version = models.CharField(max_length=64, blank=True, null=True, verbose_name="系统版本")
    gpu_num = models.IntegerField(blank=True, null=True, verbose_name="GPU数量")
    gpu_info = models.CharField(max_length=128, blank=True, null=True, verbose_name="GPU信息")
    ip = models.CharField(unique=True, max_length=128, verbose_name="ip信息")
    flex_ip = models.CharField(max_length=128, blank=True, null=True, verbose_name="弹性ip")
    port = models.CharField(max_length=64, blank=True, null=True, verbose_name="服务器端口")
    credential_id = models.CharField(max_length=64, blank=True, null=True, verbose_name="密钥id")
    status = models.CharField(max_length=64, blank=True, null=True,
                              verbose_name="运行状态")
    # task_id = models.CharField(max_length=64, blank=True, null=True, verbose_name="应用环境id")
    message = models.TextField(blank=True, null=True, verbose_name="信息")
    has_gpu = models.BooleanField(blank=True, null=True, verbose_name="是否有GPU")  # 默认没有 false
    architecture = models.CharField(max_length=255, blank=True, null=True, verbose_name="系统架构")

    def get_host_password_or_privatekey(self):
        '''
        获取host的密码或者密钥
        '''
        credential = CredentialModel.object.get(id=self.credential_id)
        if not credential:
            raise ValidationError("not credential")
        if credential.type == "password":
            host_password = aesDecrypt(credential.password)
            if not host_password:
                raise ValidationError("Password decryption failed ")
        elif credential.type == "private_key":
            host_private_key = credential.private_key
        else:
            return ValidationError("credential type error")

        return host_password, host_private_key

    def get_host_config(self):
        password, private_key = self.get_host_password_or_privatekey()
        pass

    class Meta:
        db_table = 'qupot_runtime_host'


class TaskNodeQuerySet(models.query.QuerySet):

    def multi_create(self, ids, **kwargs):
        """
        批量创建
        """
        for host in HostModel.objects.filter(id__in=ids):
            _kwargs = copy.deepcopy(kwargs)
            # Todo：无需更新status，可直接获取host的status
            _kwargs["status"] = host.status
            node = self.create(**_kwargs)
            node.host.add(host)

    def multi_create_master(self, ids, **kwargs):
        kwargs["role"] = NodeRoleNameMaster
        return self.multi_create(ids, **kwargs)

    def multi_create_slave(self, ids, **kwargs):
        kwargs["role"] = NodeRoleNameWorker
        return self.multi_create(ids, **kwargs)


class TaskNodeModel(BaseModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="自定义id")
    name = models.CharField(max_length=255, blank=True, null=True)
    host = models.ManyToManyField(to=HostModel, db_constraint=False, blank=True)  # TODO: 同量子应用的，一对一
    # host = models.OneToOneField(to=HostModel, db_constraint=False, blank=True, on_delete=models.CASCADE)
    task_id = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    status_id = models.CharField(max_length=255, blank=True, null=True)
    pre_status = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    dirty = models.IntegerField(blank=True, null=True)
    env_group_ids = models.CharField(max_length=255, blank=True, null=True)

    objects = TaskNodeQuerySet.as_manager()

    def clean(self):
        """
        更新name
        """
        num_node = (
            self.__class__
            .objects
            .filter(task_id=self.task_id, role=self.role)
            .count()
        )
        self.name = "%s-%s-%s" % (self.task_id, self.role, num_node + 1)

    class Meta:
        db_table = 'qupot_runtime_task_node'


class LogModel(BaseModel, models.Model):
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="自定义id")
    task_id = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'qupot_runtime_log'


class NtpServerModel(BaseModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="自定义id")
    name = models.CharField(max_length=64, blank=True, null=True)
    address = models.CharField(max_length=256, blank=True, null=True)
    status = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        db_table = 'qupot_runtime_ntp_server'


class RuntimeAppModel(BaseModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="自定义id")
    name = models.CharField(unique=True, max_length=255)
    spec = models.JSONField(blank=True, null=True, verbose_name="quprouduct spec")

    class Meta:
        db_table = 'qupot_runtime_app'

    def playbooks(self, processing_unit: str = None):
        """
        playbooks: {
            "default": [],
            "GPU": [],
            "CPU": [],
        }
        """
        _playbooks = self.spec.get("playbooks", [])
        if _playbooks and isinstance(_playbooks, dict) and processing_unit:
            _playbooks = _playbooks.get(processing_unit, _playbooks.get("default", []))

        return _playbooks


# class CeleryTaskModel(BaseModel, models.Model):
#     task_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="自定义id")
#     host_ids = models.CharField(max_length=255, blank=True, null=True)
#     trigger = models.CharField(max_length=255, blank=True, null=True)
#     ansible_roles = models.CharField(max_length=255, blank=True, null=True)
#
#     class Meta:
#         db_table = 'qupot_runtime_celery_task'

class KoModel(BaseModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="自定义id")
    name = models.CharField(unique=True, max_length=255)
    url = models.CharField(unique=True, max_length=255)
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)

    # 重写 save ，加密密码
    def save(self, *args, **kwargs):
        _m = aesEncrypt(self.password)
        self.password = _m
        super(KoModel, self).save(*args, **kwargs)

    class Meta:
        db_table = 'qupot_runtime_ko'


# 仓库 对应 ko_system_registry
class TaskRegistryModel(BaseModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="自定义id")
    hostname = models.CharField(max_length=255, blank=True, null=True)
    protocol = models.CharField(max_length=255, blank=True, null=True)
    architecture = models.CharField(max_length=255, blank=True, null=True)
    registry_hosted_port = models.IntegerField(blank=True, null=True)
    nexus_user = models.CharField(max_length=255, blank=True, null=True)
    nexus_password = models.CharField(max_length=255, blank=True, null=True)
    registry_port = models.IntegerField(blank=True, null=True)
    repo_port = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'qupot_runtime_task_registry'


# 信号机制，监听 TaskSpecModel 的 pre_delete 信号，在删除 TaskSpecModel 前执行 delete_task_nodes 函数。
@receiver(models.signals.pre_delete, sender=TaskSpecModel)
def delete_task_nodes(sender, instance, **kwargs):
    master_host_ids = instance.master_host_ids or []
    slave_host_ids = instance.slave_host_ids or []
    host_ids = master_host_ids + slave_host_ids
    TaskNodeModel.objects.filter(host__id__in=host_ids).delete()

    TaskStatusConditionModel.objects.filter(task_id=instance.task_id).delete()

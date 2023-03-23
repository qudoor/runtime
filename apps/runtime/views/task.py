from celery.result import AsyncResult
from django.core.exceptions import FieldError
from django.db import transaction
from django.forms import model_to_dict
from rest_framework import mixins, status
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.common.constant.cluster import NodeRoleNameWorker, NodeRoleNameMaster
from apps.common.constant.credential import Password
from apps.common.constant.index import CREDENTIAL_ID
from apps.common.utils.aes import aesDecrypt
from apps.common.utils.logger import get_logger
from apps.common.utils.format_data import gen_response_data
from apps.ops.third_party import nexus
from apps.runtime.custom_celery_tasks import task_ping_host, task_tail_ansible_log
from apps.runtime.models import TaskModel
from apps.runtime.models import TaskRegistryModel
from apps.runtime.models import HostModel
from apps.runtime.models import CredentialModel
from apps.runtime.models import TaskStatusModel
from apps.runtime.models import TaskStatusConditionModel
from apps.runtime.models import TaskNodeModel
from apps.runtime.models import TaskSpecModel
from apps.runtime.models import RuntimeAppModel
from apps.runtime.models import TaskCondition

from apps.runtime.serializer import TaskSerializer
from apps.runtime.serializer import TaskSpecSerializer
from apps.runtime.serializer import TaskStatusConditionSerializer
from apps.runtime.serializer import TaskNodeSerializer
from apps.runtime.serializer import HostsSerializer
from apps.runtime.serializer import RuntimeAppModelSerializer

from ..utils import HooksCreated, HealthCheck, gen_host_data_for_ansible, get_arch
from ..helpers import RuntimeTaskHelper

logger = get_logger(__file__)


def get_credential_by_host(host):
    credential = CredentialModel.objects.get(id=host[CREDENTIAL_ID])
    del credential._state
    return credential.__dict__


def is_wrong_path(item):
    item_list = item.get("group", None).split("/")
    return len(item_list) != 4


def get_name_by_item(item):
    try:
        logger.info(f'get name: {item.get("group", None).split("/")}')
        _, name, version, arch = item.get("group", None).split("/")
        package_name = item.get("name", "").replace(item.get("group", "")[1:] + "/", "")
        # logger.info("name: ", name, " version: ", version, " arch: ", arch, "package_name: ", package_name)
        # return item.get("name").split(item["group"][1:] + "/")[1].split("-")[0]
        return name, version, arch, package_name
    except Exception as e:
        raise Exception(e)


def filter_arch(dependents_dict, arch_name):
    # 根据arch fileterd
    filtered_dict = {}
    for name, versions in dependents_dict.items():
        filtered_versions = []
        for version in versions:
            filtered_arch = []
            for arch in version["arch"]:
                if arch["name"] == arch_name:
                    filtered_arch.append(arch)
            if filtered_arch:
                filtered_versions.append({"version": version["version"], "arch": filtered_arch})
        if filtered_versions:
            filtered_dict[name] = filtered_versions
    return filtered_dict


def filter_app_by_quproduct(quproduct, nexus_dependents, arch):
    try:
        queryset = RuntimeAppModel.objects.get(name=quproduct)
        dependents_list = queryset.spec.get("dependents")
    except FieldError:
        raise FieldError("field spec error")
    res_filtered_nexus = {}
    # 筛选 model的dependents
    for i in dependents_list:
        if i in list(nexus_dependents.keys()):
            res_filtered_nexus[i] = nexus_dependents[i]
    arch_name = get_arch(arch, is_ansible=True)
    # 筛选架构
    res_filtered_arch = filter_arch(res_filtered_nexus, arch_name=arch_name)
    return res_filtered_arch


def add_role_in_list(res_list, nodes, role='master'):
    for node_item in list(nodes):
        node_item.role = role
        res_list.append(node_item)
    return res_list


class TaskModelViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       mixins.DestroyModelMixin,
                       # PartialUpdateModelMixin,
                       GenericViewSet):
    queryset = TaskModel.objects.all()
    serializer_class = TaskSerializer
    lookup_field = 'name'

    @action(methods=['get'], detail=False, url_path="status/(?P<name>[^/.]+)")
    def get_task_conditions_status(self, request, name):
        task = self.get_object()
        task_status = getattr(task, "status", None)
        if not task_status:
            raise serializers.ValidationError("task status not found")

        task_status_condition = (
            TaskStatusConditionModel
            .objects
            .filter(task_status_id=task_status.id)
            .order_by("updated_at")
        )
        cond_serializer = TaskStatusConditionSerializer(task_status_condition, many=True)

        # 初始化任务步骤状态列表
        task_status_data = model_to_dict(task_status)
        task_status_data['conditions'] = cond_serializer.data

        return Response(task_status_data)

    @transaction.atomic
    def perform_create(self, serializer):
        instance = serializer.save()

        # 更新task_spec中的version
        try:
            app = RuntimeAppModel.objects.get(name=instance.quproduct)
        except RuntimeAppModel.DoesNotExist:
            raise serializers.ValidationError({
                "quproduct": "QuProduct not found"
            })
        instance.spec.version = app.spec.get("version", None)
        instance.spec.save()

        # 开始创建任务
        logger.info(f"begin generate task chain for {instance}...")

        task_helper = RuntimeTaskHelper(instance)
        task_chain = task_helper.generate_task_chain()
        task_chain.apply_async()

        logger.info(f"creat task_chain success")

    @action(methods=['get'], detail=False, url_path="existence/(?P<name>[^/.]+)")
    def existence(self, request, name):
        res = self.queryset.filter(name=name)
        res_data = {}
        if res:
            res_data['isExist'] = True
        else:
            res_data['isExist'] = False
        return Response(res_data)

    @action(methods=['post'], detail=False)
    def search(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset.order_by('created_at'))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False, url_path="nodes/(?P<name>[^/.]+)")
    def get_nodes(self, request, name):
        try:
            # TODO: page
            task_model = TaskModel.objects.get(name=name)
            task_spec = task_model.spec
            logger.info(f'task_spec : {task_spec}')

            res_list = []
            master_nodes = HostModel.objects.filter(id__in=task_spec.master_host_ids)
            slave_nodes = HostModel.objects.filter(id__in=task_spec.slave_host_ids)
            add_role_in_list(res_list=res_list, nodes=master_nodes, role='master')
            add_role_in_list(res_list=res_list, nodes=slave_nodes, role='slave')

            serializer = HostsSerializer(res_list, many=True)
            return Response(gen_response_data(success=True, msg='', data=serializer.data))
        except Exception as e:
            logger.error("get_nodes error: {}".format(e))
            return Response(gen_response_data(success=False, msg=str(e)))

    @action(methods=['get'], detail=False, url_path="dependents/(?P<arch>[^/.]+)/(?P<quproduct>[^/.]+)")
    def get_dependents_by_quproduct(self, request, arch, quproduct):
        nexus_dependents = []
        queryset = TaskRegistryModel.objects.filter(architecture=get_arch(arch))
        registry_list = list(queryset.values())
        if len(registry_list) > 0:
            for registry in registry_list:
                # 获取nexus上依赖
                nexus_dependents = nexus.get_quproduct_list(registry)
        if len(nexus_dependents) == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST, data="请在系统设置中完善对应仓库信息")
        res = filter_app_by_quproduct(quproduct, nexus_dependents, arch)
        return Response(status=status.HTTP_200_OK, data=res)

    @action(methods=['get'], detail=False, url_path="quproduct/all")
    def get_quproduct(self, request):
        # 获取所有产品信息
        queryset = RuntimeAppModel.objects.all()
        serializer = RuntimeAppModelSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False, url_path="node/(?P<task_name>[^/.]+)")
    def get_node(self, request, task_name):
        task = TaskModel.objects.get(name=task_name)
        res = TaskNodeModel.objects.filter(task_id=task.id)
        total = len(res)

        page = self.paginate_queryset(res)
        if page is not None:
            serializer = TaskNodeSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TaskNodeSerializer(res, many=True)
        # 统一分页格式
        return Response({
            'items': serializer.data,
            'total': total
        })

    @transaction.atomic
    @action(methods=['post'], detail=False, url_path="node/batch/(?P<task_name>[^/.]+)")
    def nodes_batch(self, request, task_name):
        # TODO: 是否需要删除需要根据量子应用业务确定？
        # 删除多个节点
        # 1. 删除节点表中的记录
        # 2. 删除 host 中的 task_id
        # 3. update table task_spec worker or master ids 数组
        # TODO: 4. playbook 删除主机目录
        nodes = request.data.get('nodes')
        logger.info("request.nodes: {}".format(nodes))

        host_ids = []
        for node_name in nodes:
            node = TaskNodeModel.objects.get(name=node_name)
            host_ids.append(node.host_id)
            task = TaskModel.objects.get(id=node.task_id)
            task_spec = TaskSpecModel.objects.get(id=task.spec_id)
            if node.role == NodeRoleNameMaster:
                return Response(status=status.HTTP_400_BAD_REQUEST, data="主节点禁止删除")
            elif node.role == NodeRoleNameWorker:
                slave_host_ids = task_spec.slave_host_ids
                slave_host_ids.remove(str(node.host_id))
                task_spec.slave_host_ids = slave_host_ids
                serializer = TaskSpecSerializer(task_spec, data=task_spec.__dict__, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()

        return Response(status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path="health/(?P<cluster_name>[^/.]+)")
    def health_check(self, request, cluster_name):
        # TODO:
        #  1. checkHostSSHConnected: 多个节点，每个节点一个协程，等待所有协程都结束后，返回结果(协程非阻塞同步)
        #      a. ip ping
        #      b. ssh client ping
        #      c. ssh client connect
        #  2. 检测节点是否同步
        # 通过 cluster_name 查找主从节点，迭代各个节点
        task = TaskModel.objects.prefetch_related('spec').get(name=cluster_name)
        task_host_list = HostModel.objects.filter(id__in=(task.spec.master_host_ids + task.spec.slave_host_ids))

        host_list = []
        for host in task_host_list:
            del host._state
            host = host.__dict__
            credential = get_credential_by_host(host)
            host['user'] = credential['username']
            host['password'] = aesDecrypt(credential[Password])
            host['private_key'] = credential['private_key']
            host['groups'] = ['all']
            host['credential'] = credential
            host_list.append(host)

        host_data = gen_host_data_for_ansible(host_list)

        task_id = task_ping_host.delay(host_data)
        res = AsyncResult(str(task_id)).get()
        hook = HooksCreated(res).msg

        data = HealthCheck([hook]).health_check_response
        logger.info(f'host_data: {host_data}, cluster_name: {cluster_name} task_id: {task_id} res: {res}')
        return Response(status=status.HTTP_200_OK, data=data)

    @action(methods=['get'], detail=False, url_path="logger/(?P<task_name>[^/.]+)")
    def get_logger_api(self, request, task_name):
        try:
            task_id = task_tail_ansible_log.delay(task_name)
            res = AsyncResult(str(task_id)).get()
            return Response(status=status.HTTP_200_OK, data=res)
        except Exception as e:
            logger.error("get_logger error: {}".format(e))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['post'], detail=False, url_path="upgrade/(?P<task_name>[^/.]+)")
    def upgrade(self, request, task_name):
        # TODO: upgrade
        return Response(status=status.HTTP_404_NOT_FOUND, data='comming soon')

    @action(methods=['POST'], detail=True)
    def retry(self, request, *args, **kwargs):
        """
        重试任务
        """
        task = self.get_object()
        # 验证version
        try:
            app = RuntimeAppModel.objects.get(name=task.quproduct)
        except RuntimeAppModel.DoesNotExist:
            raise serializers.ValidationError({
                "quproduct": "QuProduct not found"
            })
        if app.spec.get("version") != task.spec.version:
            raise serializers.ValidationError({
                "version": "QuProduct version not match"
            })

        cond_qs = TaskStatusConditionModel.objects.filter(task_id=task.id).order_by("order_num")
        if not cond_qs:
            raise serializers.ValidationError({
                "task": "Task not found"
            })

        failed_qs = cond_qs.filter(status=TaskCondition.FAILED.value)
        if not failed_qs.exists():
            raise serializers.ValidationError({
                "task": "Task not failed or running now."
            })

        retry_playbooks = [
            cond.name for cond in cond_qs[failed_qs.first().order_num:]
        ]
        logger.info(f"retry_playbooks: {retry_playbooks}")
        task_helper = RuntimeTaskHelper(task, retry_playbooks)
        task_chain = task_helper.generate_task_chain()
        task_chain.apply_async()
        return Response()

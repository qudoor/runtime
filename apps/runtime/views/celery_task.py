import numbers

from django.conf import settings
from rest_framework import status
# Create your views here.
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework import fields
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse, OpenApiTypes

from apps.common.constant.index import GetQutrunkPodStatus, BACKEND, DEFAULT_BACKEND, \
    DeployQutrunkEnv, DeleteQutrunkEnv, ViewLog
from apps.common.utils.common import is_number, convert_cpu_unit_to_m, convert_memory_unit_to_Mi, get_k8s_config_file
from apps.common.utils.format_data import gen_response_data
from apps.common.utils.logger import get_logger
from apps.ops.kubernetes.apis import is_enough_resource, create_namespace_if_not_exists
from apps.runtime.custom_celery_tasks import task_run_playbook_without_db

logger = get_logger(__name__)

DEFAULT_PYTHON_VERSION = '3.9'


def gen_query_or_log_host_data(quantum_app_env_id, cluster_name, namespace, task_name):
    return {
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
        "vars": {
            "kubeconfig_file": get_k8s_config_file(cluster_name),
            "kubernetes_qutrunk_namespace": namespace,
            "qutrunk_id": quantum_app_env_id,
            "helm_binary_path": settings.HELM_BINARY_PATH,
            "task_name": task_name
        }
    }


def query_and_log_common(request=None, playbook_filename=None, task_name=None):
    try:
        cluster_name = request.data['cluster_name']
        quantum_app_env_id = request.data['quantum_app_env_id']

        _host_data = gen_query_or_log_host_data(quantum_app_env_id=quantum_app_env_id,
                                                cluster_name=cluster_name,
                                                namespace=settings.APPSTORE_NAMESPACE, task_name=task_name)
        task_id_async_result = task_run_playbook_without_db.delay(host_data=_host_data,
                                                                  playbook=playbook_filename)
        logger.info(f"task_run_playbook_without_db task_id: {task_id_async_result}")
        return Response(gen_response_data(success=True, msg='', data={'task_id': str(task_id_async_result)}), )
    except Exception as e:
        return Response(status=status.HTTP_400_BAD_REQUEST, data=gen_response_data(data=str(e)))


def gen_deploy_host_data(cluster_name=None, quantum_app_env_id=None, cpu_require=None, memory_require=None,
                         qutrunk_architecture=None, namespace=None, download_url=None, qutrunk_filename=None,
                         python_version=DEFAULT_PYTHON_VERSION, task_name=None, backend=None):
    if isinstance(cpu_require, numbers.Number) or is_number(cpu_require):
        cpu_require = str(convert_cpu_unit_to_m(cpu_require)) + 'm'

    if isinstance(memory_require, numbers.Number) or is_number(memory_require):
        memory_require = str(convert_memory_unit_to_Mi(memory_require)) + 'Mi'

    return {
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
        "vars": {
            "helm_qudoor_chart_url": "http://x.x.x.202:8081/repository/chart",
            "helm_repo_name": "qudoor",
            "helm_binary_path": settings.HELM_BINARY_PATH,
            "kubeconfig_file": get_k8s_config_file(cluster_name),
            "kubernetes_qutrunk_namespace": namespace,
            "qutrunk_id": quantum_app_env_id,
            "qutrunk_cpu": cpu_require,
            "qutrunk_memory": memory_require,
            "qutrunk_architecture": qutrunk_architecture,
            "qutrunk_filename": qutrunk_filename,
            "qutrunk_url": download_url,
            "qutrunk_jobtimeout": "86400",
            "qutrunk_retrycount": "4",
            "python_version": python_version,
            "task_name": task_name,
            "BACKEND_TYPE": backend.get(BACKEND['BACKEND_TYPE'], None),
            "AWS_ACCESS_KEY_ID": backend.get(BACKEND['AWS_ACCESS_KEY_ID'], None),
            "AWS_SECRET_ACCESS_KEY": backend.get(BACKEND['AWS_SECRET_ACCESS_KEY'], None),
            "AWS_DEFAULT_REGION": backend.get(BACKEND['AWS_DEFAULT_REGION'], None),
        }
    }


class CeleryTaskViewSet(GenericViewSet):
    @extend_schema(summary='创建量子APP环境')
    @extend_schema(request={
        "application/json": inline_serializer("createEnvTaskSerializer", {
            "quantum_app_env_id": fields.CharField(required=True, help_text="量子应用 id"),
            "cluster_name": fields.CharField(required=True, help_text="集群名称"),
            "cpu_require": fields.IntegerField(required=True, help_text="cpu 值，单位为核，注意最低核数和最大核数。"),
            "memory_require": fields.IntegerField(required=True,
                                                  help_text="内存要求值，单位为 Mi，注意最低内存（足以运行一个pod）和最高内存"),
            "app_file_url": fields.CharField(required=True, help_text="量子应用下载链接"),
            "arch": fields.ChoiceField(['arm64', 'amd64'], required=True),
            "python_version": fields.CharField(help_text="Python 版本"),
            "backend": fields.CharField(
                help_text="QuTrunk backend: BACKEND_TYPE、AWS_ACCESS_KEY_ID、AWS_SECRET_ACCESS_KEY"),
        })
    })
    @action(methods=['post'], detail=False, url_path="create_env_task")
    def create_env_task(self, request):
        """
        如果资源足够，通过拉起 k8s 资源，创建量子 APP 运行环境
        """
        try:
            cpu_require = request.data['cpu_require']
            memory_require = request.data['memory_require']
            arch = request.data['arch']
            cluster_name = request.data['cluster_name']
            quantum_app_env_id = request.data['quantum_app_env_id']
            python_version = request.data.get('python_version', DEFAULT_PYTHON_VERSION)
            backend = request.data.get('backend', DEFAULT_BACKEND)
            logger.info(f'backend: {backend}')

            #  通过 app_file_url(定义下载链接名称规则) 获取文件，文件名，
            app_file_url = request.data['app_file_url']
            qutrunk_filename = app_file_url.split("/")[-1]
            url_without_filename = app_file_url.replace("/" + app_file_url.split("/")[-1], '')

            if is_enough_resource(cpu_require=cpu_require, memory_require=memory_require,
                                  arch=arch, cluster_name=cluster_name):

                create_namespace_if_not_exists(namespace_name=settings.APPSTORE_NAMESPACE)

                # 调用 ansible 拉起资源，创建量子应用环境
                _host_data = gen_deploy_host_data(cluster_name=cluster_name, quantum_app_env_id=quantum_app_env_id,
                                                  cpu_require=cpu_require, memory_require=memory_require,
                                                  qutrunk_architecture=arch, namespace=settings.APPSTORE_NAMESPACE,
                                                  download_url=url_without_filename,
                                                  qutrunk_filename=qutrunk_filename, python_version=python_version,
                                                  backend=backend, task_name=DeployQutrunkEnv)
                deploy_playbook_filename = "21-qutrunk-deploy.yml"

                task_id_async_result = task_run_playbook_without_db.delay(host_data=_host_data,
                                                                          playbook=deploy_playbook_filename)
                logger.info("task_run_playbook_without_db task_id: ", task_id_async_result)
                res = dict()
                res['task_id'] = str(task_id_async_result)
                return Response(gen_response_data(success=True, data=res))
            else:
                return Response(gen_response_data(success=False, msg='资源不足'))
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=gen_response_data(success=False, msg=str(e)))

    # @swagger_auto_schema(method='post',
    #                      operation_summary='测试集群连通性，并返回集群列表',
    #                      operation_description='通过账号、密码、KO 链接测试集群的连通性，并返回集群列表',
    #                      request_body=openapi.Schema(
    #                          type=openapi.TYPE_OBJECT,
    #                          required=['username', 'password', 'ko_url'],
    #                          properties={
    #                              'username': openapi.Schema(
    #                                  type=openapi.TYPE_STRING,
    #                                  description='username',
    #                              ),
    #                              'password': openapi.Schema(
    #                                  type=openapi.TYPE_STRING,
    #                                  description='password',
    #                              ),
    #                              'ko_url': openapi.Schema(
    #                                  type=openapi.TYPE_STRING,
    #                                  description='KO 链接',
    #                              ),
    #                          }
    #                      ))
    # @action(methods=['post'], detail=False, url_path="test_cluster_connectivity")
    # def test_cluster_connectivity(self, request, *args, **kwargs):
    #     print("request: ", request)
    #     print("request data: ", request.data)
    #     # 1. 通过 username/password 登录，再根据集群名，调用 ko 下载所有集群的 KubeConfig 文件
    #     # request by username/password then download
    #     try:
    #         ko_url = request.data['ko_url']
    #         username = request.data['username']
    #         password = request.data['password']
    #         verify_res = verify_ko(username=username, pwd=password, ko_url=ko_url)
    #         if verify_res.status_code == status.HTTP_200_OK:
    #             download_all_cluster_config(ko_url, verify_res.cookies)
    #             cluster_list = get_cluster_list_by_ko_url(ko_url, verify_res.cookies)
    #             cluster_list = filter_running_cluster_list(cluster_list)
    #
    #             return Response(
    #                 gen_response_data(success=True, msg="KO 系统验证通过", data={'clusterList': cluster_list}))
    #         else:
    #             res_content = json.loads(verify_res.content.decode('utf-8'))
    #             if res_content.get("msg", None):
    #                 res_data = gen_response_data(msg=res_content.get("msg"), data=None)
    #             else:
    #                 res_data = gen_response_data(data=res_content)
    #
    #             return Response(status=verify_res.status_code, data=res_data)
    #     except Exception as e:
    #         return Response(status=status.HTTP_400_BAD_REQUEST, data=gen_response_data(msg=str(e)))

    @extend_schema(summary="创建查询(query)异步任务")
    @extend_schema(request=inline_serializer("CreateQueryTaskSerializer", {
        "quantum_app_env_id": fields.CharField(help_text="量子应用 id"),
        "cluster_name": fields.CharField(help_text="集群名称"),
    }))
    @action(methods=['post'], detail=False, url_path="create_query_task")
    def create_query_task(self, request, *args, **kwargs):
        """
        查询容器状态
        """
        return query_and_log_common(request, "22-qutrunk-query.yml", GetQutrunkPodStatus)

    @extend_schema(summary="创建查询日志（log）异步任务")
    @extend_schema(request=inline_serializer("CreateQueryTaskSerializer", {
        "quantum_app_env_id": fields.CharField(help_text="量子应用 id"),
        "cluster_name": fields.CharField(help_text="集群名称"),
    }))
    @action(methods=['post'], detail=False, url_path="create_log_task")
    def create_log_task(self, request):
        return query_and_log_common(request, "24-qutrunk-log.yml", task_name=ViewLog)

    # @swagger_auto_schema(method='post',
    #                      operation_summary='通过异步 id，查询异步任务结果',
    #                      operation_description='',
    #                      request_body=openapi.Schema(
    #                          type=openapi.TYPE_OBJECT,
    #                          required=['task_id', 'task_type'],
    #                          properties={
    #                              'task_id': openapi.Schema(
    #                                  type=openapi.TYPE_STRING,
    #                              ),
    #                              'task_type': openapi.Schema(
    #                                  type=openapi.TYPE_STRING,
    #                                  enum=['log', 'create', 'query'],
    #                                  description="描述任务类型"
    #                              )
    #                          }
    #                      ),
    #                      responses={200: 'query taskId 中对应状态有： 1. Active 创建中 2. Retry 重试中 3. Success 成功  4. Failed 失败'})
    #
    # @action(methods=['post'], detail=False, url_path="get_result_by_task_id")
    # def get_result_by_task_id(self, request, *args, **kwargs):
    #     try:
    #         # TODO: 不存在 task_id 如何处理，目前是超时
    #         res = AsyncResult(str(request.data['task_id'])).get(timeout=SHORT_TIMEOUT)
    #         if res is not None:
    #             raw, summary = res
    #             res = get_result_from_ansible_data(raw, summary, request.data['task_type'])
    #             return Response(status=status.HTTP_200_OK, data=res)
    #         else:
    #             return Response(status=status.HTTP_400_BAD_REQUEST, data=gen_response_data(msg="此任务已失效或不存在"))
    #     except TimeoutError as e:
    #         res_data = gen_response_detail(detail=str(e), error_type=ErrorTypeTimeout)
    #         return Response(status=status.HTTP_400_BAD_REQUEST,
    #                         data=gen_response_data(success=True, msg=str(e), data=res_data))
    #     except Exception as e:
    #         return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=gen_response_data(msg=str(e)))
    #

    @extend_schema(summary="删除量子应用环境")
    @extend_schema(request=inline_serializer("CreateQueryTaskSerializer", {
        "quantum_app_env_id": fields.CharField(help_text="量子应用 id"),
        "cluster_name": fields.CharField(help_text="集群名称"),
    }))
    @action(methods=['post'], detail=False, url_path="create_delete_env_task")
    def create_delete_env_task(self, request):
        try:
            return query_and_log_common(request, "23-qutrunk-delete.yml", DeleteQutrunkEnv)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=gen_response_data(msg=str(e)))

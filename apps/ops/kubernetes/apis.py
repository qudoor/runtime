import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QuPot.settings')
import django

django.setup()

from kubernetes import client, config
from kubernetes.client import CustomObjectsApi, OpenApiException
# Configs can be set in Configuration class directly or using helper utility
from kubernetes.config import ConfigException

from apps.common.constant.cluster import ClusterRunning
from apps.common.exceptions import ConfigNotFoundException, K8SException
from apps.common.utils.common import convert_cpu_unit_to_m, convert_memory_unit_to_Mi, get_k8s_config_file
from apps.common.utils.logger import get_logger
from apps.ops.third_party.nexus import get_chart_list

logger = get_logger(__file__)


def is_enough_resource(cpu_require, memory_require, arch, cluster_name):
    cpu_require = convert_cpu_unit_to_m(cpu_require)
    memory_require = convert_memory_unit_to_Mi(memory_require)
    node_list = get_node_resource_list(arch=arch, cluster_name=cluster_name)
    # 判断是否存在一个节点资源足够
    logger.info(f'cpu_require: {cpu_require}, memory_require: {memory_require}, node_list: {node_list}')
    for node in node_list:
        if node['cpu_receive'] > cpu_require and node['memory_receive'] > memory_require:
            return True
    return False


# 获取各个节点资源使用情况：总资源 和 剩余资源
def get_node_resource_list(arch=None, cluster_name=None):
    # config.load_kube_config(config_file=K8S_CONFIG + "/" + cluster_name)
    config.load_kube_config(config_file=get_k8s_config_file(cluster_name))
    v1 = client.CoreV1Api()
    logger.info("Listing pods with their IPs:")
    # ret = v1.read_node(name="oneqloud-master-1")
    res = []
    # items = []
    # if arch == 'all':
    #     ret = v1.list_node(label_selector="beta.kubernetes.io/arch=arm64")  # by arm64 /amd64
    #     items.extend(ret.items)
    #     ret = v1.list_node(label_selector="beta.kubernetes.io/arch=amd64")  # by arm64 /amd64
    #     items.extend(ret.items)
    # else:
    #     ret = v1.list_node(label_selector="beta.kubernetes.io/arch="+arch) # by arm64 /amd64
    #     items = ret.items

    ret = v1.list_node(label_selector="beta.kubernetes.io/arch=" + arch)  # by arm64 /amd64
    items = ret.items
    # ret = v1.list_node()
    for i in items:
        logger.info(f"i.metadata.labels['beta.kubernetes.io/arch']: {i.metadata.labels['beta.kubernetes.io/arch']}")
        # 1(核) = 1000m(毫核) = 1000 000n = 1000 000 000u
        # 1 微米 (μm) = 1000 纳米

        cust = CustomObjectsApi()
        nodes_obj = cust.list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'nodes')  # All node metrics
        nodes = nodes_obj.get('items')
        for node in nodes:
            node_name = node.get('metadata').get('name')
            if node_name == i.metadata.name:
                cpu_total = convert_cpu_unit_to_m(i.status.allocatable['cpu'])
                memory_total = convert_memory_unit_to_Mi(i.status.allocatable['memory'])
                logger.info(f"+++++++++ 总 cpu: {cpu_total}, +++++++++ 总 cpu: {memory_total}")
                cpu_usage = convert_cpu_unit_to_m(node.get('usage').get('cpu'))
                memory_usage = convert_memory_unit_to_Mi(node.get('usage').get('memory'))
                logger.info(f"node name: : {node_name} \n, usage cpu:: {cpu_usage}, \n usage memory:: {memory_usage}")

                temp_node = dict()
                temp_node['name'] = node_name
                temp_node['cpu_usage'] = cpu_usage
                temp_node['memory_usage'] = memory_usage
                temp_node['cpu_total'] = cpu_total
                temp_node['memory_total'] = memory_total
                temp_node['cpu_receive'] = round(float(cpu_total) - cpu_usage, 2)
                temp_node['memory_receive'] = round(float(memory_total) - memory_usage, 2)
                logger.info(f"temp_node : {temp_node} \n, res: {res}")
                res.append(temp_node)

    # v1beta1 = client.BatchV1beta1Api()

    logger.info(f"get_node_resource_list res: {res}")
    return res


# 获取应用商店应用的状态
def get_app_info_by_k8s(chart_url, cluster_name, namespace):
    app_status_list = []
    try:
        config.load_kube_config(config_file=get_k8s_config_file(cluster_name))
        v1 = client.CoreV1Api()
        chart_list = get_chart_list(chart_url)
        app_name_list = []
        for i in chart_list:
            app_name_list.append(i["name"])
        # 获取app应用列表
        for i in app_name_list:
            app_status = dict({'nodePort': '', 'qudomain': '', 'serverPort': ''})
            ret = v1.list_namespaced_pod(namespace=namespace, label_selector="app.kubernetes.io/instance={}".format(i))
            service_list = v1.list_namespaced_service(namespace=namespace,
                                                      label_selector="app.kubernetes.io/instance={}".format(i))
            if len(service_list.items) > 0:
                app_status['nodePort'] = service_list.items[0].spec.ports[0].node_port
                app_status['qudomain'] = service_list.items[0].metadata.labels['qudomain']
                app_status['serverPort'] = service_list.items[0].metadata.labels['serverPort']
                app_status['type'] = service_list.items[0].spec.type
            app_status['name'] = i
            # 判断同一chart内容器都是running，才是running，否则
            for r in ret.items:
                if r.status.phase != ClusterRunning:
                    app_status['status'] = r.status.phase
                    break
                else:
                    app_status['status'] = r.status.phase
            if app_status.get('status'):
                app_status_list.append(app_status)
    except ConfigException as e:
        logger.error("找不到配置文件，请检查集群是否存在:", e)
        raise ConfigNotFoundException()
    except OpenApiException as e:
        logger.error("k8s 错误:", e)
        raise K8SException()

    return app_status_list


def create_namespace_if_not_exists(namespace_name, cluster_name):
    # 读取 kubeconfig 文件
    # config.load_kube_config()
    config.load_kube_config(config_file=get_k8s_config_file(cluster_name))

    # 创建一个 Namespace 对象
    namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace_name))

    # 创建一个 Namespace API 客户端
    namespace_api = client.CoreV1Api()

    # 检查 Namespace 是否存在
    try:
        namespace_api.read_namespace(namespace.metadata.name)
        logger.info("Namespace already exists.")
    except client.exceptions.ApiException as e:
        if e.status == 404:
            # 如果返回 404 错误，则表示 Namespace 不存在，创建它
            namespace_api.create_namespace(namespace)
            logger.info(f"{namespace} Namespace created.")
        else:
            # 其他错误，抛出异常
            raise e


if __name__ == '__main__':
    # get_node_resource_list()
    # print("is_enough_resource:", is_enough_resource(cpu_require=3800, memory_require=5000, arch='amd64', cluster_name='test-oneqcloud'))
    create_namespace_if_not_exists('qudoor-test', 'test-oneqcloud')

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.common.constant.cluster import ClusterInitializing
from apps.common.utils.common import is_has_key, is_ip

from .models import CredentialModel
from .models import HostModel
from .models import TaskModel
from .models import TaskSpecModel
from .models import TaskRegistryModel
from .models import TaskStatusModel
from .models import TaskStatusConditionModel
from .models import TaskNodeModel
from .models import KoModel
from .models import RuntimeAppModel


class HostsSerializer(serializers.ModelSerializer):
    # ip 不是ko的ip

    # 如果密钥不为空，定义password = 对应的密码，否则密钥=密钥

    port = serializers.CharField(required=True)
    role = serializers.CharField(required=False)

    def validate(self, host):
        # if host['ip']:
        #     print('validators ip: ', host['ip'])
        if is_has_key(host, 'ip') and not is_ip(host['ip']):
            raise serializers.ValidationError("ip 格式不正确")
        return host

    class Meta:
        model = HostModel
        fields = '__all__'


class CredentialModelSerializer(serializers.ModelSerializer):
    type = serializers.CharField(required=True)
    name = serializers.CharField(required=True, validators=[
        UniqueValidator(queryset=CredentialModel.objects.all(), message="凭据名字已存在，请修改!")])
    username = serializers.CharField(required=True)

    class Meta:
        model = CredentialModel
        # exclude = ('password', 'private_key')
        fields = '__all__'


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatusModel
        fields = '__all__'


class TaskNodeSerializer(serializers.ModelSerializer):
    # host = HostsSerializer(many=False, read_only=True, required=False)
    # host_id = serializers.CharField(required=True)
    host = serializers.PrimaryKeyRelatedField(many=True, queryset=HostModel.objects.all())
    task_id = serializers.CharField(required=True)
    role = serializers.CharField(required=False)
    pre_status = serializers.CharField(required=False)

    class Meta:
        model = TaskNodeModel
        fields = '__all__'


class TaskSpecSerializer(serializers.ModelSerializer):
    version = serializers.CharField(allow_null=True, allow_blank=True)
    architectures = serializers.CharField(required=False)
    # registry_id = serializers.IntegerField(required=True)  # 仓库 跟ko不同，ko 是写死仓库域名
    max_node_num = serializers.IntegerField(required=False, allow_null=True)

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #
    #     if data['master_host_ids']:
    #         data['master_host_ids'] = json.loads(data['master_host_ids'])
    #     if data['slave_host_ids']:
    #         data['slave_host_ids'] = json.loads(data['slave_host_ids'])
    #     return data

    class Meta:
        model = TaskSpecModel
        fields = '__all__'
        # extra_kwargs = {
        #     'url': {'lookup_field': 'id'},
        # }


class TaskSerializer(serializers.ModelSerializer):
    spec = TaskSpecSerializer(read_only=False)
    status = TaskStatusSerializer(read_only=True)
    nodes = serializers.ListField(required=False)

    class Meta:
        model = TaskModel
        fields = '__all__'

    # 创建一个被嵌套的实例: https://hkvision.cn/2019/08/04/django-restframework-%E5%B5%8C%E5%A5%97%E5%BA%8F%E5%88%97%E5%8C%96/
    def create(self, validated_data):
        spec_data = validated_data.pop("spec", None)
        nodes = validated_data.pop("nodes", None)  # TODO:
        instance = super().create(validated_data)

        status = TaskStatusModel.objects.create(task=instance)

        if spec_data:
            spec_data['task'] = instance.id
            spec_ser = TaskSpecSerializer(data=spec_data)
            spec_ser.is_valid(raise_exception=True)
            spec = spec_ser.save()
            # 创建主从节点
            TaskNodeModel.objects.multi_create_master(
                spec.master_host_ids,
                task_id=instance.id,
            )
            TaskNodeModel.objects.multi_create_slave(
                spec.slave_host_ids,
                task_id=instance.id,
            )
            # 创建子任务状态
            for index, playbook in enumerate(instance.get_playbook_list()):
                TaskStatusConditionModel.objects.create(
                    task_id=instance.id,
                    task_status_id=status.id,
                    name=playbook,
                    order_num=index,
                    last_probe_time=timezone.now()
                )

        return instance


class TaskRegistrySerializer(serializers.ModelSerializer):
    hostname = serializers.CharField(required=True)
    protocol = serializers.CharField(required=True)
    architecture = serializers.CharField(required=True)
    registry_hosted_port = serializers.IntegerField(required=True)
    nexus_user = serializers.CharField(required=True)
    nexus_password = serializers.CharField(required=True)
    registry_port = serializers.IntegerField(required=True)
    repo_port = serializers.IntegerField(required=True)

    def validate(self, registry):
        if self.instance:
            return registry
        query_set = TaskRegistryModel.objects.filter(architecture=registry['architecture'])
        if len(query_set) > 0:
            raise serializers.ValidationError("该架构类型的仓库已经存在")
        return registry

    class Meta:
        model = TaskRegistryModel
        fields = '__all__'


class TaskStatusConditionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    task_status_id = serializers.CharField(required=True)
    status = serializers.CharField(required=True)
    message = serializers.CharField(required=True)
    order_num = serializers.IntegerField(required=True)
    last_probe_time = serializers.DateTimeField(required=False)

    class Meta:
        model = TaskStatusConditionModel
        fields = '__all__'


class KoSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    url = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def create(self, validated_data):
        # 新增校验
        query_set_by_name = KoModel.objects.filter(name=validated_data['name'])
        if len(query_set_by_name) > 0:
            raise serializers.ValidationError(f"名字为 {validated_data['name']}  已存在")

        query_set = KoModel.objects.filter(url=validated_data['url'])
        if len(query_set) > 0:
            raise serializers.ValidationError(f"仓库为 {validated_data['url']}  已存在")

        return super().create(validated_data)

    class Meta:
        model = KoModel
        fields = '__all__'


class RuntimeAppModelSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    spec = serializers.JSONField()

    class Meta:
        model = RuntimeAppModel
        fields = '__all__'

"""
基于 ansible v2.8.5 的 api，低于 v2.8 不适用
"""
from ansible.parsing.dataloader import DataLoader  # 解析 json/ymal/ini 格式的文件
from ansible.vars.manager import VariableManager  # 管理主机和主机组的变量
from ansible.inventory.manager import InventoryManager  # 管理资产文件（动态资产、静态资产）或者主机列表
from ansible.inventory.host import Host  # 单台主机类
from ansible.utils.vars import combine_vars
from django.conf import settings


class BaseHost(Host):
    """
    处理单个主机
    """

    def __init__(self, host_data):
        self.host_data = host_data
        hostname = host_data.get('name') or host_data.get('ip')
        port = host_data.get('port') or 22
        super().__init__(hostname, port)
        self.__set_required_variables()
        self.__set_extra_variables()

    def __set_required_variables(self):
        host_data = self.host_data
        # ssh 连接参数，提升速度， 仅到连接插件为 ssh 时生效，paramiko 模式下不生效
        if settings.ANSIBLE_CONNECTION_TYPE == 'ssh':
            self.set_variable('ansible_ssh_args', '-C -o ControlMaster=auto -o ControlPersist=60s')
            self.set_variable('ansible_ssh_pipelining', True)
            self.set_variable('ansible_host_key_checking', False)

        if host_data['name']:
            self.set_variable('ansible_host', host_data['name'])
        if host_data.get('ip'):
            self.set_variable('ansible_ssh_host', host_data['ip'])
        if host_data.get('port'):
            self.set_variable('ansible_port', host_data['port'])
        else:
            self.set_variable('ansible_port', 22)
        if host_data.get('user'):
            self.set_variable('ansible_user', host_data['user'])

        # 添加密码和秘钥
        if host_data.get('password'):
            self.set_variable('ansible_ssh_pass', host_data['password'])

        if host_data.get('private_key'):
            # if not os.path.exists(TMP_DIR):
            #     os.makedirs(TMP_DIR)
            file_name = settings.TMP_DIR + "/id_rsa_" + host_data['name']
            f = open(file_name, "w")
            f.write(host_data['private_key'])
            f.close()
            self.set_variable('ansible_ssh_private_key_file', file_name)

        # 添加host vars 变量
        if host_data.get('vars'):
            for k, v in self.host_data.get('vars', {}).items():
                self.set_variable(k, v)

    def get_vars(self):
        return combine_vars(self.vars, self.get_magic_vars())

    def __set_extra_variables(self):
        for k, v in self.host_data.get('vars', {}).items():
            self.set_variable(k, v)

    def __repr__(self):
        return self.name


class BaseInventory(InventoryManager):
    """
    生成 Ansible inventory 对象
    """
    loader_class = DataLoader
    variable_manager_class = VariableManager
    host_manager_class = BaseHost

    def __init__(self, inventory_data=None):
        if inventory_data is None:
            self.host_list = []
        self.host_list = inventory_data["hosts"]
        self.group_list = inventory_data["groups"]
        self.var_list = inventory_data["vars"]
        assert isinstance(self.host_list, list)
        self.loader = self.loader_class()
        self.variable_manager = self.variable_manager_class()
        super().__init__(self.loader)

    def get_groups(self):
        return self._inventory.groups

    def get_group(self, name):
        return self._inventory.groups.get(name, None)

    def get_or_create_group(self, name):
        group = self.get_group(name)
        if not group:
            self.add_group(name)
            return self.get_or_create_group(name)
        else:
            return group

    def parse_groups(self):
        # 循环gourp，定义组
        # [{'name': 'kube-master', 'hosts': ['test-211-212-01-master-1']},
        #  {'name': 'kube-worker', 'hosts': ['test-211-212-01-worker-1'], 'children': ['kube-master']},
        #  {'name': 'new-worker'}, {'name': 'ex_lb'},
        #  {'name': 'etcd', 'hosts': ['test-211-212-01-master-1'], 'children': ['kube-master']},
        #  {'name': 'chrony', 'hosts': ['test-211-212-01-master-1']}, {'name': 'del-worker'}]
        if self.group_list:
            for g in self.group_list:
                parent = self.get_or_create_group(g.get("name"))
                children = [self.get_or_create_group(n) for n in g.get('children', [])]
                for child in children:
                    parent.add_child_group(child)

    def parse_hosts(self, cache=False):
        # 循环主机列表
        # {'ip': 'x.x.x.212', 'name': 'test-211-212-01-worker-1', 'port': 22, 'user': 'root',
        #  'password': '1qa2ws#ED', 'vars': {'architectures': 'amd64', 'has_gpu': 'false', 'registry_hosted_port': '8083',
        #                                    'registry_hostname': 'x.x.x.202', 'registry_port': '8082',
        #                                    'registry_protocol': 'http', 'repo_port': '8081'}}
        group_all = self.get_group('all')
        ungrouped = self.get_group('ungrouped')
        for host_data in self.host_list:
            # 定义单台主机host
            host = self.host_manager_class(host_data=host_data)
            # inventory的host类增加主机
            self.hosts[host_data['name']] = host

            if self.group_list:
                for group_name in self.group_list:
                    if group_name.get("hosts"):
                        for h in group_name.get("hosts"):
                            if host_data.get('name') == h:
                                group = self.get_or_create_group(group_name['name'])
                                group.add_host(host)
            else:
                ungrouped.add_host(host)
            group_all.add_host(host)

    def parse_vars(self, cache=False):
        if self.var_list:
            for k, v in self.var_list.items():
                self._inventory.set_variable('all', k, v)

    def parse_sources(self, cache=False):
        self.parse_groups()
        self.parse_hosts()
        self.parse_vars()

    def get_matched_hosts(self, pattern):
        return self.get_hosts(pattern)

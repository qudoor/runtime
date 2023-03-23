import json

from channels.generic.websocket import WebsocketConsumer
from django.http.request import QueryDict
from six import StringIO

from apps.common.constant.credential import PrivateKey
from apps.common.utils.aes import aesDecrypt
from apps.common.utils.webssh.ssh import SSH
from apps.runtime.models import CredentialModel


# 参考： https://github.com/huyuan1999/django-webssh.git
class WebSSH(WebsocketConsumer):
    message = {'status': 0, 'message': None}
    """
    status:
        0: ssh 连接正常, websocket 正常
        1: 发生未知错误, 关闭 ssh 和 websocket 连接

    message:
        status 为 1 时, message 为具体的错误信息
        status 为 0 时, message 为 ssh 返回的数据, 前端页面将获取 ssh 返回的数据并写入终端页面
    """

    def connect(self):
        """
        打开 websocket 连接, 通过前端传入的参数尝试连接 ssh 主机
        :return:
        """
        self.accept()
        query_string = self.scope.get('query_string')
        ssh_args = QueryDict(query_string=query_string, encoding='utf-8')

        width = ssh_args.get('width')
        height = ssh_args.get('height')
        port = ssh_args.get('port')

        width = int(width)
        height = int(height)
        port = int(port)

        # ssh_key_name = ssh_args.get('ssh_key')

        host = ssh_args.get('host')
        credential_id = ssh_args.get('credentialId')
        credential = self.get_credential(credential_id)
        print(credential)
        auth = credential['type']
        user = credential['username']
        ssh_key = credential['private_key']

        if credential['password']:
            passwd = credential['password']
        else:
            passwd = None

        self.ssh = SSH(websocker=self, message=self.message)

        ssh_connect_dict = {
            'host': host,
            'user': user,
            'port': port,
            'timeout': 30,
            'pty_width': width,
            'pty_height': height,
            'password': passwd
        }

        if auth == PrivateKey:
            # ssh_key_file = os.path.join(TMP_DIR, ssh_key_name)
            # with open(ssh_key_file, 'r') as f:
            #     ssh_key = f.read()

            string_io = StringIO()
            string_io.write(ssh_key)
            string_io.flush()
            string_io.seek(0)
            ssh_connect_dict['ssh_key'] = string_io

            # os.remove(ssh_key_file)
            # ssh_connect_dict['ssh_key'] = ssh_key

        self.ssh.connect(**ssh_connect_dict)

    def disconnect(self, close_code):
        try:
            self.ssh.close()
        except:
            pass

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        if type(data) == dict:
            status = data['status']
            if status == 0:
                data = data['data']
                self.ssh.shell(data)
            else:
                cols = data['cols']
                rows = data['rows']
                self.ssh.resize_pty(cols=cols, rows=rows)

    def get_credential(self, credential_id):
        credential = CredentialModel.objects.filter(id=credential_id).first()
        credential = credential.__dict__
        credential['password'] = aesDecrypt(credential['password'])
        print('credential :', credential)
        return credential

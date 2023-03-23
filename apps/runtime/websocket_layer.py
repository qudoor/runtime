import time
import traceback

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

from .custom_celery_tasks import task_run_playbook
from .utils import gen_rand_char


class Playbook(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = 'session_' + gen_rand_char()
        self.session = dict()
        self.message = dict()
        self.is_running = False

    # 创建连接时
    def connect(self):
        # 允许加入
        self.accept()
        # 加入组
        async_to_sync(self.channel_layer.group_add)(self.group, self.channel_name)

    # 断开连接时
    def disconnect(self, close_code):
        try:
            async_to_sync(self.channel_layer.group_discard)(self.group, self.channel_name)  # 退出组
        except Exception:
            print(traceback.format_exc())

    # 接受信息
    def receive(self, text_data=None, bytes_data=None):

        data = [
            {
                'name': 'runner01',
                'ip': '124.71.30.220',
                'port': 22,
                'user': 'root',
                'password': '1qa2ws#ED',
                # 'private_key': all_of_it,
                'groups': ['master', 'test'],
            }
        ]

        r = task_run_playbook.delay(
            hosts=data, group=self.group,
        )  # 执行
        print(r)

    # 发送消息
    def send_message(self, data):
        try:
            self.send(data['text'])
        except Exception:
            print(traceback.format_exc())

    # 关闭
    def close_channel(self, data):
        try:
            self.send(data['text'])
            time.sleep(0.3)
            self.close()
        except Exception:
            print(traceback.format_exc())

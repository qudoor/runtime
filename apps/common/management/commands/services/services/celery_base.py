from ..hands import *
from .base import BaseService


class CeleryBaseService(BaseService):

    def __init__(self, num=5, **kwargs):
        super().__init__(**kwargs)
        self.num = num

    @property
    def cmd(self):
        print('\n- Start Celery  ')

        os.environ.setdefault('PYTHONOPTIMIZE', '1')
        os.environ.setdefault('ANSIBLE_FORCE_COLOR', 'True')

        if os.getuid() == 0:
            os.environ.setdefault('C_FORCE_ROOT', '1')
        server_hostname = os.environ.get("SERVER_HOSTNAME")
        if not server_hostname:
            server_hostname = '%h'

        cmd = [
            'celery',
            '-A', 'QuPot',
            'worker',
            '-P', 'prefork',  # 使用 threads 导致在长时间运行时，celery 某些任务一直处于 STARTED 状态
            '-l', 'INFO',
            '-c', str(self.num),
            '-n', f'@{server_hostname}'
        ]
        return cmd

    @property
    def cwd(self):
        return BASE_DIR

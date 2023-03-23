from ..hands import *
from .base import BaseService

__all__ = ['GunicornService']


class GunicornService(BaseService):

    def __init__(self, **kwargs):
        self.worker = kwargs['worker_gunicorn']
        super().__init__(**kwargs)

    @property
    def cmd(self):
        print("\n- Start Gunicorn WSGI HTTP Server")

        log_format = '%(h)s %(L)ss "%(r)s" %(s)s %(b)s '
        bind = f'{HTTP_HOST}:{HTTP_PORT}'
        cmd = [
            'gunicorn', 'QuPot.wsgi',
            '-b', bind,
            '-k', 'gthread',
            '--threads', '10',
            '-w', str(self.worker),
            '--max-requests', '4096',
            '--access-logformat', log_format,
            '--access-logfile', '-'
        ]
        if DEBUG:
            cmd.append('--reload')
        return cmd

    @property
    def cwd(self):

        return BASE_DIR

    def start_other(self):
        pass
    #     from terminal.startup import CoreTerminal
    #     core_terminal = CoreTerminal()
    #     core_terminal.start_heartbeat_thread()

# ~*~ coding: utf-8 ~*~

import datetime
import json
import os
from collections import defaultdict

import ansible.constants as C
from ansible.plugins.callback.default import CallbackModule
from ansible.plugins.callback.minimal import CallbackModule as CMDCallBackModule


def safe_str(s):
    return s.encode('utf-8', errors='ignore').decode('utf-8')


def current_time():
    return '%sZ' % datetime.datetime.utcnow().isoformat()


class CallbackMixin:
    def __init__(self, display=None):
        # result_raw example: {
        #   "ok": {"hostname": {"task_name": {}，...},..},
        #   "failed": {"hostname": {"task_name": {}..}, ..},
        #   "unreachable: {"hostname": {"task_name": {}, ..}},
        #   "skipped": {"hostname": {"task_name": {}, ..}, ..},
        # }
        # results_summary example: {
        #   "contacted": {"hostname": {"task_name": {}}, "hostname": {}},
        #   "dark": {"hostname": {"task_name": {}, "task_name": {}},...,},
        #   "success": True
        # }
        self.results_raw = dict(
            ok=defaultdict(dict),
            failed=defaultdict(dict),
            unreachable=defaultdict(dict),
            skippe=defaultdict(dict),
        )
        self.results_summary = dict(
            contacted=defaultdict(dict),
            dark=defaultdict(dict),
            success=True
        )
        self.results = {
            'raw': self.results_raw,
            'summary': self.results_summary,
        }
        super().__init__()
        if display:
            self._display = display

        cols = os.environ.get("TERM_COLS", None)
        self._display.columns = 79
        if cols and cols.isdigit():
            self._display.columns = int(cols) - 1

    def display(self, msg):
        self._display.display(msg)

    def gather_result(self, t, result):
        # self._clean_results(result._result, result._task.action)
        host = result._host.get_name()
        task_name = result.task_name
        task_result = result._result

        self.results_raw[t][host][task_name] = task_result
        self.clean_result(t, host, task_name, task_result)

    def close(self):
        if hasattr(self._display, 'close'):
            self._display.close()


class AdHocResultCallback(CallbackMixin, CallbackModule, CMDCallBackModule):
    """
    Task result Callback
    """
    context = None

    def clean_result(self, t, host, task_name, task_result):
        contacted = self.results_summary["contacted"]
        dark = self.results_summary["dark"]

        if task_result.get('rc') is not None:
            cmd = task_result.get('cmd')
            if isinstance(cmd, list):
                cmd = " ".join(cmd)
            else:
                cmd = str(cmd)
            detail = {
                'cmd': cmd,
                'stderr': task_result.get('stderr'),
                'stdout': safe_str(str(task_result.get('stdout', ''))),
                'rc': task_result.get('rc'),
                'delta': task_result.get('delta'),
                'msg': task_result.get('msg', '')
            }
        else:
            detail = {
                "changed": task_result.get('changed', False),
                "msg": task_result.get('msg', '')
            }

        if t in ("ok", "skipped"):
            contacted[host][task_name] = detail
        else:
            dark[host][task_name] = detail

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.results_summary['success'] = False
        self.gather_result("failed", result)

        if result._task.action in C.MODULE_NO_JSON:
            CMDCallBackModule.v2_runner_on_failed(self,
                                                  result, ignore_errors=ignore_errors
                                                  )
        else:
            super().v2_runner_on_failed(
                result, ignore_errors=ignore_errors
            )

    def v2_runner_on_ok(self, result):
        self.gather_result("ok", result)
        if result._task.action in C.MODULE_NO_JSON:
            CMDCallBackModule.v2_runner_on_ok(self, result)
        else:
            super().v2_runner_on_ok(result)

    def v2_runner_on_skipped(self, result):
        self.gather_result("skipped", result)
        super().v2_runner_on_skipped(result)

    def v2_runner_on_unreachable(self, result):
        self.results_summary['success'] = False
        self.gather_result("unreachable", result)
        super().v2_runner_on_unreachable(result)

    def v2_runner_on_start(self, *args, **kwargs):
        pass

    def display_skipped_hosts(self):
        pass

    def display_ok_hosts(self):
        pass

    def display_failed_stderr(self):
        pass

    def set_play_context(self, context):
        # for k, v in context._attributes.items():
        #     print("{} ==> {}".format(k, v))
        if self.context and isinstance(self.context, dict):
            for k, v in self.context.items():
                setattr(context, k, v)


class CommandResultCallback(AdHocResultCallback):
    """
    Command result callback

    results_command: {
      "cmd": "",
      "stderr": "",
      "stdout": "",
      "rc": 0,
      "delta": 0:0:0.123
    }
    """

    def __init__(self, display=None, **kwargs):

        self.results_command = dict()
        super().__init__(display)

    def gather_result(self, t, res):
        super().gather_result(t, res)
        self.gather_cmd(t, res)

    def v2_playbook_on_play_start(self, play):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg = '$ {} ({})'.format(play.name, now)
        self._play = play
        self._display.banner(msg)

    def v2_runner_on_unreachable(self, result):
        self.results_summary['success'] = False
        self.gather_result("unreachable", result)
        msg = result._result.get("msg")
        if not msg:
            msg = json.dumps(result._result, indent=4)
        self._display.display("%s | FAILED! => \n%s" % (
            result._host.get_name(),
            msg,
        ), color=C.COLOR_ERROR)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.results_summary['success'] = False
        self.gather_result("failed", result)
        msg = result._result.get("msg", '')
        stderr = result._result.get("stderr")
        if stderr:
            msg += '\n' + stderr
        module_stdout = result._result.get("module_stdout")
        if module_stdout:
            msg += '\n' + module_stdout
        if not msg:
            msg = json.dumps(result._result, indent=4)
        self._display.display("%s | FAILED! => \n%s" % (
            result._host.get_name(),
            msg,
        ), color=C.COLOR_ERROR)

    def v2_playbook_on_stats(self, stats):
        pass


    def _print_task_banner(self, task):
        pass

    def gather_cmd(self, t, res):
        host = res._host.get_name()
        cmd = {}
        if t == "ok":
            cmd['cmd'] = res._result.get('cmd')
            cmd['stderr'] = res._result.get('stderr')
            cmd['stdout'] = safe_str(str(res._result.get('stdout', '')))
            cmd['rc'] = res._result.get('rc')
            cmd['delta'] = res._result.get('delta')
        else:
            cmd['err'] = "Error: {}".format(res)
        self.results_command[host] = cmd


class PlaybookResultCallBack(CallbackMixin, CallbackModule, CMDCallBackModule):
    """
    playbook result Callback
    """
    context = None

    def clean_result(self, t, host, task_name, task_result):
        contacted = self.results_summary["contacted"]
        dark = self.results_summary["dark"]

        if task_result.get('rc') is not None:
            cmd = task_result.get('cmd')
            if isinstance(cmd, list):
                cmd = " ".join(cmd)
            else:
                cmd = str(cmd)
            detail = {
                'cmd': cmd,
                'stderr': task_result.get('stderr'),
                'stdout': safe_str(str(task_result.get('stdout', ''))),
                'rc': task_result.get('rc'),
                'delta': task_result.get('delta'),
                'msg': task_result.get('msg', '')
            }
        else:
            detail = {
                "changed": task_result.get('changed', False),
                "msg": task_result.get('msg', '')
            }

        if t in ("ok", "skipped"):
            contacted[host][task_name] = detail
        else:
            dark[host][task_name] = detail

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.results_summary['success'] = False
        self.gather_result("failed", result)

        if result._task.action in C.MODULE_NO_JSON:
            CMDCallBackModule.v2_runner_on_failed(self,
                                                  result, ignore_errors=ignore_errors
                                                  )
        else:
            super().v2_runner_on_failed(
                result, ignore_errors=ignore_errors
            )

    def v2_runner_on_ok(self, result):
        self.gather_result("ok", result)
        if result._task.action in C.MODULE_NO_JSON:
            CMDCallBackModule.v2_runner_on_ok(self, result)
        else:
            super().v2_runner_on_ok(result)

    def v2_runner_on_skipped(self, result):
        self.gather_result("skipped", result)
        super().v2_runner_on_skipped(result)

    def v2_runner_on_unreachable(self, result):
        self.results_summary['success'] = False
        self.gather_result("unreachable", result)
        super().v2_runner_on_unreachable(result)

    def v2_runner_on_start(self, *args, **kwargs):
        pass

    def display_skipped_hosts(self):
        pass

    def display_ok_hosts(self):
        pass

    def display_failed_stderr(self):
        pass

    def set_play_context(self, context):
        # for k, v in context._attributes.items():
        #     print("{} ==> {}".format(k, v))
        if self.context and isinstance(self.context, dict):
            for k, v in self.context.items():
                setattr(context, k, v)

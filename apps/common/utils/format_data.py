from enum import Enum

from apps.common.constant.index import StatusSuccess, StatusFailed, ErrorTypeFailed, ErrorTypeUnreachable, Log, \
    Localhost, \
    ViewLog, StatusString, Query, GetQutrunkPodStatus, ConditionsString, StatusActive, StatusRetry, Create, Delete, \
    DeployQutrunkEnv, DeleteQutrunkEnv
from apps.common.utils.common import merge_two_dicts, is_has_key


class StatusCodeEnum(Enum):
    """状态码枚举类"""

    OK = (0, '成功')
    ANSIBLE_NOT_RUN = (5001, 'Ansible 未运行')
    ANSIBLE_NOT_DONE = (5002, 'Ansible 未运行完毕')
    ANSIBLE_RUN_ERROR = (5003, 'Ansible 运行失败')

    UNREACHABLE = (50004, '主机不可达')
    FAILED = (50005, '业务失败')

    @property
    def code(self):
        """获取状态码"""
        return self.value[0]

    @property
    def msg(self):
        """获取状态码信息"""
        return self.value[1]


# 尝试次数超过限制
def is_backoff_limit_exceeded(conditions):
    if conditions is not None and len(conditions) > 0 and conditions[0]['reason'] == 'BackoffLimitExceeded':
        return True
    return False


def get_pod_status(pod_data):
    status = pod_data.get(StatusString, None)
    if is_has_key(status, 'active') and status['active'] > 0:
        return StatusActive  # 正在初始化中
    elif is_has_key(status, 'succeeded') and status['succeeded'] > 0:
        return StatusSuccess
    else:
        conditions = status.get(ConditionsString, None)
        if is_backoff_limit_exceeded(conditions):
            return StatusFailed

    return StatusRetry


# 根据类型，自定义栏位，根据调用 api 的需求，格式化数据
# 读取业务逻辑下的数据，不同查询不同结构
def format_res_data(raw_data, task_type):
    data = dict()
    if task_type == Log:
        data[Log] = raw_data[Localhost].get(ViewLog, None)
        # 当 k8s 中创建失败，不会有 log
        if data[Log]:
            data[Log] = data[Log].get(Log, None)
        else:
            data[StatusString] = StatusFailed

    elif task_type == Query:
        resource_list = raw_data[Localhost][GetQutrunkPodStatus].get('resources', None)
        if resource_list is None or len(resource_list) == 0:
            data[StatusString] = StatusFailed
            data[Query] = "该环境不存在，已删除，或应用 id 错误"
        else:
            data[Query] = resource_list[0][StatusString]
            data[StatusString] = get_pod_status(resource_list[0])
    elif task_type == Create:
        data[Create] = raw_data[Localhost][DeployQutrunkEnv][StatusString]
        data[StatusString] = data[Create].get(StatusString, None)
    elif task_type == Delete:
        data[Delete] = raw_data[Localhost][DeleteQutrunkEnv]
    # else:
    # key, = raw_data[Localhost]  # 取数组第一个
    # data[Detail] = raw_data[Localhost][key]

    return data


def gen_response_data(success=False, msg=None, data=None):
    return {
        'success': success,
        'msg': msg,
        'data': data,  # 这个类型为 gen_response_detail 返回类型
    }


def gen_ko_response_data(item=None, total=0):
    return {
        'items': item,
        'total': total
    }


def gen_response_detail(detail=None, error_type=None, status=None):
    return {
        "status": status,
        "detail": detail,
        "error_type": error_type,
    }


def format_by_raw_and_summary(raw=None, summary=None, task_type=None):
    res = {
        "success": False,  # 业务上成功或失败
        "code": -1,
        "msg": None,  # 自定义错误信息
        "data": {
            "status": StatusFailed,
            "detail": None,
            # "error_type": None,
        },
    }

    dark = summary.get("dark", [])
    unreachable = raw.get(ErrorTypeUnreachable, {})
    failed = raw.get(ErrorTypeFailed, {})
    ok = raw.get('ok', None)

    # celery id 类型传错了无法判断
    if summary is None or summary == {}:
        # 查 log Ansible 未运行完毕
        res['code'] = StatusCodeEnum.ANSIBLE_NOT_RUN.code
        res['msg'] = StatusCodeEnum.ANSIBLE_NOT_RUN.msg
        return res

    if summary.get('success') is not True:
        res['code'] = StatusCodeEnum.ANSIBLE_NOT_DONE.code
        res['msg'] = StatusCodeEnum.ANSIBLE_NOT_DONE.msg
        res['data']['detail'] = summary
        return res

    if dark != [] and dark != {}:
        res['code'] = StatusCodeEnum.ANSIBLE_RUN_ERROR.code
        res['msg'] = StatusCodeEnum.ANSIBLE_RUN_ERROR.msg
        res['data']['detail'] = dark
    elif unreachable != {}:
        res['code'] = StatusCodeEnum.UNREACHABLE.code
        res['msg'] = StatusCodeEnum.UNREACHABLE.msg
        res['data']['detail'] = unreachable
    elif failed != {}:
        res['code'] = StatusCodeEnum.FAILED.code
        res['msg'] = StatusCodeEnum.FAILED.msg
        res['data']['detail'] = failed
    else:
        res['success'] = True
        res['code'] = StatusCodeEnum.OK.code
        res['msg'] = StatusCodeEnum.OK.msg
        res['data']['status'] = StatusSuccess
        res['data']['detail'] = ok
    temp_data = format_res_data(res['data']['detail'], task_type)
    res['data'] = merge_two_dicts(res['data'], temp_data)

    return res


def get_result_from_ansible_data(raw=None, summary=None, task_type=None):
    try:
        data = format_by_raw_and_summary(raw=raw, summary=summary, task_type=task_type)
        res = gen_response_data(success=True, data=data.get('data'), msg=data.get('msg'))
    except Exception as e:
        res = gen_response_data(msg="请检查该任务类型是否正确。错误详情： " + str(e))
        pass
    return res

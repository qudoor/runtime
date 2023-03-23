import json

from rest_framework import status
from rest_framework.response import Response


def result_success(res):
    return {'result': res, 'code': 0, 'message': 'ok', 'type': 'success'}


def get_response(resp, no_data=False):
    if resp.status_code == status.HTTP_200_OK:
        if no_data:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_200_OK, data=json.loads(resp.text))
    err = dict()
    err['msg'] = resp.reason
    try:
        resp_text = json.loads(resp.text)
        if resp_text.get('msg'):
            err['msg'] = resp_text.get('msg')  # check_ko_auth 中 账号密码错误会返回："msg": "NAME_PASSWORD_ERROR"
        return Response(status=status.HTTP_400_BAD_REQUEST, data=err)
    except Exception as e:
        return Response(status=status.HTTP_400_BAD_REQUEST, data=err)

import json

import requests
from django.conf import settings
from rest_framework import serializers
from rest_framework import status

from apps.common.utils.aes import aesDecrypt
from apps.common.utils.logger import get_logger
from apps.runtime.models import KoModel

session = requests.Session()

logger = get_logger(__name__)


class Ko:
    def __init__(self):
        try:
            # ko_url = 'http://qupot.queco.cn/'
            self.koObj = KoModel.objects.get(name='ko_url')
        except KoModel.DoesNotExist:
            self.koObj = None
            raise Exception('找不到 Ko 仓库，请配置 Ko 仓库')

    def refresh_session(self):
        global session
        data = {
            'username': self.koObj.username,
            'password': aesDecrypt(self.koObj.password)
        }
        session.post(self.koObj.url + 'api/v1/auth/session', json=data)

    def check_session_validity(self):
        global session
        response = session.get(self.koObj.url + 'api/v1/auth/session/status')
        responseText = json.loads(response.text)
        if response.status_code == 401 or not responseText.get('isLogin'):
            self.refresh_session()

    def get_clusters(self):
        global session
        self.check_session_validity()
        response = session.post(self.koObj.url + 'api/v1/clusters/search')
        logger.info(f'get_clusters response: {response}')
        return json.loads(response.text)

    def get_cluster_by_name(self, name):
        global session
        self.check_session_validity()
        response = session.get(self.koObj.url + 'api/v1/clusters/' + name)
        logger.info(f'get_clusters response: {response}')
        return json.loads(response.text)

    def download_all_cluster_config_by_session(self):
        global session
        self.check_session_validity()
        download_all_cluster_config(self.koObj.url, session.cookies)


def format_ko_url(ko_url):
    if not ko_url.endswith('/'):
        ko_url = ko_url + '/'
    return ko_url


def get_cluster_list_by_ko_url(ko_url, cookies):
    ko_url = format_ko_url(ko_url)
    r = requests.post(ko_url + 'api/v1/clusters/search', cookies=cookies)
    cluster_list = []
    if r.status_code == 200:
        cluster_list = json.loads(r.text)['items']
    return cluster_list


def download_file(ko_url, cluster_name):
    ko_url = format_ko_url(ko_url)
    r = requests.get(ko_url + 'api/v1/clusters/kubeconfig/' + cluster_name)
    with open(settings.K8S_CONFIG + '/' + cluster_name, "wb") as code:
        code.write(r.content)


def download_all_cluster_config(ko_url, cookies):
    ko_url = format_ko_url(ko_url)
    r = requests.post(ko_url + 'api/v1/clusters/search', cookies=cookies)
    if r.status_code == status.HTTP_200_OK:
        cluster_list = json.loads(r.text)['items']
        print('clusterList:', cluster_list)
        for cluster_item in cluster_list:
            download_file(ko_url, cluster_item['name'])


def get_ko_cookies(ko_url, username, password):
    data = {
        'username': username,
        'password': password
    }
    response = requests.post(ko_url + 'api/v1/auth/session', json=data)
    return response.cookies


def check_ko_auth(ko_dict):
    _ko_url = format_ko_url(ko_dict.get('url'))
    try:
        resp = requests.post(_ko_url + 'api/v1/auth/session', json=ko_dict)
        logger.info('check_conn resp: {}', resp)
        return resp
    except Exception as e:
        logger.error('check_conn exception: {}', e)
        raise serializers.ValidationError(e)

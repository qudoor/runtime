import json
import os

import requests
from django.conf import settings
from rest_framework import serializers

from apps.common.utils.logger import get_logger
from apps.common.utils.common import yaml_to_json

BaseUrl = "service/rest"
RepoUrl = BaseUrl + "/v1/repositories"

QuProductUrl = BaseUrl + "/v1/search?repository=" + settings.NEXUS_NAME

logger = get_logger(__file__)


def get_chart_list(chart_url):
    # 获取appstore 应用列表
    repo_list = chart_url + "/index.yaml"
    chart_yaml_url = requests.get(repo_list).content
    # yaml to json
    chart_yaml_file = os.path.join(settings.TMP_DIR, "index.yaml")
    with open(chart_yaml_file, 'wb') as f:
        f.write(chart_yaml_url)
    chart_json = yaml_to_json(chart_yaml_file)
    # 按创建时间排序，取应用第一个：

    chart_list = []
    for key, app in chart_json["entries"].items():
        app.sort(key=lambda x: x["created"])
        chart_list.append(app[-1])
    return chart_list


def check_conn(nexus_dict):
    endpoint = nexus_dict.get('protocol') + '://' + nexus_dict.get('hostname') + ':' + str(nexus_dict.get('repo_port'))
    url = endpoint + '/' + RepoUrl

    try:
        resp = requests.get(url, auth=(nexus_dict.get('nexus_user'), nexus_dict.get('nexus_password')))
        logger.info(f'check_conn resp: success')
        return resp
    except Exception as e:
        logger.error(f'check_conn exception: {e}')
        raise serializers.ValidationError(e)


def get_quproduct_list(nexus_dict):
    endpoint = nexus_dict.get('protocol') + '://' + nexus_dict.get('hostname') + ':' + str(nexus_dict.get('repo_port'))
    url = endpoint + '/' + QuProductUrl
    # url = 'http://x.x.x.202:8081/service/rest/v1/search?repository=qudoor-quproduct'
    logger.info('check nexus url: {}'.format(url))
    try:
        resp = requests.get(url, auth=(nexus_dict.get('nexus_user'), nexus_dict.get('nexus_password')))
        resp_data = json.loads(resp.text).get('items', [])
        # {
        #     "anaconda": [
        #         {
        #             "version": 123232,
        #             "arch": [
        #                 {
        #                     "name": "amd64",
        #                      "filename": ""
        #                 },
        #                 {
        #                     "name": "arm64",
        #                     "filename": ""
        #                 },
        #
        #             ]
        #         },
        #         {
        #             "version": 2222,
        #             "arch": [{"amd64"}]
        #         },
        #     ]
        # }
        dependents_dict = {}
        for i in resp_data:
            data = str(i.get("name", None))
            sp = data.split('/')
            name, version, arch, filename = sp[0], sp[1], sp[2], sp[3]
            if name in dependents_dict:
                found = False
                for j in dependents_dict[name]:
                    if version == j.get("version", None):
                        j["arch"].append({"name": arch, "filename": filename})
                        found = True
                        break
                if not found:
                    dependents_dict[name].append({"version": version, "arch": [{"name": arch, "filename": filename}]})
            else:
                dependents_dict[name] = [{"version": version, "arch": [{"name": arch, "filename": filename}]}]

        return dependents_dict
    except Exception as e:
        logger.error('get_quproduct_list exception: {}', e)
        raise serializers.ValidationError(e)

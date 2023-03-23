import json
import string
import random

import requests
from typing import Any, Dict, List
import math

class NexusHandler:
    def __init__(self, source_auth, target_auth, filter_list=None):
        self.s_auth = source_auth
        self.t_auth = target_auth
        self.filter_list = filter_list
        self.session = requests.Session()
        self.header = {'Content-Type': 'application/json'}
        self._check_connections()
        self.target_create_blob()


    def _check_connections(self) -> None:
        for auth in [self.s_auth, self.t_auth]:
            if not self._check_connection(auth):
                raise Exception(f'Unable to reach Nexus server at {auth["url"]}')

    def _check_connection(self, auth: Dict[str, str]) -> bool:
        try:
            response = requests.get(auth['url'], auth=(auth['user'], auth['passwd']))
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise Exception(str(e))
            return Falsee

    def make_request(self, method: str, url: str, auth: Dict[str, str], json: Any = None,
                     data: Any = None,**kwargs) -> requests.Response:
        try:
            response = self.session.request(method, url, auth=(auth['user'], auth['passwd']),
                                            json=json,
                                            data=data,**kwargs)
            if not response.ok:
                raise Exception(f'Request failed with status code {response.status_code}: {response.text}')
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(str(e), response.text)

    def get_source_all_repo_list(self, auth) -> List[Dict[str, str]]:
        all_repo_url = f'{auth["url"]}/service/rest/v1/repositories'
        res = self.make_request('GET', all_repo_url, auth, self.header)
        repo_list = res.json()
        return self.filter_repo_list(repo_list)

    def filter_repo_list(self, repo_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if self.filter_list:
            return [repo for repo in repo_list if repo["format"] in self.filter_list.get("format")]
        return repo_list

    def import_repo(self, repo: Dict[str, str]) -> None:
        import_url = f'{self.t_auth["url"]}/service/rest/v1/repositories'

        print(import_url, repo)
        res = self.make_request('POST', import_url, self.t_auth, self.header, json=repo)
        print(f'Successfully imported repository {repo["name"]}')
        res.raise_for_status()

    def target_create_blob(self):

        for blob_name in self.diff_blob_name_list():
            export_blob_url = f'{self.s_auth["url"]}/service/rest/v1/blobstores/file/{blob_name}'
            export_blob_res = self.make_request('GET', export_blob_url, self.s_auth, self.header)
            export_blob_res.raise_for_status()
            print(f'ready imported blob  {blob_name}')

            import_blob_url = f'{self.t_auth["url"]}/service/rest/v1/blobstores/file'
            import_blob_json = {
                "name": blob_name,
                "path": export_blob_res.json()['path']
            }
            import_blob_res = self.make_request("POST", import_blob_url, self.t_auth,
                                                json=import_blob_json)
            import_blob_res.raise_for_status()
            print(f'Success imported blobname  {blob_name}')

    def get_blob_name_list(self, auth):
        # 导出 blob list
        export_blob_url = f'{auth["url"]}/service/rest/v1/blobstores'
        blob_res = requests.get(export_blob_url, auth=(auth["user"], auth["passwd"]))
        blob_res = self.make_request("GET", export_blob_url, self.s_auth)
        blob_res.raise_for_status()
        blob_list = blob_res.json()
        return blob_list

    def diff_blob_name_list(self):
        source_blob_list = self.get_blob_list(self.s_auth)
        target_blob_list = self.get_blob_list(self.t_auth)

        source_blob_names = [blob["name"] for blob in source_blob_list]
        target_blob_names = [blob["name"] for blob in target_blob_list]

        diff_blob_names = list(set(source_blob_names) - set(target_blob_names))

        return diff_blob_names

    def get_blob_list(self, auth):
        # 导出 blob list
        export_blob_url = f'{auth["url"]}/service/rest/v1/blobstores'
        blob_res = self.make_request("GET", export_blob_url, auth)
        blob_res.raise_for_status()
        blob_list = blob_res.json()
        return blob_list

    def need_create_repo(self):
        source_all_repo_list = self.get_source_all_repo_list(self.s_auth)
        target_all_repo_list = self.get_source_all_repo_list(self.t_auth)
        source_repo_names = [repo["name"] for repo in source_all_repo_list]
        target_repo_names = [repo["name"] for repo in target_all_repo_list]
        diff_blob_names = list(set(source_repo_names) - set(target_repo_names))

        return [repo for repo in source_all_repo_list if repo["name"] in diff_blob_names]

    def target_create_repo(self):
        need_create_repo_list = self.need_create_repo()
        for repo in need_create_repo_list:
            export_repo_data_url = f'{self.s_auth["url"]}/service/rest/v1/repositories/{repo["format"]}/{repo["type"]}/{repo["name"]}'
            export_repo_data_res = self.make_request("GET", export_repo_data_url, self.s_auth)
            export_repo_data_res.raise_for_status()
            source_repo_data = export_repo_data_res.json()
            import_repo_data_url = f'{self.t_auth["url"]}/service/rest/v1/repositories/{repo["format"]}/{repo["type"]}'
            import_repo_data_res = self.make_request("POST", import_repo_data_url, self.t_auth, json=source_repo_data)
            import_repo_data_res.raise_for_status()
            print(f'success repo {repo["name"]} import data')

    def get_components_info(self, repository: str):
        """
        获取 Nexus 仓库中所有组件的信息
        """
        url = f"{self.s_auth['url']}/service/rest/v1/components?repository={repository}"
        response = self.make_request("GET", url, self.s_auth)
        response.raise_for_status()
        data = response.json()
        return data

    def transfer_raw_host_file(self, chunk_size: int = 1024 * 1024) -> None:
        # 获取源 Nexus 仓库中的所有组件信息
        components = self.get_components_info("qudoor-raw")

        # 遍历组件列表，找到文件对应的组件信息
        file_found = False
        for component in components['items']:
            # 找到对应的组件信息，获取组件的下载链接
            component_id = component.get("id")
            component_name = component.get("name")
            component_url = f"{self.s_auth['url']}/service/rest/v1/components/{component_id}"
            component_res = self.make_request("GET", component_url, self.s_auth)
            component_data = component_res.json()
            component_assets = component_data["assets"]

            for assets in component_assets:
                download_url = assets.get("downloadUrl")
                # 从源 Nexus 仓库下载文件到内存
                response = self.make_request("GET", download_url, self.s_auth)

                headers = {
                    "Content-Type": "multipart/form-data; boundary=<calculated when request is sent>"
                }

                with open("../tmp/celery.pid", "rb") as f:
                    file_content = f.read()


                target_url = f"{self.t_auth['url']}/service/rest/v1/components"
                data = {
                    "raw.directory": "/path/to/save/file/in/nexus",  # 上传到 Nexus 的路径
                    "raw.asset1": ("filename", file_content, "application/octet-stream"),
                    "raw.asset1.filename": "dkj"
                }
                res = self.make_request("POST", target_url, self.t_auth, headers=headers, data=data)
                res.raise_for_status()

        if not file_found:
            print(f"No such file in Nexus repository: {download_url}")


if __name__ == "__main__":
    source_auth = {
        "url": "http://x.x.x.x:8081",
        "user": "admin",
        "passwd": "123456"
    }
    target_auth = {
        "url": "http://x.x.x.x:8081",
        "user": "admin",
        "passwd": "123456"
    }
    filter_list = {
        "format": ["yum", "apt", "raw", "pypi"]
    }
    handler = NexusHandler(source_auth=source_auth, target_auth=target_auth, filter_list=filter_list)
    repos = handler.target_create_repo()

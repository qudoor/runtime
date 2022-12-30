# Runtime 配置文件文档
## 1. 概述

---
文档对组成 Runtime 的 `runtime.conf` `hosts.hostname.ini` `variables.yml` 服务的配置文件进行了详细的说明。配置文件在部署过程直接读取，做到配置即代码。

## 2. 配置文件说明

---
### 2.1 Runtime 管控机配置文件
配置文件名：`runtime/runtime/runtime.conf`

默认安装路径： `/opt/qupot/etc/runtime.conf`

配置参数说明：

| <div style="width:200px">配置项</div> | <div style="width:60px">值类型</div> | <div style="width:400px">默认值</div> | <div style="width:300px">说明</div> |
| ---- |-----------|---------|-------------------|
|RT_BASE  | string    | /opt | 默认安装管控机路径         |
|RT_TAG  | string       | ansible-2.10.6 | ansible 版本号       |
|RT_SECRET_PATH  | string    | /root/.ssh | 管控机 ssh 配置文件路径    |
|RT_ARCH  | string    | amd64 |  架构： arm64 amd64  |
|RT_PORT  | string    | 80 | 端口 |
|RT_REPO_PORT  | string    | 8081 | nexus l仓库端口 |
|DOCKER_COMPOSE_COMMAND  | string    | /usr/bin/docker-compose |  docker compose 路径  |
|CONTAINER_PLAYBOOK_PATH  | string    | /etc/runtime/playbook/ |   playbook 默认安装路径  |
<!-- |RT_REGISTRY_PORT  | string    | 8082 |     |
|RT_REGISTRY_HOSTED_PORT  | string    | 8083 |     |
|RT_REGISTRY_CHART_PORT  | string    | 8084 |     | -->

### 2.2 配置目标主机信息

配置文件名：`runtime/runtime/conf/hosts.hostname.ini`

- 2.2.1 在 `[all]` 下配置主机信息。可配置多个主机，以下为两个的主机的配置
    ```
    node1 ansible_ssh_host=192.168.1.1 ansible_port=22 ansible_user="root" ansible_ssh_pass="********" architectures="amd64" registry_hostname="192.168.100.54" repo_port="8081" registry_port="8082" registry_hosted_port="8083"
    node2 ansible_ssh_host=192.168.1.1 ansible_port=22 ansible_user="root" ansible_ssh_pass="********" architectures="amd64" registry_hostname="192.168.100.54" repo_port="8081" registry_port="8082" registry_hosted_port="8083"
    ```

    每条主机信息配置说明

    | <div style="width:200px">配置项</div> | <div style="width:60px">值类型</div> | <div style="width:400px">默认值</div> | <div style="width:300px">说明</div> |
    | ---- |-----------|------------------------------------|-----------------------------------|
    |node1 | string    | -                               |  自定义节点名称                    |
    |ansible_ssh_host  | string    | -                               | 主机 IP                             |
    |ansible_port  | string       | 22                               | 主机端口                              |
    |ansible_user  | string    | root                                | 主机用户名                             |
    |ansible_ssh_pass  | string    | -                               | 主机用户名对应密码                         |
    |architectures  | string    | -                                  | 架构：   arm64 amd64                 |
    |registry_hostname | string    |           -                     |  nexus 仓库地址          |

- 2.2.2 在 `[qupot-master]` 配置下添加 `2.2.1` 中声明的节点名称
    ```
    [qupot-master]
    node1
    node2
    ```

### 3. 变量配置文件

配置文件名 `runtime/runtime/conf/variables.yml`

| <div style="width:200px">配置项</div> | <div style="width:60px">值类型</div> | <div style="width:400px">默认值</div> | <div style="width:300px">说明</div> |
| ---- |-----------|------------------------------------|-----------------------------------|
|qupot_repository_hostname | string    | registry.quantum-door.com |  docker 仓库地址           |
|cluster_name_style | string    |  |  主机名称样式           |
|bin_dir | string    | /usr/local/bin |  Binaries Directory           |
|base_dir | string    | /opt/qupot |  存放目录           |
|dns_repository_hostname | string    | /opt/qupot |   驱动安装包下载仓库域名     |
|download_timeout_online | string    | 900(15min) |   驱动安装包下载仓库域名     |
|nvidia_name | string    | NVIDIA-Linux-x86_64 |   NVIDIA 包名称     |
|cuda_package | string    | NVIDIA-Linux-x86_64 |   cuda 包名称     |
|anaconda_package | string    | Anaconda3-{{ anaconda }}-Linux-x86_64.sh |   anaconda 包名称     |
|anaconda_dir | string    | /usr/local/anaconda |   anaconda安装路径     |
|anaconda_env | string    | cuquantum_env |   虚拟环境    |
|python_version | string    | 3.9.14 |   python 版本    |
|python_package | string    | 3.9.14 |   python 包名 |
|qusprout_version | string    | 0.1.12 |   qusprout 版本    |
|qusprout_package | string    | Qusprout-{{ qusprout_version }}.tar.gz |   qusprout 包名    |
|pcie_qrng_version | string    | 1.1.2 |   量子随机数发生卡（PCIE-QRNG） 版本    |
| pcie_qrng_name | string    | QRNG-PCIE-{{ pcie_qrng_version }}-Lylin |   量子随机数发生卡（PCIE-QRNG）名称   |
| pcie_qrng_package | string    | {{ pcie_qrng_name }}.zip |   量子随机数发生卡（PCIE-QRNG）包名  |
| quqcs_package | string    | quqcs-{{ quqcs_version }}-py3-none-any.whl |  quqcs 包名  |
| quqcs_version | string    | 0.1.0 |  quqcs 版本号  |
| nvidia_download_url | string    | - |   nvidia 驱动 下载地址  |
| cuda_repo_key_download_url | string    |  - |  cuda apt key  下载地址  |
| cuda_download_url | string    |  - |  cuda  下载地址  |
| cuda_repo_url | string    | -  |  cuda 仓库地址  |
| anaconda_download_url | string    | -  |  Anaconda3 下载地址  |
| python_download_url | string    | -  |  python3 下载地址  |
| qusprout_download_url | string    | -  |  Qusprout 下载地址  |
| pcie_qrng_download_url | string    | -  |  PCIE-QRNG 下载地址   |
| quqcs_download_url | string    | - |  quqcs 下载地址  |

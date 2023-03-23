# installer
QuPot 1.0 Installer


## kubernetes 部署
### [ko 部署](https://kubeoperator.io/index.html) 
> 第一步：准备一台主机
> 
> 准备一台不小于 8 G内存且可以访问互联网的 64位 Linux 主机。

> 第二步：安装
> 
> 在线包已不维护，可以参考离线包安装。

### 存储持久化部署
#### NFS 动态存储部署
##### nfs 服务端安装

1. 安装 NFS 软件包
```shell
```shell
# 安装 nfs-client
yum install nfs-utils

# 安装 nfs-server
yum install nfs-utils nfs-utils-lib

```

在 Ubuntu 中，可以使用 apt-get 命令来安装软件包。因此，将上述命令转换为 Ubuntu 命令，如下所示：
```shell
# 安装 nfs-client
sudo apt-get install nfs-common

# 安装 nfs-server
sudo apt-get install nfs-kernel-server
```

2. 创建共享目录

在 NFS 服务器上创建一个共享目录，例如 "/mnt/nfs_share"。创建和更改权限：
```shell
mkdir -p /mnt/nfs_share
chmod nobody:nogroup /mnt/nfs_share
chmod -R 777 /mnt/nfs_share
```

3. 配置 NFS 共享目录

在 NFS 服务器上，编辑 "/etc/exports" 文件，添加以下内容：
```shell
/mnt/nfs_share *(rw,sync,no_subtree_check)
```
将 "/mnt/nfs_share" 目录共享给所有客户端，使用 "rw" 来指定读写权限，使用 "sync" 来指定同步写入，使用 "no_subtree_check" 来禁用子树检查。

4. 重启 NFS 服务
```shell
systemctl restart nfs-server
```


##### nfs helm 仓库增加
1. 添加 namespace
```shell
kubectl create namespace nfs
```

2. 安装 nfs-subdir-external-provisioner
```shell
helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/
helm repo update
helm install nfs-subdir-external-provisioner nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
  --namespace nfs \
  --set nfs.server=172.31.21.0 \
  --set nfs.path=/mnt/nfs_share \
  --set storageClass.defaultClass=true \
  --set storageClass.allowVolumeExpansion=true
```
将 nfs.server 和 nfs.path 替换为 NFS 服务器的 IP 地址和共享目录。 

3. 检查 nfs-subdir-external-provisioner 是否安装成功
```shell
kubectl get pods -n nfs # Running 则表示安装成功
kubectl describe pods -n nfs
```

- 创建 nfs-storageclass.yaml
```shell
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: nfs-client
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: nfs-subdir-external-provisioner
parameters:
  archiveOnDelete: "false"
mountOptions:
  - nfsvers=4.1
  - hard
  - timeo=600
  - retrans=2
  - noresvport
reclaimPolicy: Retain
allowVolumeExpansion: true
```

kubectl apply -f nfs-storageclass.yaml
  
### apisix 部署

- apisix 安装，要先删除 kubernetes 默认的使用的 ingress controller: 可从 kubepi 中删除 

#### helm 安装apisix
- apisix 安装

安装apisix,并且设置gateway的类型为NodePort,并且设置gateway的端口为30080
```shell
# 获取所有 namespace
kubectl get ns
# 创建 apisix namespace
kubectl create ns apisix

helm repo add apisix https://charts.apiseven.com
helm repo update

helm install apisix apisix/apisix --set gateway.type=NodePort --set gateway.http.nodePort=30080 --namespace apisix --set etcd.image.tag=3.5.7-debian-11-r15
```

端口通过80转发出去

```shell
nohup kubectl port-forward --address 0.0.0.0 service/apisix-gateway 80:80 -n apisix &
```

- apisix-dashboard 安装
```shell    
helm install apisix-dashboard apisix/apisix-dashboard --set apisix.baseURL=http://apisix-gateway.apisix.svc.cluster.local:9080/apisix/admin --namespace apisix
```

端口通过9000转发出去
```shell
nohup kubectl port-forward --address 0.0.0.0 service/apisix-dashboard 9000:80 -n apisix &
```

- apisix-ingress-controller 安装
```shell
helm install apisix-ingress-controller apisix/apisix-ingress-controller --set config.apisix.serviceFullname=apisix-admin.apisix.svc.cluster.local \
  --set service.type=NodePort \
  --set service.nodePorts.http=80 \
  --namespace apisix 
```

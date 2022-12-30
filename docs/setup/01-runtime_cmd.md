# Runtime 命令说明

---

## 查询 `runtime` 运行状态

 ```shell
 $ rtctl status
 ```

`State` 表示运行状态
```
    Name                   Command                  State                                                   Ports                                             
--------------------------------------------------------------------------------------------------------------------------------------------------------------
runtime         sleep 360000000                  Up                                                                                                           
runtime-nexus   sh -c ${SONATYPE_DIR}/star ...   Up (healthy)   0.0.0.0:8081->8081/tcp, 0.0.0.0:8082->8082/tcp, 0.0.0.0:8083->8083/tcp, 0.0.0.0:8084->8084/tcp


Process finished with exit code 0
```

## 启动 `runtime`

 ```shell
 $ rtctl start
 ```


## 停止 `runtime`

 ```shell
 $ rtctl stop
 ```


## 重启 `runtime`

 ```shell
 $ rtctl restart
 ```

## 卸载 `runtime`

 ```shell
 $ rtctl uninstall
 ```

 ## 列出可安装应用环境名称
 ```shell
$ rtctl list
 ```

 运行结果
 ```
 runtime list: 
    04-algorithms-lib
    02-qutrunk
    01-nvidia-gpu
    03-qusprout
    05-pcie-qrng
    00hello

Process finished with exit code 0
 ```
## 应用环境安装
> 应用环境安装前需要先**配置安装目标主机信息**，具体见文档 [02-Runtime配置说明](./02-runtime_config.md) 

 ```shell
 $ rtctl run --playbook 应用环境名称
 ```
 `--playbook ` 后名称表示应用环境对应名称，可通过命令 `$ rtctl list` 列出存在可安装的应用环境


如测试连通性
 ```shell
 $ rtctl run --playbook 00hello
 ```

具体应用环境说明安装见文档 [03-应用环境安装说明](./03-install_env.md)

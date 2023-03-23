# QuPot UI
前端 UI 项目, 主要使用 [Vue](https://cn.vuejs.org/), [Element UI](https://github.com/fit2cloud-ui/fit2cloud-ui/) 完成。

## 开发运行

```
0. 前置条件: 部署运行好 API 服务器

1. 安装依赖
$ npm install

2. 运行
$ npm run serve

3. 构建
$ npm run build
```

### 多cpu 架构打包
```shell
# ui 目录下
docker buildx build --platform linux/amd64,linux/arm64 -t harbor.quantum-door.com/qudoor/ui:0.1 --push .
```

### 本地拉取
```shell
docker pull harbor.quantum-door.com/qudoor/ui:0.1
```

### 本地打开测试
```shell
docker run -d --restart=unless-stopped -p 80:80 harbor.quantum-door.com/qudoor/ui:0.1
```

## 致谢
- [Vue](https://cn.vuejs.org) 前端框架
- [FIT2CLOUD UI](https://github.com/fit2cloud-ui/fit2cloud-ui/) FIT2CLOUD UI组件库
- [Vue-element-admin](https://github.com/PanJiaChen/vue-element-admin) 项目脚手架


## Copyright
Copyright (c)


docker 打包：
amd版本：

docker build -t registry.quantum-door.com:8084/repository/qudoor/ui:v1.0.0-amd64 .

推送：
docker push registry.quantum-door.com:8084/repository/qudoor/ui:v1.0.0-amd64

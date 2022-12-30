#!/usr/bin/env bash
#Install Runtime Tool

set -e

red=31
green=32
yellow=33
blue=34


# 检测系统架构，目前支持 arm64 和 amd64
os=`uname -a`
if [[ $os =~ 'aarch64' ]];then
  architecture="arm64"
elif [[ $os =~ 'x86_64' ]];then
  architecture="amd64"
else
  colorMsg $red "暂不支持的系统架构，选择受支持的系统"
fi

docker_compose_version="1.29.0"
docker_version="19.03.15"

CONF_PATH="/etc/runtime"

if [ ! -d $CONF_PATH ];then
  mkdir $CONF_PATH
fi  

echo
cat << EOF

██████╗ ██╗   ██╗███╗   ██╗████████╗██╗███╗   ███╗███████╗
██╔══██╗██║   ██║████╗  ██║╚══██╔══╝██║████╗ ████║██╔════╝
██████╔╝██║   ██║██╔██╗ ██║   ██║   ██║██╔████╔██║█████╗
██╔══██╗██║   ██║██║╚██╗██║   ██║   ██║██║╚██╔╝██║██╔══╝
██║  ██║╚██████╔╝██║ ╚████║   ██║   ██║██║ ╚═╝ ██║███████╗
╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝     ╚═╝╚══════╝
EOF

function colorMsg()
{
  echo -e "\033[$1m $2 \033[0m"
}

function log() {
   message="[runtime Log]: $1 "
   echo -e "${message}" 2>&1 | tee -a ${CURRENT_DIR}/install.log
}

#设置当前路径
if [ ! $CURRENT_DIR ];then
  CURRENT_DIR=$(cd "$(dirname "$0")";pwd)
fi

# 配置 runtime路径
function set_dir() {
  if read -t 120 -p "设置runtime安装目录,默认/opt: " RT_BASE;then
  if [ "$RT_BASE" != "" ];then
    echo "你选择的安装路径为 $RT_BASE"
    if [ ! -d $RT_BASE ];then
      mkdir -p $RT_BASE
    fi
  else
    RT_BASE=/opt
    echo "你选择的安装路径为 $RT_BASE"
  fi
  else
    RT_BASE=/opt
    echo "(设置超时，使用默认安装路径 /opt)"
  fi
}

# 解压离线文件
function unarchive() {
      # 离线安装
      log "... 解压离线包中,大概需要3分钟，请勿取消"
      \cp -rfp ${CURRENT_DIR}/runtime $RT_BASE
      tar zxf ${CURRENT_DIR}/nexus-data.tar.gz -C $RT_BASE/runtime/data/ > /dev/null 2>&1
}

function rt_config() {
  # 修改环境变量配置文件
  if [ ! -f $CONF_PATH/runtime/runtime.conf ];then
    ln -s  $RT_BASE/runtime/runtime.conf $CONF_PATH/runtime.conf
  fi
  sed -i -e "s#RT_BASE=.*#RT_BASE=$RT_BASE#g" $RT_BASE/runtime/runtime.conf
  if [ ! -f $RT_BASE/runtime/.env ];then
    ln -s $RT_BASE/runtime/runtime.conf $RT_BASE/runtime/.env
  fi
}

# 配置docker，私有 docker 仓库授信
function config_docker() {
  log "关闭selinux"
  if [ $(getenforce) == "Enforcing" ];then
    log  "... 关闭 SELINUX"
    setenforce 0
    sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config
  fi
  log  "... 关闭 Firewalld"
  systemctl stop firewalld | tee -a ${CURRENT_DIR}/install.log
  systemctl disable firewalld | tee -a ${CURRENT_DIR}/install.log
  if ! grep registry.quantum-door.com /etc/hosts;then
    log  "... 添加 docker 仓库"
    echo "127.0.0.1 registry.quantum-door.com" >> /etc/hosts
  fi
  if [ -r /etc/docker/daemon.json ];then
    mv -n /etc/docker/daemon.json /etc/docker/daemon.json.bak
  else
    mkdir -p /etc/docker
  fi
cat << EOF > /etc/docker/daemon.json
{
  "registry-mirrors": ["http://registry.quantum-door.com:8082","http://registry.quantum-door.com:8083","http://registry.quantum-door.com:8084"],
  "insecure-registries": ["registry.quantum-door.com:8082","registry.quantum-door.com:8083","registry.quantum-door.com:8084"],
  "max-concurrent-downloads": 10,
  "log-driver": "json-file",
  "log-level": "warn",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
  }
EOF
  systemctl daemon-reload | tee -a ${CURRENT_DIR}/install.log
  systemctl restart docker | tee -a ${CURRENT_DIR}/install.log
}

# 检测 docker 是否存在
function install_docker() {
  if which docker >/dev/null; then
    log "检测到 Docker 已安装，跳过安装步骤"
    log "启动 Docker "
    systemctl start docker 2>&1 | tee -a ${CURRENT_DIR}/install.log
  else
    if [[ -d docker ]]; then
      log "... 离线安装 docker"
      \cp docker/bin/* /usr/bin/
      \cp docker/service/docker.service /etc/systemd/system/
      chmod +x /usr/bin/docker*
      chmod +x /usr/bin/runc
      chmod +x /usr/bin/ctr
      chmod +x /usr/bin/containerd*
      chmod 754 /etc/systemd/system/docker.service
      log "... 配置 docker"
      config_docker
      log "... 启动 docker"
      systemctl start docker 2>&1 | tee -a ${CURRENT_DIR}/install.log
      systemctl enable docker 2>&1 | tee -a ${CURRENT_DIR}/install.log
    else
      log "... 在线安装 docker"
      curl -fsSL https://get.docker.com -o get-docker.sh 2>&1 | tee -a ${CURRENT_DIR}/install.log
      sudo sh get-docker.sh --mirror Aliyun 2>&1 | tee -a ${CURRENT_DIR}/install.log
      log "... 配置 docker"
      config_docker
      log "... 启动 docker"
      systemctl start docker 2>&1 | tee -a ${CURRENT_DIR}/install.log
    fi
  fi
  # 检查docker服务是否正常运行
  docker ps 1>/dev/null 2>/dev/null
  if [ $? != 0 ];then
    log "Docker 未正常启动，请先安装并启动 Docker 服务后再次执行本脚本"
    exit
  fi

  ##Install Latest Stable Docker Compose Release
  if which docker-compose >/dev/null; then
    log "检测到 Docker Compose 已安装，跳过安装步骤"
  else
    if [[ -d docker ]]; then
      log "... 离线安装 docker-compose"
      \cp docker/bin/docker-compose /usr/bin/
      ln -s /usr/bin/docker-compose /usr/local/bin/docker-compose
      sudo chmod +x /usr/bin/docker-compose
    else
      log "... 在线安装 docker-compose"
      wget --no-check-certificate $docker_compose_download_url -P /usr/local/bin/ 2>&1 | tee -a ${CURRENT_DIR}/install.log
      chmod +x /usr/local/bin/docker-compose
      ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
    fi
  fi
  # 检查docker-compose是否正常
  docker-compose version 1>/dev/null 2>/dev/null
  if [ $? != 0 ];then
    log "docker-compose 未正常安装，请先安装 docker-compose 后再次执行本脚本"
    exit
  fi
}

# 加载镜像
function load_image() {
  export COMPOSE_HTTP_TIMEOUT=180
  if [[ -d ${CURRENT_DIR}/images ]]; then
     log "... 加载镜像"
     cd  $CURRENT_DIR
     for i in $(ls images); do
        docker load -i images/$i 2>&1 | tee -a ${CURRENT_DIR}/install.log
     done
  else
     log "... 拉取镜像"
     cd $RT_BASE/runtime/ && docker-compose pull 2>&1 | tee -a ${CURRENT_DIR}/install.log
     cd -
  fi
}

#启动runtime
function rt_start() {
  ln -s $RT_BASE/runtime/rtctl /usr/bin/rtctl
  cd  $RT_BASE/runtime/ && docker-compose up -d 2>&1 | tee -a ${CURRENT_DIR}/install.log
  sleep 15s
  while [ $(docker ps -a|grep runtime|wc -l) -lt 2 ]
  do
    log "... 检测到应用程序未正常运行，尝试重新启动"
    sleep 15s
    rtctl start
    break
  done
  echo -e "======================= Runtime 安装完成 =======================\n" 2>&1 | tee -a ${CURRENT_DIR}/install.log
}

function main() {
  set_dir
  unarchive
  install_docker
  rt_config
  load_image
  rt_start
}

main

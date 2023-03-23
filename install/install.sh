#!/usr/bin/env bash
#Install Latest Stable QuPot Release

red=31
green=32
yellow=33
blue=34

set -e
# 检测系统架构，目前支持 arm64 和 amd64
os=$(uname -a)
if [[ $os =~ 'aarch64' ]]; then
  architecture="arm64"
elif [[ $os =~ 'x86_64' ]]; then
  architecture="amd64"
else
  colorMsg $red "暂不支持的系统架构，请参阅官方文档，选择受支持的系统"
fi
docker_compose_version="1.29.0"
docker_version="19.03.15"

function colorMsg() {
  echo -e "\033[$1m $2 \033[0m"
}

function log() {
  message="[QuPot Log]: $1 "
  echo -e "${message}" 2>&1 | tee -a ${CURRENT_DIR}/install.log
}

if [ ! $QU_VERSION ]; then
  QU_VERSION=$(cat qupot/qupot.conf | grep "QU_TAG" | awk -F= '{print $2}')
fi

echo
cat <<EOF

 ██████╗ ██╗   ██╗██████╗  ██████╗ ████████╗
██╔═══██╗██║   ██║██╔══██╗██╔═══██╗╚══██╔══╝
██║   ██║██║   ██║██████╔╝██║   ██║   ██║   
██║▄▄ ██║██║   ██║██╔═══╝ ██║   ██║   ██║   
╚██████╔╝╚██████╔╝██║     ╚██████╔╝   ██║   
 ╚══▀▀═╝  ╚═════╝ ╚═╝      ╚═════╝    ╚═╝   
                                            
EOF

if [ ! $CURRENT_DIR ]; then
  CURRENT_DIR=$(
    cd "$(dirname "$0")"
    pwd
  )
fi

# 配置 qupot
function set_dir() {
  if read -t 120 -p "设置QuPot安装目录,默认/opt: " QU_BASE; then
    if [ "$QU_BASE" != "" ]; then
      # 配置 qupot
      if [ ! -d $QU_BASE ]; then
        mkdir -p $QU_BASE
      fi
    else
      QU_BASE=/opt
      echo "你选择的安装路径为 $QU_BASE"
    fi
  else
    QU_BASE=/opt
    echo "(设置超时，使用默认安装路径 /opt)"
  fi
}

# 解压离线文件
function unarchive() {
  if [ -d ${CURRENT_DIR}/docker ]; then
    # 离线安装
    log "... 解压离线包"
    \cp -rfp ${CURRENT_DIR}/qupot $QU_BASE
    \cp -rfp ${CURRENT_DIR}/quctl $QU_BASE/qupot
    tar zxf ${CURRENT_DIR}/nexus-data.tar.gz -C $QU_BASE/qupot/data/ >/dev/null 2>&1
    log "... 解压 mysql 初始化文件"
    tar zxf ${CURRENT_DIR}/mysql.tar.gz -C $QU_BASE/qupot/data/ >/dev/null 2>&1
  else
    # 在线安装
    log "... 解压 ansible "

  fi
}

function qu_config() {
  # 修改环境变量配置文件
  sed -i -e "s#QU_BASE=.*#QU_BASE=$QU_BASE#g" $QU_BASE/qupot/qupot.conf
  if [ ! -f $QU_BASE/qupot/.env ]; then
    ln -s $QU_BASE/qupot/qupot.conf $QU_BASE/qupot/.env
  fi
  # 修改 quctl 可执行文件并拷贝到环境变量
  sed -i -e "1,9s#QU_BASE=.*#QU_BASE=${QU_BASE}#g" $QU_BASE/qupot/quctl
  \cp -rfp $QU_BASE/qupot/quctl /usr/local/bin/
  # 修改 const 文件
  sed -i -e "1,9s#QU_BASE=.*#QU_BASE=${QU_BASE}#g" $QU_BASE/qupot/scripts/const.sh
}

# 配置docker，私有 docker 仓库授信
function config_docker() {
  if [ $(getenforce) == "Enforcing" ]; then
    log "... 关闭 SELINUX"
    setenforce 0
    sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config
  fi
  log "... 关闭 Firewalld"
  systemctl stop firewalld | tee -a ${CURRENT_DIR}/install.log
  systemctl disable firewalld | tee -a ${CURRENT_DIR}/install.log
  if ! grep registry.qupot.io /etc/hosts; then
    log "... 添加 qupot docker 仓库"
    echo "127.0.0.1 harbor.quantum-door.com" >>/etc/hosts
  fi
  if [ -r /etc/docker/daemon.json ]; then
    mv -n /etc/docker/daemon.json /etc/docker/daemon.json.bak
  else
    mkdir -p /etc/docker
  fi
  cat <<EOF >/etc/docker/daemon.json
{
  "registry-mirrors": ["http://registry.quantum-door.com:8082","http://registry.quantum-door.com:8083","http://registry.quantum-door.com:8084","http://registry.quantum-door.com","http://registry.queco.cn"],
  "insecure-registries": ["registry.quantum-door.com:8082","registry.quantum-door.com:8083","registry.quantum-door.com:8084","registry.quantum-door.com","registry.queco.cn"],
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
  if which docker docker-compose; then
    log "... docker 已经安装，跳过安装步骤"
    config_docker
    if systemctl status docker | grep running; then
      log "... docker 运行正常"
    else
      log "... docker 已经安装，跳过安装步骤"
    fi
  else
    if [[ -d docker ]]; then
      log "... 离线安装 docker"
      cp docker/bin/* /usr/bin/
      cp docker/service/docker.service /etc/systemd/system/
      sudo chmod +x /usr/bin/docker*
      sudo chmod 754 /etc/systemd/system/docker.service
      log "... 配置 docker"
      config_docker
      log "... 启动 docker"
      systemctl start docker 2>&1 | tee -a ${CURRENT_DIR}/install.log
      systemctl enable docker 2>&1 | tee -a ${CURRENT_DIR}/install.log
    else
      log "... 在线安装 docker,暂不支持"
    fi
  fi
}

##here

# 加载镜像
function load_image() {
  export COMPOSE_HTTP_TIMEOUT=180
  if [[ -d ${CURRENT_DIR}/images ]]; then
    log "... 加载镜像"
    cd $CURRENT_DIR
    for i in $(ls images); do
      docker load -i images/$i 2>&1 | tee -a ${CURRENT_DIR}/install.log
    done
  else
    log "... 拉取镜像"
    cd $QU_BASE/qupot/ && docker-compose pull 2>&1 | tee -a ${CURRENT_DIR}/install.log
    cd -
  fi
}

# 启动 qupot
function qu_start() {
  # 设置 app.yaml 配置文件权限
  log "... 开始启动 QuPot"
  cd $QU_BASE/qupot/ && docker-compose up -d 2>&1 | tee -a ${CURRENT_DIR}/install.log
  sleep 15s
  while [ $(docker ps -a | grep qupot | wc -l) -lt 5 ]; do
    log "... 检测到应用程序未正常运行，尝试重新启动"
    sleep 15s
    quctl start
    break
  done
  if [ $(docker ps -a | grep qupot | wc -l) -gt 0 ] && [ $(docker ps -a | grep qupot | egrep "Exit|unhealthy" | wc -l) -eq 0 ]; then
    echo -e "======================= QuPot 安装完成 =======================\n" 2>&1 | tee -a ${CURRENT_DIR}/install.log
    echo -e "请开放防火墙或安全组的80,8081-8083端口,通过以下方式访问:\n URL: \033[33m http://\$LOCAL_IP:80\033[0m \n 用户名: \033[${green}m admin \033[0m \n 初始密码: \033[${green}m qupot@admin123 \033[0m" 2>&1 | tee -a ${CURRENT_DIR}/install.log
  else
    colorMsg $red "QuPot 服务异常，请检查服务是否启动" | tee -a ${CURRENT_DIR}/install.log
    cd $QU_BASE/qupot/ && docker-compose ps
  fi
}

function main() {
  set_dir
  unarchive
  install_docker
  qu_config
  load_image
  qu_start
}

main

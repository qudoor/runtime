#!/usr/bin/env bash

source "${QU_BASE}/qupot/scripts/const.sh"

function success(){
    echo -e "\033[32m QuPot 卸载完成. \033[0m"
}

function remove_dir() {
    echo -e "删除 QuPot 工作目录"
    rm -rf ${QU_BASE}/qupot 2&> /dev/null
}

function remove_service() {
    if [ -a ${QU_BASE}/qupot/docker-compose.yml ]; then
      read -p "卸载将会完全清除 QuPot 的所有容器和数据，是否继续 [y/n] : " yn
      if [ "$yn" == "Y" ] || [ "$yn" == "y" ]; then
      echo -e "停止 QuPot 服务进程"
      cd ${QU_BASE}/qupot && docker-compose down -v
      rm -rf /usr/local/bin/quctl
      else
      exit 0
      fi
    fi
}



function remove_images() {
    echo -e "清理镜像中..."
    docker images -q|xargs docker rmi -f 2&> /dev/null
}


function main() {
    remove_service
    remove_images
    remove_dir
    success
}

if [[ "$0" == "${BASH_SOURCE[0]}" ]]; then
  main
fi